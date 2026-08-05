#!/bin/bash
# Backfill the DeepSeek decoupled episodes lost when 3 workers died on APITimeoutError
# (the retry matcher missed "Request timed out."; fixed in uqlog).
# Uses the REACT_ONLY_TASKS_FILE allow-list to run ONLY the missing tasks, then merges —
# rather than regenerating all 140.
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/deepseek
NW=4
cd $RD
source ~/.config/nvidia_api.env
source ~/.config/azure_judge.env
export ALFWORLD_DATA=/home/user/.cache/alfworld
export UQ_API_MODE=1 UQ_RPM=40 UQ_RATE_FILE=/tmp/uq_rate_slot.lock
export REACT_API_KEY=$NVIDIA_API_KEY PROBE_API_KEY=$NVIDIA_API_KEY
export REACT_BASE_URL=https://integrate.api.nvidia.com/v1
export REACT_MODEL=$NVIDIA_MODEL REACT_TOKENIZER=none REACT_ENABLE_THINKING=none
export REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 REACT_MAX_STEPS=50

echo "[bf] waiting for the main DeepSeek run to finish..."
until grep -q "DS_ALL_DONE" /tmp/ds_alfworld.out 2>/dev/null; do sleep 120; done
echo "[bf] main run done $(date)"

N=$(wc -l < /tmp/ds_missing_tasks.txt 2>/dev/null || echo 0)
if [ "$N" -eq 0 ]; then echo "[bf] nothing missing"; exit 0; fi
echo "[bf] backfilling $N decoupled episodes"

rm -f $OUT/uq_bf_ds.w*.jsonl
pids=()
for w in $(seq 0 $((NW-1))); do
  REACT_NUM_WORKERS=$NW REACT_WORKER_ID=$w \
  REACT_ONLY_TASKS_FILE=/tmp/ds_missing_tasks.txt \
  REACT_RUN_ID=decoupled_ds REACT_UQLOG=$OUT/uq_bf_ds.w${w}.jsonl \
    $PY -u src/chat_react.py > $OUT/gen_bf_w${w}.log 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
cat $OUT/uq_bf_ds.w*.jsonl >> $OUT/uq_decoupled_ds.jsonl
echo "BF_GEN_DONE merged; total lines=$(wc -l < $OUT/uq_decoupled_ds.jsonl)"

# probes for just the backfilled steps, then merge into the existing probe files
for spec in "thought,action::"  "response::.aggtrue_ptrue"; do
  stages=${spec%%::*}; sfx=${spec##*::}
  rm -f $OUT/probes_bf${sfx}.w*.jsonl
  pids=()
  for w in $(seq 0 $((NW-1))); do
    PROBE_INPUT=$OUT/uq_bf_ds.w${w}.jsonl PROBE_OUTPUT=$OUT/probes_bf${sfx}.w${w}.jsonl \
      PROBE_NUM_WORKERS=1 PROBE_WORKER_ID=0 \
      PROBE_BASE_URL=https://integrate.api.nvidia.com/v1 PROBE_MODEL=$NVIDIA_MODEL \
      PROBE_TOKENIZER=none PROBE_KINDS=ptrue PROBE_STAGES="$stages" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > $OUT/probes_bf${sfx}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat $OUT/probes_bf${sfx}.w*.jsonl >> $OUT/probes_decoupled_ds${sfx}.jsonl
  echo "BF_PROBES_DONE $sfx total=$(wc -l < $OUT/probes_decoupled_ds${sfx}.jsonl)"
done

# judge is resumable by task_id: re-running over the merged log only labels the new tasks
JUDGE_INPUT=$OUT/uq_decoupled_ds.jsonl JUDGE_OUTPUT=$OUT/judge_decoupled_ds.jsonl JUDGE_WORKERS=8 \
  $PY -u src/judge_e0.py > $OUT/judge_bf.log 2>&1
echo "BF_JUDGE_DONE records=$(wc -l < $OUT/judge_decoupled_ds.jsonl 2>/dev/null)"
echo "BF_ALL_DONE"
