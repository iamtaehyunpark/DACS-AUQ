#!/usr/bin/env bash
# Judge server: Llama-3.3-70B-Instruct bf16 via vLLM (yllm env), chat endpoint, TP=2.
# Disjoint model family from the agent by design (kills correlated-plausibility failure).
#   cd /Users/t/sclab && lg run -d -- bash <DACS>/scripts/serve_judge.sh
set -euo pipefail

VLLM=${VLLM:-/opt/anaconda3/envs/yllm/bin/vllm}
export HF_HUB_CACHE=${HF_HUB_CACHE:-/data3/hg_weight/hg_weight}
export HF_HUB_OFFLINE=1

MODEL=${JUDGE_MODEL:-meta-llama/Llama-3.3-70B-Instruct}
PORT=${JUDGE_PORT:-8001}
TP=${JUDGE_TP:-2}
export CUDA_VISIBLE_DEVICES=${JUDGE_GPUS:-2,3}

exec "$VLLM" serve "$MODEL" \
  --served-model-name judge \
  --port "$PORT" \
  --tensor-parallel-size "$TP" \
  --max-model-len 16384 \
  --seed 0
