#!/usr/bin/env bash
# One HotpotQA ENTANGLED arm, end to end, for a single agent model.
#
# Serial by design: serve one checkpoint, generate, probe, tear the server down,
# then move to the next model. Generation and post-hoc probing must share one
# serving window because the probes read the AGENT's own logprobs — they cannot
# be deferred the way the judge can. The judge is Azure-side and needs no GPU,
# so it is deliberately NOT run here; batch it with run_hotpot_judge.sh.
#
# RESUMABLE. Work is cut into SHARDS, each writing its own file and dropping a
# .done marker only on clean exit. Re-running skips finished shards, discards the
# partial output of any shard that died, and redoes just that one. A crashed
# server, an OOM, or a killed terminal costs one shard, never the whole arm.
# Neither chat_react_hotpot_entangled.py nor run_probes.py skips completed work
# on its own — both append blindly — so shard granularity IS the resume unit, and
# a partial shard must be truncated rather than continued or it would duplicate.
#
# Nothing about the pipeline is modified: this calls the same phase scripts
# run_hotpot_acquisition.sh calls, with the decoupled half skipped, so the record
# schema stays byte-compatible with the ALFWorld arms and the existing Qwen
# HotpotQA arm. That comparability is the whole point of the run.
#
# Usage: run_hotpot_arm.sh <model_key> [N_EPISODES=500] [CONCURRENCY=4] [SHARDS=20]
#   model_key: phi4mini | gemma4b | mistral7b | llama8b | llama70b | qwen35b
set -euo pipefail

RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=${HOTPOT_PY:-/opt/anaconda3/envs/Jagent/bin/python}
V=${HOTPOT_VLLM:-/opt/anaconda3/envs/yllm/bin/vllm}
PORT=${HOTPOT_PORT:-8071}

KEY=${1:?usage: run_hotpot_arm.sh <model_key> [N_EPISODES] [CONCURRENCY] [SHARDS]}
N_EPISODES=${2:-500}
CONC=${3:-4}
SHARDS=${4:-20}

# 500 episodes matches the existing Qwen HotpotQA arm (2235 steps) so the cells are
# balanced. Do not change it for one model only.
# 20 shards over 500 episodes = 25 episodes lost in the worst crash, not 500.

# Main HF cache is /data3/hg_weight/hg_weight — models sit directly under it as
# models--<org>--<name>/, so it is HF_HUB_CACHE, not HF_HOME. Qwen3.6-35B-A3B is the
# exception: it lives in a different cache and is served by repo id under HF_HOME.
HUB=/data3/hg_weight/hg_weight
export HF_HUB_CACHE=$HUB
export HF_HUB_OFFLINE=1

# UTIL is the KV reservation, sized to the weights: the smalls need only headroom
# over a few GB, the big two need most of a card. NEED tracks UTIL as the
# free-memory bar for picking a GPU.
case "$KEY" in
  phi4mini)  SNAP=$HUB/models--microsoft--Phi-4-mini-instruct/snapshots/5889daf2bc85b5300eba142a516fe65b0c2ef3f7;      TP=1; UTIL=0.30; NEED=28000 ;;
  gemma4b)   SNAP=$HUB/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767;               TP=1; UTIL=0.30; NEED=28000 ;;
  mistral7b) SNAP=$HUB/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de; TP=1; UTIL=0.30; NEED=28000 ;;
  llama8b)   SNAP=$HUB/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659;   TP=1; UTIL=0.30; NEED=28000 ;;
  # 132GB over 2 cards -> ~66GB of weights per card, so the reservation cannot be small.
  llama70b)  SNAP=$HUB/models--meta-llama--Llama-3.3-70B-Instruct/snapshots/6f6073b423013f6a7d4d9f39144961bfbfbc386b;  TP=2; UTIL=0.90; NEED=78000 ;;
  qwen35b)   SNAP=Qwen/Qwen3.6-35B-A3B; TP=1; UTIL=0.90; NEED=78000; export HF_HOME=/data5/user/hf_cache ;;
  *) echo "unknown model key: $KEY" >&2; exit 1 ;;
esac
NEED_MIB=${HOTPOT_NEED_MIB:-$NEED}

# Snapshot hashes are pinned so an arm is reproducible; fall back to whatever the
# cache holds if a pin goes stale, and say so rather than failing silently.
if [ "$KEY" != qwen35b ] && [ ! -d "$SNAP" ]; then
  ALT=$(ls -d "$(dirname "$(dirname "$SNAP")")"/snapshots/*/ 2>/dev/null | head -1)
  [ -n "$ALT" ] || { echo "no snapshot for $KEY under $HUB" >&2; exit 1; }
  echo "WARNING: pinned snapshot missing, using $ALT" >&2
  SNAP=${ALT%/}
fi

# Mistral needs protobuf + sentencepiece in the harness env for its tokenizer;
# HotpotQA needs gym==0.26.2 + beautifulsoup4 for wikienv. Both already installed
# in Jagent — noted here because a fresh env fails obscurely without them.

# This box's NCCL net plugin is broken; TP>1 will not initialise without these.
if [ "$TP" -gt 1 ]; then
  export NCCL_NET_PLUGIN=none NCCL_IB_DISABLE=1
  export NCCL_SOCKET_IFNAME=lo VLLM_HOST_IP=127.0.0.1
fi

OUT=${HOTPOT_OUT:-$RD/result/hotpot_$KEY}
SH=$OUT/shards
ENT_UQ=$OUT/uq_hotpot_entangled.jsonl
ENT_PROBES=$OUT/probes_hotpot_entangled.jsonl
mkdir -p "$SH"

echo "arm=$KEY tp=$TP episodes=$N_EPISODES shards=$SHARDS concurrency=$CONC"
echo "snapshot=$SNAP"
echo "out=$OUT"

# Which shards still need doing, for a phase whose shard files are named <prefix>.wN.jsonl.
# A shard with no .done marker is discarded and redone: its file may be a partial
# write, and appending to it would duplicate records.
pending() {
  local prefix=$1 i out
  for i in $(seq 0 $((SHARDS-1))); do
    if [ -e "$SH/$prefix.w$i.done" ]; then continue; fi
    out="$SH/$prefix.w$i.jsonl"
    [ -e "$out" ] && rm -f "$out"
    echo "$i"
  done
}

# Run a phase's pending shards, at most CONC at a time. $1=prefix, rest=command
# template where {W} is replaced by the shard id. The .done marker is written only
# if the shard's process exits 0.
run_shards() {
  local prefix=$1; shift
  local todo running=0 rc=0
  todo=$(pending "$prefix")
  [ -z "$todo" ] && { echo "  all $SHARDS shards already done"; return 0; }
  echo "  pending shards: $(echo "$todo" | tr '\n' ' ')"
  for w in $todo; do
    ( "$@" "$w" && touch "$SH/$prefix.w$w.done" ) &
    running=$((running+1))
    if [ "$running" -ge "$CONC" ]; then wait -n || rc=1; running=$((running-1)); fi
  done
  wait || rc=1
  return $rc
}

# --- pick GPUs ----------------------------------------------------------------
# HOTPOT_GPU pins the cards explicitly (comma-separated, e.g. "4" or "3,4") and
# skips the free-memory scan. Use it to stay off cards other users are on, or when
# you want a specific pair for TP.
if [ -n "${HOTPOT_GPU:-}" ]; then
  GPU=$HOTPOT_GPU
  n=$(echo "$GPU" | tr ',' '\n' | grep -c .)
  [ "$n" -eq "$TP" ] || { echo "HOTPOT_GPU lists $n GPU(s) but $KEY needs TP=$TP" >&2; exit 1; }
else
  mapfile -t FREE < <(nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader,nounits \
    | awk -F', ' -v need="$NEED_MIB" '($3-$2) >= need {print $1}')
  [ "${#FREE[@]}" -ge "$TP" ] || { echo "need $TP GPU(s) with ${NEED_MIB}MiB free; have ${#FREE[@]}" >&2; exit 1; }
  GPU=$(IFS=,; echo "${FREE[*]:0:$TP}")
fi
echo "gpus=$GPU"

# --- serve --------------------------------------------------------------------
SERVE_LOG=$OUT/serve.log
: > "$SERVE_LOG"
# setsid is load-bearing: without it the server shares this script's process group
# in a non-interactive shell, and the `kill -- -PGID` teardown takes the driver down
# with it. That silently ended a whole run once.
# --gpu-memory-utilization is a RESERVATION, not a ceiling — vLLM fills whatever it
# reserves with KV cache. At 0.85 a 7GB model took 69GB. 0.30 (~24GB) is ample for
# this batch-1 16k-context workload and leaves the box usable by others.
CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name qwen \
  --tensor-parallel-size "$TP" --max-model-len 16384 \
  --gpu-memory-utilization "${HOTPOT_GPU_UTIL:-$UTIL}" --max-num-seqs 64 \
  --port "$PORT" >> "$SERVE_LOG" 2>&1 &
SRV=$!
trap 'kill -- -$(ps -o pgid= $SRV 2>/dev/null | tr -d " ") 2>/dev/null || true' EXIT

echo -n "waiting for server"
for _ in $(seq 1 240); do
  curl -sf "http://localhost:$PORT/v1/models" >/dev/null 2>&1 && { echo " up"; break; }
  kill -0 $SRV 2>/dev/null || { echo; echo "server died — see $SERVE_LOG" >&2; tail -20 "$SERVE_LOG" >&2; exit 1; }
  echo -n .; sleep 5
done
curl -sf "http://localhost:$PORT/v1/models" >/dev/null || { echo "server never came up" >&2; exit 1; }

# --- shared agent/probe environment ------------------------------------------
# Sampling params pinned explicitly rather than left to defaults: every arm must
# decode identically or cross-model comparisons measure decoding, not the model.
export REACT_MODEL=qwen PROBE_MODEL=qwen
export REACT_TOKENIZER=$SNAP PROBE_TOKENIZER=$SNAP
export REACT_BASE_URL=http://localhost:$PORT/v1 PROBE_BASE_URL=http://localhost:$PORT/v1
export REACT_TEMPERATURE=0.7 REACT_TOP_P=0.80 REACT_TOP_K=20 REACT_MIN_P=0.0
export REACT_PRESENCE_PENALTY=1.5 REACT_REPETITION_PENALTY=1.0
export REACT_MAX_STEPS=7 REACT_SEED=233 REACT_SEED_BASE=1000 REACT_SPLIT=dev
unset UQ_API_MODE UQ_RPM UQ_RATE_FILE REACT_API_KEY PROBE_API_KEY

cd "$RD/src"

gen_shard() {
  local w=$1
  REACT_N_EPISODES=$N_EPISODES REACT_NUM_WORKERS=$SHARDS REACT_WORKER_ID="$w" \
  REACT_RUN_ID="hotpot_entangled_$KEY" REACT_UQLOG="$SH/uq.w$w.jsonl" \
    $PY -u chat_react_hotpot_entangled.py > "$SH/uq.w$w.log" 2>&1
}

probe_shard() {
  local w=$1
  PROBE_INPUT="$ENT_UQ" PROBE_OUTPUT="$SH/probes.w$w.jsonl" \
  PROBE_NUM_WORKERS=$SHARDS PROBE_WORKER_ID="$w" \
  PROBE_KINDS="ptrue,sep_verbalized,posthoc_numeric" \
  PROBE_STAGES="thought,action" PROBE_RESPONSE_KINDS="ptrue" \
    $PY -u run_probes.py > "$SH/probes.w$w.log" 2>&1
}

# --- phase 1: entangled generation --------------------------------------------
echo "phase 1/2: entangled generation"
run_shards uq gen_shard || { echo "generation incomplete — re-run to resume" >&2; exit 1; }
cat "$SH"/uq.w*.jsonl > "$ENT_UQ"      # rebuilt from shards; shards are kept
$PY audit_hotpot.py "$ENT_UQ" entangled | tee "$OUT/audit_hotpot_entangled.log" || true
# The audit exits non-zero on its own gate; a single empty thought_text trips it
# (1/2235 on the Qwen arm), so its verdict is recorded, not enforced.

# --- phase 2: post-hoc probes (same serving window) ---------------------------
echo "phase 2/2: post-hoc probes"
run_shards probes probe_shard || { echo "probing incomplete — re-run to resume" >&2; exit 1; }
cat "$SH"/probes.w*.jsonl > "$ENT_PROBES"

# Completion marker, so a chain can skip a finished arm without paying to load
# weights just to discover every shard is already done.
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/ARM_COMPLETE"

echo "DONE $KEY"
echo "  $ENT_UQ      ($(wc -l < "$ENT_UQ") records)"
echo "  $ENT_PROBES  ($(wc -l < "$ENT_PROBES") records)"
echo "judge NOT run (Azure, no GPU) — batch it with run_hotpot_judge.sh $OUT"
