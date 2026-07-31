#!/bin/bash
# Full ALFWorld runs for the 4 co-resident models on GPU0.
# Seen split, 140 episodes, step cap 50 (matches the Qwen-e1 / Llama-70B main runs for
# cross-model comparability). Identical prompts + sampling across all models.
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
cd $RD
export ALFWORLD_DATA=/home/user/.cache/alfworld HF_HUB_OFFLINE=1
OUT=$RD/result/models4
mkdir -p $OUT

run() {  # name port tokenizer
  REACT_BASE_URL=http://localhost:$2/v1 REACT_MODEL=$1 REACT_TOKENIZER=$3 \
  REACT_ENABLE_THINKING=none REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 \
  REACT_MAX_STEPS=50 \
  REACT_RUN_ID=decoupled_$1 REACT_UQLOG=$OUT/uq_decoupled_$1.jsonl \
    $PY -u src/chat_react.py > $OUT/gen_$1.log 2>&1
  echo "GEN_DONE $1 rc=$? lines=$(wc -l < $OUT/uq_decoupled_$1.jsonl 2>/dev/null)"
}

run gemma4b   8010 $B/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767 &
run phi4mini  8011 $B/models--microsoft--Phi-4-mini-instruct/snapshots/5889daf2bc85b5300eba142a516fe65b0c2ef3f7 &
run llama8b   8012 $B/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659 &
run mistral7b 8013 $B/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de &
wait
echo "=== FINAL SUCCESS RATES ==="
for m in gemma4b phi4mini llama8b mistral7b; do
  echo "  $m: $(grep -h '^FINAL' $OUT/gen_$m.log 2>/dev/null | tail -1)"
done
echo "ALL_4_FULL_DONE"
