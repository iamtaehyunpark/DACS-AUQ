#!/bin/bash
# 1) Unqueue Llama-3.1-8B: wait until the decoupled chain reaches it, then stop that chain
#    (Mistral finishes fully first — gen + probes + AGG-true + teardown all complete before
#    llama8b is reached, so nothing of Mistral's is lost).
# 2) Run the ENTANGLED arm for phi4mini and gemma4b on GPU1: serve -> gen -> probes -> AGG-true.
# 3) Judge both entangled runs on Azure.
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
OUT=$RD/result/models4
PORT=8022
GPU=1
cd $RD
source ~/.config/azure_judge.env
export ALFWORLD_DATA=/home/user/.cache/alfworld HF_HUB_OFFLINE=1
mkdir -p $OUT

echo "[ent] waiting for the decoupled chain to finish mistral7b and reach llama8b..."
until grep -q "\[llama8b\] START" /tmp/seq_4models.out 2>/dev/null; do
  grep -q "SEQ_ALL_DONE" /tmp/seq_4models.out 2>/dev/null && break
  sleep 60
done
echo "[ent] reached llama8b — unqueueing it $(date)"
# stop the decoupled chain driver (single PID, NOT the process group)
for p in $(pgrep -f "bash /data5/kje/MULTIAGENT/DACS-AUQ/react_validation/run_seq_resume.sh"); do kill -9 $p 2>/dev/null; done
pkill -9 -f "served-model-name llama8b" 2>/dev/null      # its server, if it began loading
sleep 10
echo "[ent] llama8b unqueued; GPU free: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader -i $GPU)"

do_entangled() {   # name  snapshot
  name=$1; snap=$2
  echo "=== [ent-$name] START $(date) ==="
  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$snap" --served-model-name $name \
    --tensor-parallel-size 1 --max-model-len 16384 \
    --gpu-memory-utilization 0.30 --max-num-seqs 64 \
    --port $PORT > /tmp/ent_serve_$name.log 2>&1 &
  SRV=$!
  for i in $(seq 1 120); do
    curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && break
    grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/ent_serve_$name.log 2>/dev/null && { echo "[ent-$name] SERVE_FAILED"; return 1; }
    sleep 10
  done
  curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 || { echo "[ent-$name] SERVE_TIMEOUT"; return 1; }
  echo "[ent-$name] SERVER_READY"

  # ---- entangled generation (single joint call/step, one AUQ c-hat) ----
  rm -f $OUT/uq_entangled_$name.jsonl
  REACT_BASE_URL=http://localhost:$PORT/v1 REACT_MODEL=$name REACT_TOKENIZER=$snap \
  REACT_ENABLE_THINKING=none REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 \
  REACT_RUN_ID=entangled_$name REACT_UQLOG=$OUT/uq_entangled_$name.jsonl \
    $PY -u src/chat_react_entangled.py > $OUT/gen_ent_$name.log 2>&1
  echo "ENT_GEN_DONE $name lines=$(wc -l < $OUT/uq_entangled_$name.jsonl 2>/dev/null) | $(grep -h '^FINAL' $OUT/gen_ent_$name.log | tail -1)"

  probe() {   # stages kinds suffix
    out=$OUT/probes_ent_$name$3.jsonl
    rm -f ${out%.jsonl}.w*.jsonl
    pids=()
    for w in 0 1 2 3 4 5 6 7; do
      PROBE_INPUT=$OUT/uq_entangled_$name.jsonl PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
        PROBE_NUM_WORKERS=8 PROBE_WORKER_ID=$w \
        PROBE_BASE_URL=http://localhost:$PORT/v1 PROBE_MODEL=$name PROBE_TOKENIZER=$snap \
        PROBE_KINDS="$2" PROBE_STAGES="$1" \
        PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
        $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
      pids+=($!)
    done
    wait "${pids[@]}"
    cat ${out%.jsonl}.w*.jsonl > $out
    echo "ENT_PROBES_DONE $name$3 records=$(wc -l < $out)"
  }
  probe "thought,action" "ptrue,sep_verbalized,posthoc_numeric,targeted" ""
  probe "response"       "ptrue"                                        ".aggtrue_ptrue"

  SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
  if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then kill -9 -$SPGID 2>/dev/null; fi
  pkill -9 -f "served-model-name $name" 2>/dev/null
  sleep 8
  echo "=== [ent-$name] COMPLETE, GPU freed $(date) ==="

  # ---- judge (Azure, no GPU) ----
  JUDGE_INPUT=$OUT/uq_entangled_$name.jsonl JUDGE_OUTPUT=$OUT/judge_ent_$name.jsonl JUDGE_WORKERS=8 \
    $PY -u src/judge_e0.py > $OUT/judge_ent_$name.log 2>&1
  echo "ENT_JUDGE_DONE $name records=$(wc -l < $OUT/judge_ent_$name.jsonl 2>/dev/null)"
}

do_entangled phi4mini $B/models--microsoft--Phi-4-mini-instruct/snapshots/5889daf2bc85b5300eba142a516fe65b0c2ef3f7
do_entangled gemma4b  $B/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767
echo "ENT_ALL_DONE"
