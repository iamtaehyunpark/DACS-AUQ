#!/bin/bash
# CROSS-MODEL P(True): evaluate the SMALL models' frozen trajectories with a BIG evaluator.
#
# Question: small models show poor P(True) AUROC. Is that because their trajectories are
# degenerate (generator problem), or because a small model cannot self-assess (evaluator
# problem)? Holding the trajectories fixed and swapping only the evaluator separates the two.
#
# run_probes.py never re-runs the agent — it reconstructs (task, history, commands, thought,
# action) from the frozen uq log and issues fresh probe calls to PROBE_MODEL. So pointing it
# at Qwen while feeding Phi/gemma logs gives exactly the counterfactual we want.
#
# P(True) ONLY: no posthoc_numeric, no sep_verbalized, no targeted.
B=/data3/hg_weight/hg_weight
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
OUT=$RD/result/models4
PORT=8030
GPU=2
QWEN=Qwen/Qwen3.6-35B-A3B
cd $RD
export HF_HOME=/data5/user/hf_cache HF_HUB_OFFLINE=1
unset UQ_API_MODE UQ_RPM UQ_MIN_INTERVAL PROBE_API_KEY     # local vLLM, not the NVIDIA API

echo "[xp] serving $QWEN on GPU$GPU:$PORT"
CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve $QWEN --served-model-name qwen \
  --tensor-parallel-size 1 --max-model-len 16384 \
  --gpu-memory-utilization 0.90 --max-num-seqs 128 \
  --port $PORT > /tmp/xp_serve_qwen.log 2>&1 &
SRV=$!
for i in $(seq 1 120); do
  curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && break
  grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/xp_serve_qwen.log 2>/dev/null && { echo "[xp] SERVE_FAILED"; exit 1; }
  sleep 10
done
curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 || { echo "[xp] SERVE_TIMEOUT"; exit 1; }
echo "[xp] QWEN_READY"

xprobe() {   # tag(uq basename)  stages  suffix
  tag=$1; stages=$2; sfx=$3
  uq=$OUT/uq_${tag}.jsonl
  out=$OUT/probes_${tag}.qwenjudge${sfx}.jsonl
  [ -s "$uq" ] || { echo "[xp] missing $uq — skip"; return; }
  rm -f ${out%.jsonl}.w*.jsonl
  pids=()
  for w in 0 1 2 3 4 5 6 7; do
    PROBE_INPUT=$uq PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
      PROBE_NUM_WORKERS=8 PROBE_WORKER_ID=$w \
      PROBE_BASE_URL=http://localhost:$PORT/v1 PROBE_MODEL=qwen PROBE_TOKENIZER=$QWEN \
      PROBE_KINDS=ptrue PROBE_STAGES="$stages" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat ${out%.jsonl}.w*.jsonl > $out
  echo "XP_DONE ${tag}${sfx} records=$(wc -l < $out)"
}

for tag in decoupled_phi4mini decoupled_gemma4b entangled_phi4mini entangled_gemma4b; do
  xprobe $tag "thought,action" ""
  xprobe $tag "response"       ".aggtrue_ptrue"
done

# free the GPU (server is in its own process group thanks to setsid)
SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then kill -9 -$SPGID 2>/dev/null; fi
pkill -9 -f "served-model-name qwen" 2>/dev/null
sleep 5
echo "XP_GPU_FREED $(date)"
echo "XP_ALL_DONE"
