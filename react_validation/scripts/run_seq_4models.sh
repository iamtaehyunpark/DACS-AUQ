#!/bin/bash
# Sequential GPU chain: one model at a time on GPU0 at FULL memory bandwidth.
# Order = smallest -> largest.  Per model: serve -> generate -> probes -> AGG-true -> free GPU.
# The judge is NOT here (no GPU needed) — run_judge_seq.sh handles it in parallel.
#
# Why sequential: ALFWorld decodes one sequence at a time, so it is HBM-bandwidth-bound.
# Co-resident models split that bandwidth, making each ~N x slower for no aggregate gain.
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
OUT=$RD/result/models4
PORT=8020
cd $RD
export ALFWORLD_DATA=/home/user/.cache/alfworld HF_HUB_OFFLINE=1
mkdir -p $OUT

do_model() {   # name  snapshot
  name=$1; snap=$2
  echo "=== [$name] START $(date) ==="

  # ---- serve (full GPU) ----
  CUDA_VISIBLE_DEVICES=0 nohup $V serve "$snap" --served-model-name $name \
    --tensor-parallel-size 1 --max-model-len 16384 \
    --gpu-memory-utilization 0.85 --max-num-seqs 64 \
    --port $PORT > /tmp/seq_serve_$name.log 2>&1 &
  SRV=$!
  for i in $(seq 1 120); do
    curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && break
    grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/seq_serve_$name.log 2>/dev/null && { echo "[$name] SERVE_FAILED"; return 1; }
    sleep 10
  done
  curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 || { echo "[$name] SERVE_TIMEOUT"; return 1; }
  echo "[$name] SERVER_READY"

  # ---- generation (140 eps, cap 50, identical prompts/sampling) ----
  rm -f $OUT/uq_decoupled_$name.jsonl
  REACT_BASE_URL=http://localhost:$PORT/v1 REACT_MODEL=$name REACT_TOKENIZER=$snap \
  REACT_ENABLE_THINKING=none REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 \
  REACT_MAX_STEPS=50 \
  REACT_RUN_ID=decoupled_$name REACT_UQLOG=$OUT/uq_decoupled_$name.jsonl \
    $PY -u src/chat_react.py > $OUT/gen_$name.log 2>&1
  echo "GEN_DONE $name lines=$(wc -l < $OUT/uq_decoupled_$name.jsonl 2>/dev/null) | $(grep -h '^FINAL' $OUT/gen_$name.log | tail -1)"

  # ---- probes: per-stage roster, then AGG-true whole-response P(True) ----
  probe() {   # stages kinds suffix
    out=$OUT/probes_$name$3.jsonl
    rm -f ${out%.jsonl}.w*.jsonl
    pids=()
    for w in 0 1 2 3 4 5 6 7; do
      PROBE_INPUT=$OUT/uq_decoupled_$name.jsonl PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
        PROBE_NUM_WORKERS=8 PROBE_WORKER_ID=$w \
        PROBE_BASE_URL=http://localhost:$PORT/v1 PROBE_MODEL=$name PROBE_TOKENIZER=$snap \
        PROBE_KINDS="$2" PROBE_STAGES="$1" \
        PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
        $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
      pids+=($!)
    done
    wait "${pids[@]}"
    cat ${out%.jsonl}.w*.jsonl > $out
    echo "PROBES_DONE $name$3 records=$(wc -l < $out)"
  }
  probe "thought,action" "ptrue,sep_verbalized,posthoc_numeric,targeted" ""
  probe "response"       "ptrue"                                        ".aggtrue_ptrue"

  # ---- free the GPU before the next model ----
  PGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
  [ -n "$PGID" ] && kill -9 -$PGID 2>/dev/null
  pkill -9 -f "served-model-name $name" 2>/dev/null
  sleep 8
  echo "=== [$name] COMPLETE, GPU freed $(date) ==="
}

do_model phi4mini  $B/models--microsoft--Phi-4-mini-instruct/snapshots/5889daf2bc85b5300eba142a516fe65b0c2ef3f7
do_model gemma4b   $B/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767
do_model mistral7b $B/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de
do_model llama8b   $B/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659

echo "=== FINAL SUCCESS RATES ==="
for m in phi4mini gemma4b mistral7b llama8b; do
  echo "  $m: $(grep -h '^FINAL' $OUT/gen_$m.log 2>/dev/null | tail -1)"
done
echo "SEQ_ALL_DONE"
