#!/bin/bash
# Mistral-7B ENTANGLED arm (only decoupled was run). Completes the 2x2 arch x model grid
# for the small/mid models. Same config as the phi4mini/gemma4b entangled runs so the
# cross-model comparison stays clean: Seen split, 140 eps, cap 50, identical prompts+sampling.
#   serve -> generate -> probes (full roster) -> AGG-true P(True) -> free GPU -> Azure judge
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
OUT=$RD/result/models4
SNAP=$B/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de
PORT=8031
GPU=2
TAG=entangled_mistral7b
cd $RD
source ~/.config/azure_judge.env
export HF_HUB_OFFLINE=1 ALFWORLD_DATA=/home/user/.cache/alfworld
# local vLLM — make sure no hosted-API settings leak in from other runs
unset UQ_API_MODE UQ_RPM UQ_MIN_INTERVAL UQ_RATE_FILE REACT_API_KEY PROBE_API_KEY
mkdir -p $OUT

echo "=== [$TAG] START $(date) ==="
CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name mistral7b \
  --tensor-parallel-size 1 --max-model-len 16384 \
  --gpu-memory-utilization 0.30 --max-num-seqs 64 \
  --port $PORT > /tmp/me_serve.log 2>&1 &
SRV=$!
for i in $(seq 1 120); do
  curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && break
  grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/me_serve.log 2>/dev/null && { echo "SERVE_FAILED"; exit 1; }
  sleep 10
done
curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 || { echo "SERVE_TIMEOUT"; exit 1; }
echo "[$TAG] SERVER_READY"

uq=$OUT/uq_${TAG}.jsonl
rm -f $uq
REACT_BASE_URL=http://localhost:$PORT/v1 REACT_MODEL=mistral7b REACT_TOKENIZER=$SNAP \
REACT_ENABLE_THINKING=none REACT_SPLIT=eval_in_distribution REACT_N_EPISODES=140 \
REACT_MAX_STEPS=50 REACT_RUN_ID=$TAG REACT_UQLOG=$uq \
  $PY -u src/chat_react_entangled.py > $OUT/gen_${TAG}.log 2>&1
neps=$(grep -c '"kind": "episode"' $uq 2>/dev/null || echo 0)
echo "ME_GEN_DONE $TAG lines=$(wc -l < $uq) episodes=$neps/140 | $(grep -h '^FINAL' $OUT/gen_${TAG}.log | tail -1)"
[ "$neps" -lt 140 ] && echo "ME_GEN_INCOMPLETE missing=$((140-neps))"

probe() {   # stages kinds suffix
  out=$OUT/probes_${TAG}$3.jsonl
  rm -f ${out%.jsonl}.w*.jsonl
  pids=()
  for w in 0 1 2 3 4 5 6 7; do
    PROBE_INPUT=$uq PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
      PROBE_NUM_WORKERS=8 PROBE_WORKER_ID=$w \
      PROBE_BASE_URL=http://localhost:$PORT/v1 PROBE_MODEL=mistral7b PROBE_TOKENIZER=$SNAP \
      PROBE_KINDS="$2" PROBE_STAGES="$1" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat ${out%.jsonl}.w*.jsonl > $out
  sk=$(cat ${out%.jsonl}_w*.log 2>/dev/null | grep -c "^ERROR step")
  echo "ME_PROBES_DONE $TAG$3 records=$(wc -l < $out) skipped_steps=$sk"
}
probe "thought,action" "ptrue,sep_verbalized,posthoc_numeric,targeted" ""
probe "response"       "ptrue"                                        ".aggtrue_ptrue"

# free the GPU (server has its own process group via setsid)
SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then kill -9 -$SPGID 2>/dev/null; fi
pkill -9 -f "served-model-name mistral7b" 2>/dev/null
sleep 8
echo "ME_GPU_FREED $(date)"

JUDGE_INPUT=$uq JUDGE_OUTPUT=$OUT/judge_${TAG}.jsonl JUDGE_WORKERS=8 \
  $PY -u src/judge_e0.py > $OUT/judge_${TAG}.log 2>&1
echo "ME_JUDGE_DONE $TAG records=$(wc -l < $OUT/judge_${TAG}.jsonl 2>/dev/null)"
echo "ME_ALL_DONE"
