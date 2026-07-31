#!/bin/bash
# Judge chain — runs ALONGSIDE the GPU chain. Azure-only, uses no GPU, so each model is judged
# as soon as its generation finishes (while the GPU is busy probing / on the next model).
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/models4
cd $RD
source ~/.config/azure_judge.env

for m in phi4mini gemma4b mistral7b llama8b; do
  echo "[judge] waiting for GEN_DONE $m ..."
  until grep -q "GEN_DONE $m " /tmp/seq_4models.out 2>/dev/null; do
    grep -q SEQ_ALL_DONE /tmp/seq_4models.out 2>/dev/null && break
    sleep 60
  done
  [ -s $OUT/uq_decoupled_$m.jsonl ] || { echo "[judge] $m has no uq log — skipping"; continue; }
  echo "[judge] judging $m $(date)"
  JUDGE_INPUT=$OUT/uq_decoupled_$m.jsonl JUDGE_OUTPUT=$OUT/judge_$m.jsonl JUDGE_WORKERS=8 \
    $PY -u src/judge_e0.py > $OUT/judge_$m.log 2>&1
  echo "JUDGE_DONE $m records=$(wc -l < $OUT/judge_$m.jsonl 2>/dev/null)"
done
echo "ALL_JUDGES_DONE"
