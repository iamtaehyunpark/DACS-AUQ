#!/bin/bash
# Finish the DeepSeek ENTANGLED arm after 429s caused run_probes.py to SKIP steps.
#
# run_probes.py wraps each step in try/except so one failure cannot kill a sweep — which means
# an exhausted-retry 429 silently DROPS that step. At UQ_RPM=40 we sat right on the quota edge,
# so drops accumulated. Backing off to 25 RPM trades ~40% throughput for complete data.
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/deepseek
NW=10
cd $RD
source ~/.config/nvidia_api.env
source ~/.config/azure_judge.env
export UQ_API_MODE=1 UQ_RPM=25 UQ_RATE_FILE=/tmp/uq_rate_slot.lock
export UQ_MAX_RETRY=14 UQ_BACKOFF_BASE=4 UQ_BACKOFF_CAP=90
export PROBE_API_KEY=$NVIDIA_API_KEY
rm -f /tmp/uq_rate_slot.lock

probe() {   # stages suffix
  stages=$1; sfx=$2
  out=$OUT/probes_entangled_ds${sfx}.jsonl
  rm -f ${out%.jsonl}.w*.jsonl
  pids=()
  for w in $(seq 0 $((NW-1))); do
    PROBE_INPUT=$OUT/uq_entangled_ds.jsonl PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
      PROBE_NUM_WORKERS=$NW PROBE_WORKER_ID=$w \
      PROBE_BASE_URL=https://integrate.api.nvidia.com/v1 PROBE_MODEL=$NVIDIA_MODEL \
      PROBE_TOKENIZER=none PROBE_KINDS=ptrue PROBE_STAGES="$stages" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat ${out%.jsonl}.w*.jsonl > $out
  skipped=$(grep -hc "^ERROR step" ${out%.jsonl}_w*.log 2>/dev/null | paste -sd+ | bc)
  echo "DSE_PROBES_DONE entangled$sfx records=$(wc -l < $out) skipped_steps=${skipped:-0}"
}

probe "thought,action" ""
probe "response"       ".aggtrue_ptrue"

JUDGE_INPUT=$OUT/uq_entangled_ds.jsonl JUDGE_OUTPUT=$OUT/judge_entangled_ds.jsonl JUDGE_WORKERS=8 \
  $PY -u src/judge_e0.py > $OUT/judge_entangled.log 2>&1
echo "DSE_JUDGE_DONE entangled records=$(wc -l < $OUT/judge_entangled_ds.jsonl 2>/dev/null)"
echo "DS_ALL_DONE"
