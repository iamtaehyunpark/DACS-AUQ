#!/bin/bash
# DeepSeek-V4-Flash on ALFWorld via NVIDIA NIM (hosted API — no GPU used).
# Both arms: decoupled then entangled. Then P(True)-only probes, then Azure judge.
#
# Rate limit: account allows 40 RPM total. Each of the NW workers enforces a per-process
# minimum call interval of NW*60/40 s, so the fleet sums to <=40 RPM.
# thinking is forced OFF in uqlog API mode: with thinking on, gen_logprobs covers the
# reasoning channel and would silently misalign the token-entropy spans.
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/deepseek
# Rate control is a SHARED cross-process token bucket (UQ_RPM), not a per-process interval:
# N independent limiters still burst when they align, which produced 429s at only ~11 calls/min
# average. One shared timeline emits evenly-spaced calls and can safely approach the quota.
# Worker count then only needs to be enough to keep that stream saturated:
# workers >= RPM * latency / 60 = 40 * 25s / 60 ~= 17.
NW=16
RPM=40
cd $RD
source ~/.config/nvidia_api.env
source ~/.config/azure_judge.env
export ALFWORLD_DATA=/home/user/.cache/alfworld
mkdir -p $OUT

# shared token bucket across ALL workers (fresh slot file each run)
rm -f /tmp/uq_rate_slot.lock
export UQ_API_MODE=1 UQ_RPM=$RPM UQ_RATE_FILE=/tmp/uq_rate_slot.lock
INTERVAL="shared-bucket"
export REACT_API_KEY=$NVIDIA_API_KEY PROBE_API_KEY=$NVIDIA_API_KEY
export REACT_BASE_URL=https://integrate.api.nvidia.com/v1
export REACT_MODEL=$NVIDIA_MODEL REACT_TOKENIZER=none REACT_ENABLE_THINKING=none
export REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 REACT_MAX_STEPS=50
echo "[ds] NW=$NW RPM=$RPM per-worker interval=${INTERVAL}s"

gen_arm() {   # arm  script
  arm=$1; script=$2
  rm -f $OUT/uq_${arm}_ds.w*.jsonl
  pids=()
  for w in $(seq 0 $((NW-1))); do
    REACT_NUM_WORKERS=$NW REACT_WORKER_ID=$w \
    REACT_RUN_ID=${arm}_ds REACT_UQLOG=$OUT/uq_${arm}_ds.w${w}.jsonl \
      $PY -u src/$script > $OUT/gen_${arm}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat $OUT/uq_${arm}_ds.w*.jsonl > $OUT/uq_${arm}_ds.jsonl
  succ=$(grep -h "^FINAL" $OUT/gen_${arm}_w*.log 2>/dev/null | grep -oE "[0-9]+/[0-9]+" | awk -F/ "{s+=\$1; t+=\$2} END {print s\"/\"t}")
  echo "DS_GEN_DONE $arm lines=$(wc -l < $OUT/uq_${arm}_ds.jsonl) success=$succ"
}

probe_arm() {  # arm
  arm=$1
  for spec in "thought,action::" "response::.aggtrue_ptrue"; do
    stages=${spec%%::*}; sfx=${spec##*::}
    out=$OUT/probes_${arm}_ds${sfx}.jsonl
    rm -f ${out%.jsonl}.w*.jsonl
    pids=()
    for w in $(seq 0 $((NW-1))); do
      PROBE_INPUT=$OUT/uq_${arm}_ds.jsonl PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
        PROBE_NUM_WORKERS=$NW PROBE_WORKER_ID=$w \
        PROBE_BASE_URL=https://integrate.api.nvidia.com/v1 PROBE_MODEL=$NVIDIA_MODEL \
        PROBE_TOKENIZER=none PROBE_KINDS=ptrue PROBE_STAGES="$stages" \
        PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
        $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
      pids+=($!)
    done
    wait "${pids[@]}"
    cat ${out%.jsonl}.w*.jsonl > $out
    echo "DS_PROBES_DONE $arm$sfx records=$(wc -l < $out)"
  done
}

gen_arm decoupled chat_react.py
probe_arm decoupled
JUDGE_INPUT=$OUT/uq_decoupled_ds.jsonl JUDGE_OUTPUT=$OUT/judge_decoupled_ds.jsonl JUDGE_WORKERS=8 \
  $PY -u src/judge_e0.py > $OUT/judge_decoupled.log 2>&1
echo "DS_JUDGE_DONE decoupled records=$(wc -l < $OUT/judge_decoupled_ds.jsonl 2>/dev/null)"

gen_arm entangled chat_react_entangled.py
probe_arm entangled
JUDGE_INPUT=$OUT/uq_entangled_ds.jsonl JUDGE_OUTPUT=$OUT/judge_entangled_ds.jsonl JUDGE_WORKERS=8 \
  $PY -u src/judge_e0.py > $OUT/judge_entangled.log 2>&1
echo "DS_JUDGE_DONE entangled records=$(wc -l < $OUT/judge_entangled_ds.jsonl 2>/dev/null)"

echo "DS_ALL_DONE"
