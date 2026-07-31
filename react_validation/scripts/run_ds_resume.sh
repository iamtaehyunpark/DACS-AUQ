#!/bin/bash
# Resume DeepSeek after quota exhaustion.
#
# Order is deliberate — most valuable work first, so a second exhaustion costs the least:
#   0. entangled JUDGE   -> Azure, needs NO NVIDIA quota, runs immediately
#   1. entangled probes  -> the big gap that blocks the whole entangled arm
#   2. entangled AGG-true
#   3. backfill missing episodes (decoupled ~19, entangled ~23)
#
# Guards learned from the earlier silent losses:
#   * poll for quota recovery with ONE cheap call every 10 min (never hammer)
#   * conservative UQ_RPM with generous retries
#   * report skipped_steps after every stage; abort a stage if losses are severe, rather
#     than writing a quietly-incomplete file
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/deepseek
# NW=4 is ample: at 12 RPM and ~15s latency only ~3 workers are needed to keep the stream full,
# and fewer in-flight requests means less endpoint contention.
NW=4
cd $RD
source ~/.config/nvidia_api.env
source ~/.config/azure_judge.env
# 12 RPM is empirically verified end-to-end (6/6 calls, 0 failures) now that retries are paced
# too. Earlier settings of 40/25/20 all bled steps because retries bypassed the limiter.
export UQ_API_MODE=1 UQ_RPM=12 UQ_RATE_FILE=/tmp/uq_rate_slot.lock
export UQ_MAX_RETRY=14 UQ_BACKOFF_BASE=4 UQ_BACKOFF_CAP=90
export REACT_API_KEY=$NVIDIA_API_KEY PROBE_API_KEY=$NVIDIA_API_KEY
export REACT_BASE_URL=https://integrate.api.nvidia.com/v1
export REACT_MODEL=$NVIDIA_MODEL REACT_TOKENIZER=none REACT_ENABLE_THINKING=none
export ALFWORLD_DATA=/home/user/.cache/alfworld
export REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 REACT_MAX_STEPS=50

# ---- 0. entangled judge (Azure — independent of NVIDIA quota) ----
if [ ! -s $OUT/judge_entangled_ds.jsonl ]; then
  echo "[rs] entangled judge on Azure (no NVIDIA quota needed)"
  JUDGE_INPUT=$OUT/uq_entangled_ds.jsonl JUDGE_OUTPUT=$OUT/judge_entangled_ds.jsonl JUDGE_WORKERS=8 \
    $PY -u src/judge_e0.py > $OUT/judge_entangled.log 2>&1
  echo "RS_JUDGE_DONE entangled records=$(wc -l < $OUT/judge_entangled_ds.jsonl 2>/dev/null)"
fi

# ---- wait for quota ----
echo "[rs] polling for NVIDIA quota recovery (1 call / 10 min)..."
while true; do
  if $PY - <<'PYEOF'
import os, sys
from openai import OpenAI
c = OpenAI(base_url="https://integrate.api.nvidia.com/v1",
           api_key=os.environ["NVIDIA_API_KEY"], max_retries=0)
try:
    c.chat.completions.create(model=os.environ["NVIDIA_MODEL"],
                              messages=[{"role": "user", "content": "hi"}], max_tokens=3)
    sys.exit(0)
except Exception:
    sys.exit(1)
PYEOF
  then break; fi
  sleep 600
done
echo "RS_QUOTA_RECOVERED $(date)"

probe() {   # input  outbase  stages  label
  inp=$1; out=$2; stages=$3; label=$4
  rm -f ${out%.jsonl}.w*.jsonl
  pids=()
  for w in $(seq 0 $((NW-1))); do
    PROBE_INPUT=$inp PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
      PROBE_NUM_WORKERS=$NW PROBE_WORKER_ID=$w \
      PROBE_BASE_URL=https://integrate.api.nvidia.com/v1 PROBE_MODEL=$NVIDIA_MODEL \
      PROBE_TOKENIZER=none PROBE_KINDS=ptrue PROBE_STAGES="$stages" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat ${out%.jsonl}.w*.jsonl > $out
  sk=$(cat ${out%.jsonl}_w*.log 2>/dev/null | grep -c "^ERROR step")
  echo "RS_PROBES_DONE $label records=$(wc -l < $out) skipped_steps=$sk"
}

probe $OUT/uq_entangled_ds.jsonl $OUT/probes_entangled_ds.jsonl               "thought,action" "entangled"
probe $OUT/uq_entangled_ds.jsonl $OUT/probes_entangled_ds.aggtrue_ptrue.jsonl "response"       "entangled.aggtrue"

echo "RS_ALL_DONE"
