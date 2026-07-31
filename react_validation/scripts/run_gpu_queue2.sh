#!/bin/bash
# GPU1 queue (rebuild after the Mistral run was killed at 67/140 by a too-broad pkill):
#   1. mistral7b DECOUPLED  — full 140 episodes, from scratch
#   2. phi4mini  ENTANGLED
#   3. gemma4b   ENTANGLED
# Each: serve -> generate -> probes(full roster) -> AGG-true P(True) -> free GPU -> Azure judge.
#
# NOTE ON KILLS: never `pkill -f chat_react.py` while other runs exist — the DeepSeek API run
# uses the same binary. Kill by process group of this script's own children instead.
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
OUT=$RD/result/models4
PORT=8023
GPU=1
cd $RD
source ~/.config/azure_judge.env
export ALFWORLD_DATA=/home/user/.cache/alfworld HF_HUB_OFFLINE=1
unset UQ_API_MODE UQ_MIN_INTERVAL REACT_API_KEY PROBE_API_KEY      # local vLLM, not the API
mkdir -p $OUT

serve_up() {   # name snapshot
  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$2" --served-model-name $1 \
    --tensor-parallel-size 1 --max-model-len 16384 \
    --gpu-memory-utilization 0.30 --max-num-seqs 64 \
    --port $PORT > /tmp/q2_serve_$1.log 2>&1 &
  SRV=$!
  for i in $(seq 1 120); do
    curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && { echo "[$1] SERVER_READY"; return 0; }
    grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/q2_serve_$1.log 2>/dev/null && { echo "[$1] SERVE_FAILED"; return 1; }
    sleep 10
  done
  echo "[$1] SERVE_TIMEOUT"; return 1
}

serve_down() {  # name
  SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
  if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then kill -9 -$SPGID 2>/dev/null; fi
  pkill -9 -f "served-model-name $1" 2>/dev/null
  sleep 8
  echo "=== [$1] GPU freed $(date) ==="
}

probe_set() {  # name uqfile tag
  name=$1; uq=$2; tag=$3
  for spec in "thought,action::ptrue,sep_verbalized,posthoc_numeric,targeted::" "response::ptrue::.aggtrue_ptrue"; do
    stages=$(echo "$spec" | cut -d: -f1); kinds=$(echo "$spec" | cut -d: -f3); sfx=$(echo "$spec" | cut -d: -f5)
    out=$OUT/probes_${tag}${sfx}.jsonl
    rm -f ${out%.jsonl}.w*.jsonl
    pids=()
    for w in 0 1 2 3 4 5 6 7; do
      PROBE_INPUT=$uq PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
        PROBE_NUM_WORKERS=8 PROBE_WORKER_ID=$w \
        PROBE_BASE_URL=http://localhost:$PORT/v1 PROBE_MODEL=$name PROBE_TOKENIZER=$SNAP \
        PROBE_KINDS="$kinds" PROBE_STAGES="$stages" \
        PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
        $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
      pids+=($!)
    done
    wait "${pids[@]}"
    cat ${out%.jsonl}.w*.jsonl > $out
    echo "Q2_PROBES_DONE $tag$sfx records=$(wc -l < $out)"
  done
}

run_one() {   # name snapshot arm script tag
  name=$1; SNAP=$2; arm=$3; script=$4; tag=$5
  echo "=== [$tag] START $(date) ==="
  serve_up $name $SNAP || return 1
  uq=$OUT/uq_${tag}.jsonl
  rm -f $uq
  REACT_BASE_URL=http://localhost:$PORT/v1 REACT_MODEL=$name REACT_TOKENIZER=$SNAP \
  REACT_ENABLE_THINKING=none REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 \
  REACT_MAX_STEPS=50 REACT_RUN_ID=$tag REACT_UQLOG=$uq \
    $PY -u src/$script > $OUT/gen_${tag}.log 2>&1
  echo "Q2_GEN_DONE $tag lines=$(wc -l < $uq 2>/dev/null) | $(grep -h '^FINAL' $OUT/gen_${tag}.log | tail -1)"
  probe_set $name $uq $tag
  serve_down $name
  JUDGE_INPUT=$uq JUDGE_OUTPUT=$OUT/judge_${tag}.jsonl JUDGE_WORKERS=8 \
    $PY -u src/judge_e0.py > $OUT/judge_${tag}.log 2>&1
  echo "Q2_JUDGE_DONE $tag records=$(wc -l < $OUT/judge_${tag}.jsonl 2>/dev/null)"
}

run_one mistral7b $B/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de decoupled chat_react.py            decoupled_mistral7b
run_one phi4mini  $B/models--microsoft--Phi-4-mini-instruct/snapshots/5889daf2bc85b5300eba142a516fe65b0c2ef3f7        entangled chat_react_entangled.py entangled_phi4mini
run_one gemma4b   $B/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767                 entangled chat_react_entangled.py entangled_gemma4b
echo "Q2_ALL_DONE"
