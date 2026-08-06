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
    --port "$PORT" >> "$SERVE_LOG" 2>&1 &

  printf '%s serving' "$JUDGE"
  local up=0
  for _ in $(seq 1 300); do
    curl -sf "http://localhost:$PORT/v1/models" >/dev/null 2>&1 && { up=1; echo " up"; break; }
    printf .; sleep 5
  done
  [ "$up" -eq 1 ] || { echo; echo "$JUDGE: SERVE FAILED"; tail -20 "$SERVE_LOG"; return 3; }

  $PY analysis/s4_hindsight.py --judge "$JUDGE" --port "$PORT" --mode "$MODE" \
      --ctx "$CTX" > "$RUN_LOG" 2>&1
  local rc=$?
  pkill -f "vllm serve.*--port $PORT" 2>/dev/null || true
  echo "$JUDGE $MODE finished rc=$rc -> $RUN_LOG"
  return $rc
}

if [ "$MODE" = "main" ]; then
  # served window 32,768; Qwen clamped to 128 seqs (hybrid Mamba cache-block limit)
  serve_and_run Qwen3.6-35B-A3B        0 8071 32768 128 &
  P1=$!
  serve_and_run Llama-3.3-70B-Instruct 1,2 8072 32768  64 &
  P2=$!
else
  # long-context sub-pass: 36,864 ctx, batch 16 — KV cache scales with ctx x seqs and
  # 128 sequences at 36k does not fit in 80GB
  serve_and_run Qwen3.6-35B-A3B        0 8073 36864 16 &
  P1=$!
  serve_and_run Llama-3.3-70B-Instruct 1,2 8074 36864 16 &
  P2=$!
fi
wait $P1; R1=$?
wait $P2; R2=$?
echo "S4 $MODE done: qwen rc=$R1 llama rc=$R2"
exit $(( R1 || R2 ))
