#!/bin/bash
# Phase 2-3 for the 4 co-resident models: waits for generation, then
#   probes (full per-stage roster) + AGG-true whole-response P(True)   [needs GPU servers]
#   -> frees GPU0 -> 3-judge E0 (Azure, no GPU).
# AGG-true is run up-front here so the v2 tables have that cell natively.
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/models4
cd $RD
source ~/.config/azure_judge.env
export HF_HUB_OFFLINE=1
NW=4          # probe workers per model (4 models x 4 = 16 concurrent requests to GPU0)

echo "[p23] waiting for generation to finish..."
until grep -q ALL_4_FULL_DONE /tmp/full_4models.out 2>/dev/null; do sleep 60; done
echo "[p23] generation done $(date)"

# ---- probes (per-stage roster + AGG-true response P(True)) ----
probe() {  # name port tokenizer stages kinds suffix
  name=$1; port=$2; tok=$3; stages=$4; kinds=$5; sfx=$6
  uq=$OUT/uq_decoupled_$name.jsonl
  out=$OUT/probes_$name$sfx.jsonl
  rm -f ${out%.jsonl}.w*.jsonl
  pids=()
  for w in $(seq 0 $((NW-1))); do
    PROBE_INPUT=$uq PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
      PROBE_NUM_WORKERS=$NW PROBE_WORKER_ID=$w \
      PROBE_BASE_URL=http://localhost:$port/v1 PROBE_MODEL=$name PROBE_TOKENIZER=$tok \
      PROBE_KINDS="$kinds" PROBE_STAGES="$stages" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat ${out%.jsonl}.w*.jsonl > $out
  echo "PROBES_DONE $name$sfx records=$(wc -l < $out)"
}

G=$B/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767
P=$B/models--microsoft--Phi-4-mini-instruct/snapshots/5889daf2bc85b5300eba142a516fe65b0c2ef3f7
L=$B/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
M=$B/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de
FULL="ptrue,sep_verbalized,posthoc_numeric,targeted"

echo "[p23] per-stage probes"
probe gemma4b   8010 $G "thought,action" "$FULL" "" &
probe phi4mini  8011 $P "thought,action" "$FULL" "" &
probe llama8b   8012 $L "thought,action" "$FULL" "" &
probe mistral7b 8013 $M "thought,action" "$FULL" "" &
wait

echo "[p23] AGG-true whole-response P(True)"
probe gemma4b   8010 $G "response" "ptrue" ".aggtrue_ptrue" &
probe phi4mini  8011 $P "response" "ptrue" ".aggtrue_ptrue" &
probe llama8b   8012 $L "response" "ptrue" ".aggtrue_ptrue" &
probe mistral7b 8013 $M "response" "ptrue" ".aggtrue_ptrue" &
wait
echo "ALL_PROBES_DONE"

# ---- free GPU0: nothing below needs vLLM ----
for n in gemma4b phi4mini llama8b mistral7b; do
  VPID=$(pgrep -f "served-model-name $n" | head -1)
  [ -n "$VPID" ] && { PGID=$(ps -o pgid= -p $VPID | tr -d ' '); kill -9 -$PGID 2>/dev/null; }
  pkill -9 -f "served-model-name $n" 2>/dev/null
done
sleep 5
echo "GPU0_FREED $(date)"

# ---- 3-judge E0 (Azure) ----
for n in gemma4b phi4mini llama8b mistral7b; do
  JUDGE_INPUT=$OUT/uq_decoupled_$n.jsonl JUDGE_OUTPUT=$OUT/judge_$n.jsonl JUDGE_WORKERS=8 \
    $PY -u src/judge_e0.py > $OUT/judge_$n.log 2>&1
  echo "JUDGE_DONE $n records=$(wc -l < $OUT/judge_$n.jsonl 2>/dev/null)"
done
echo "ALL_4_PROBES_JUDGE_DONE"
