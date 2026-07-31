#!/bin/bash
# Resumed sequential chain on GPU1 (phi4mini already complete: gen+probes+aggtrue+judge).
# Order: gemma4b -> mistral7b -> llama8b.  Per model: serve -> generate -> probes -> AGG-true -> free GPU.
#
# FIX 1 (setsid): a background job in a non-interactive shell shares the PARENT's process group,
#   so the previous "kill -9 -$PGID" teardown killed the driver script itself. setsid gives the
#   server its own process group, making the group-kill safe.
# FIX 2 (right-sized KV): --gpu-memory-utilization 0.30 (~24GB) instead of 0.85. vLLM fills all
#   reserved memory with KV cache; at 0.85 it grabbed 58.7GB of KV (480k tokens) when our
#   batch-1 / 16k-context workload can use at most 16k. Same speed, leaves the card usable.
#
# Appends to /tmp/seq_4models.out so the already-running judge chain picks up each GEN_DONE.
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
OUT=$RD/result/models4
PORT=8021
GPU=1
cd $RD
export ALFWORLD_DATA=/home/user/.cache/alfworld HF_HUB_OFFLINE=1
mkdir -p $OUT

do_model() {   # name  snapshot
  name=$1; snap=$2
  echo "=== [$name] START $(date) ==="

  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$snap" --served-model-name $name \
    --tensor-parallel-size 1 --max-model-len 16384 \
    --gpu-memory-utilization 0.30 --max-num-seqs 64 \
    --port $PORT > /tmp/seq_serve_$name.log 2>&1 &
  SRV=$!
  for i in $(seq 1 120); do
    curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && break
    grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/seq_serve_$name.log 2>/dev/null && { echo "[$name] SERVE_FAILED"; return 1; }
    sleep 10
  done
  curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 || { echo "[$name] SERVE_TIMEOUT"; return 1; }
  echo "[$name] SERVER_READY"

  rm -f $OUT/uq_decoupled_$name.jsonl
  REACT_BASE_URL=http://localhost:$PORT/v1 REACT_MODEL=$name REACT_TOKENIZER=$snap \
  REACT_ENABLE_THINKING=none REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 \
  REACT_MAX_STEPS=50 \
  REACT_RUN_ID=decoupled_$name REACT_UQLOG=$OUT/uq_decoupled_$name.jsonl \
    $PY -u src/chat_react.py > $OUT/gen_$name.log 2>&1
  echo "GEN_DONE $name lines=$(wc -l < $OUT/uq_decoupled_$name.jsonl 2>/dev/null) | $(grep -h '^FINAL' $OUT/gen_$name.log | tail -1)"

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

  # teardown: server is in its OWN process group thanks to setsid, so this cannot kill us
  SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
  if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then
    kill -9 -$SPGID 2>/dev/null
  fi
  pkill -9 -f "served-model-name $name" 2>/dev/null
  sleep 8
  echo "=== [$name] COMPLETE, GPU freed $(date) ==="
}

do_model gemma4b   $B/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767
do_model mistral7b $B/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de
do_model llama8b   $B/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659

echo "=== FINAL SUCCESS RATES ==="
for m in phi4mini gemma4b mistral7b llama8b; do
  echo "  $m: $(grep -h '^FINAL' $OUT/gen_$m.log 2>/dev/null | tail -1)"
done
echo "SEQ_ALL_DONE"
