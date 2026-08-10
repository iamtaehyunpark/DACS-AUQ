#!/usr/bin/env bash
# S4 throughput probe — the precondition D1 attaches to the hindsight pass.
#
# EXECUTION_HANDOVER.md §1 requires a 500-step probe before any GPU stage sizes
# itself, and STOP_GATE_DECISIONS.md D1.1 makes it condition one of the approval.
# This measures the rate on HINDSIGHT-LENGTH prompts, not the banked online ones:
# hindsight carries the full trajectory plus episode outcome, so a rate measured on
# short prompts would flatter the projection and is the likeliest reason the
# handover's 6-10 A100-hour estimate and S4_COST's 1.3-3.9 disagree.
#
# Serves one capable judge, replays 500 real steps at hindsight length, records
# wall-clock and tokens, and writes the measured rate. It does NOT run the pass.
set -euo pipefail

ROOT=/data5/kje/MULTIAGENT/DACS-AUQ
cd "$ROOT"

JUDGE=${JUDGE:-Qwen3.6-35B-A3B}
GPU=${GPU:-0}
PORT=${PORT:-8071}
N=${N:-500}
OUT=${OUT:-runs/s4_probe.json}
HUB=${HUB:-/data3/hf_cache/hub}
# vllm is not on the default PATH on this box; the cross-probe scripts pin the conda
# env explicitly (scripts/run_crossprobe_matrix.sh:33) and this must match or the
# serve step dies with "failed to run command 'vllm'".
V=${XP_VLLM:-/opt/anaconda3/envs/yllm/bin/vllm}
PY=${XP_PY:-/opt/anaconda3/envs/yllm/bin/python}

# Same serving conventions as the cross-probe matrix (scripts/run_crossprobe_matrix.sh):
# Qwen lives in a different HF cache and HF_HUB_CACHE takes precedence over HF_HOME,
# so both must point at the right place or the resolver fails under HF_HUB_OFFLINE.
if [ "$JUDGE" = "Qwen3.6-35B-A3B" ]; then
  export HF_HOME=/data5/user/hf_cache HF_HUB_CACHE=/data5/user/hf_cache/hub
  SEQS=128          # hybrid Mamba cache-block limit; 256 fails to allocate
  TP=1
else
  export HF_HUB_CACHE=$HUB
  SEQS=64
  TP=${TP:-1}
fi
[ "$TP" -gt 1 ] && export NCCL_NET_PLUGIN=none NCCL_IB_DISABLE=1 \
                          NCCL_SOCKET_IFNAME=lo VLLM_HOST_IP=127.0.0.1

SNAP=$($PY - <<PY
import os,glob
hub=os.environ.get("HF_HUB_CACHE","")
pat=[p for p in glob.glob(os.path.join(hub,"models--*","snapshots","*")) if "$JUDGE".split("/")[-1].lower() in p.lower()]
print(pat[0] if pat else "")
PY
)
if [ -z "$SNAP" ]; then echo "S4 probe: snapshot for $JUDGE not found in $HF_HUB_CACHE" >&2; exit 2; fi
echo "S4 probe: $JUDGE  snapshot=$SNAP  gpu=$GPU  port=$PORT  n=$N"

SERVE_LOG=$ROOT/s4_probe_serve.log
: > "$SERVE_LOG"
CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name probe \
  --tensor-parallel-size "$TP" --max-model-len 32768 \
  --gpu-memory-utilization 0.90 --max-num-seqs "$SEQS" \
  --port "$PORT" >> "$SERVE_LOG" 2>&1 &
SRV=$!
cleanup() { pkill -f "vllm serve.*--port $PORT" 2>/dev/null || true; }
trap cleanup EXIT

printf 'serving'
up=0
for _ in $(seq 1 240); do
  curl -sf "http://localhost:$PORT/v1/models" >/dev/null 2>&1 && { up=1; echo " up"; break; }
  kill -0 $SRV 2>/dev/null || break
  printf .; sleep 5
done
[ "$up" -eq 1 ] || { echo; echo "S4 probe: SERVE FAILED"; tail -20 "$SERVE_LOG"; exit 3; }

PORT=$PORT N=$N JUDGE=$JUDGE OUT=$OUT $PY analysis/s4_probe.py
echo "S4 probe: wrote $OUT"
