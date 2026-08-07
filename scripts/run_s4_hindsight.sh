#!/usr/bin/env bash
# S4 hindsight-ceiling pass — spec docs/specs/S4_SPEC.md, authorised by D1.2.
#
# Both capable judges, full matrix, hybrid overflow policy. Each judge gets its own
# GPU and runs concurrently: the approved 17.1 A100-hours is ~3.4h wall clock only if
# the two judges do not queue behind each other.
#
# Serving conventions follow scripts/run_crossprobe_matrix.sh (that file is the
# reference for HF cache paths, the Qwen max-num-seqs clamp, and the vllm path).
set -euo pipefail
ROOT=/data5/kje/MULTIAGENT/DACS-AUQ
cd "$ROOT"

V=${XP_VLLM:-/opt/anaconda3/envs/yllm/bin/vllm}
PY=${XP_PY:-/opt/anaconda3/envs/yllm/bin/python}
# Weight root and the explicit snapshot map are taken from
# scripts/run_crossprobe_matrix.sh; the HF-cache-style path guessed here first does
# not exist on this box, and Llama-70B is ~132GB so it needs TP=2, not TP=1.
HUB=${HUB:-/data3/hg_weight/hg_weight}
snap_for() {
  case "$1" in
    Llama-3.3-70B-Instruct) echo "$HUB/models--meta-llama--Llama-3.3-70B-Instruct/snapshots/6f6073b423013f6a7d4d9f39144961bfbfbc386b" ;;
    Qwen3.6-35B-A3B)        echo "/data5/user/hf_cache/hub/models--Qwen--Qwen3.6-35B-A3B/snapshots/995ad96eacd98c81ed38be0c5b274b04031597b0" ;;
  esac
}
tp_for() { case "$1" in Llama-3.3-70B-Instruct) echo 2 ;; *) echo 1 ;; esac; }
MODE=${MODE:-main}          # main | long
# GPU topology matters here: 0 and 1 are interconnected, 1 and 2 are NOT. Llama-70B
# runs TP=2 and every all-reduce crosses that link, so placing it on 1,2 forced the
# traffic over PCIe and cost 6.5x throughput (0.154 steps/s vs Qwen's 1.01 on one
# card). Llama must sit on a connected pair; Qwen is TP=1 and can go anywhere.
LLAMA_GPUS=${LLAMA_GPUS:-0,1}
QWEN_GPU=${QWEN_GPU:-2}
JUDGES=${JUDGES:-both}      # both | llama | qwen
# In-flight requests per judge. A serial client leaves vLLM at
# "Running: 1 reqs" with KV cache ~10%, so --max-num-seqs never engages.
CONC=${CONC:-24}
# Prefill token budget per scheduler step. The default fits barely two ~7k-token
# hindsight prompts, so 24 concurrent client requests sat at "Running: 2, Waiting: 21"
# -- the client was no longer the bottleneck, the scheduler was. KV cache was at 10%,
# so the headroom was there; this spends it on prefill batching.
BATCH_TOK=${BATCH_TOK:-65536}
# vLLM 0.23 defaults max_num_partial_prefills=1 and max_long_partial_prefills=1, so
# exactly ONE long prompt prefills per scheduler step no matter what --max-num-seqs or
# --max-num-batched-tokens say. That is why the engine sat at "Running: 2, Waiting: 21"
# with KV cache at 10%, why raising BATCH_TOK to 65536 changed nothing, and why moving
# the client from serial to 24 threads bought 0.20 -> 0.21 steps/s: the server was the
# serializer, not the client.
# NOT USABLE on this stack: vLLM 0.23 runs the V1 engine, which raises
#   NotImplementedError: Concurrent Partial Prefill is not supported
# at startup if either flag is passed. The Running:1-2 ceiling on long prefills is
# therefore not tunable here; these are kept only to document that the lever was
# tried and rejected by the engine.
# PARTIAL / LONG_PARTIAL intentionally unset.

serve_and_run () {
  local JUDGE=$1 GPU=$2 PORT=$3 CTX=$4 SEQS=$5
  local TP; TP=$(tp_for "$JUDGE")
  local TAG="${JUDGE}_${MODE}"
  local SERVE_LOG=$ROOT/s4_serve_${TAG}.log
  local RUN_LOG=$ROOT/s4_run_${TAG}.log

  if [ "$JUDGE" = "Qwen3.6-35B-A3B" ]; then
    export HF_HOME=/data5/user/hf_cache HF_HUB_CACHE=/data5/user/hf_cache/hub
  else
    export HF_HUB_CACHE=$HUB
  fi
  [ "$TP" -gt 1 ] && export NCCL_NET_PLUGIN=none NCCL_IB_DISABLE=1 \
                            NCCL_SOCKET_IFNAME=lo VLLM_HOST_IP=127.0.0.1
  local SNAP; SNAP=$(snap_for "$JUDGE")
  [ -d "$SNAP" ] || { echo "$JUDGE: snapshot missing: $SNAP" >&2; return 2; }

  : > "$SERVE_LOG"
  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name probe \
    --tensor-parallel-size "$TP" --max-model-len "$CTX" \
    --gpu-memory-utilization 0.95 --max-num-seqs "$SEQS" \
    --max-num-batched-tokens "$BATCH_TOK" \
    --port "$PORT" >> "$SERVE_LOG" 2>&1 &

  printf '%s serving' "$JUDGE"
  local up=0
  for _ in $(seq 1 300); do
    curl -sf "http://localhost:$PORT/v1/models" >/dev/null 2>&1 && { up=1; echo " up"; break; }
    printf .; sleep 5
  done
  [ "$up" -eq 1 ] || { echo; echo "$JUDGE: SERVE FAILED"; tail -20 "$SERVE_LOG"; return 3; }

  $PY analysis/s4_hindsight.py --judge "$JUDGE" --port "$PORT" --mode "$MODE" \
      --ctx "$CTX" --conc "$CONC" > "$RUN_LOG" 2>&1
  local rc=$?
  pkill -f "vllm serve.*--port $PORT" 2>/dev/null || true
  echo "$JUDGE $MODE finished rc=$rc -> $RUN_LOG"
  return $rc
}

if [ "$MODE" = "main" ]; then
  CTX=32768; QSEQS=128; LSEQS=64; QPORT=8071; LPORT=8072
else
  # long-context sub-pass: 36,864 ctx, batch 16 — KV cache scales with ctx x seqs and
  # 128 sequences at 36k does not fit in 80GB
  CTX=36864; QSEQS=16; LSEQS=16; QPORT=8073; LPORT=8074
fi

R1=0; R2=0
if [ "$JUDGES" = "both" ] || [ "$JUDGES" = "llama" ]; then
  serve_and_run Llama-3.3-70B-Instruct "$LLAMA_GPUS" "$LPORT" "$CTX" "$LSEQS" &
  P2=$!
fi
if [ "$JUDGES" = "both" ] || [ "$JUDGES" = "qwen" ]; then
  serve_and_run Qwen3.6-35B-A3B "$QWEN_GPU" "$QPORT" "$CTX" "$QSEQS" &
  P1=$!
fi
[ -n "${P2:-}" ] && { wait $P2; R2=$?; }
[ -n "${P1:-}" ] && { wait $P1; R1=$?; }
echo "S4 $MODE done: qwen rc=$R1 llama rc=$R2"
exit $(( R1 || R2 ))
