#!/usr/bin/env bash
# Agent server: Qwen3.6-35B-A3B via vLLM (yllm env), raw-completions client.
# Shared box — run `nvidia-smi` first and pick free GPUs. Launch (detached) from the lg mount:
#   cd /Users/t/sclab && lg run -d -- bash <DACS>/scripts/serve_agent.sh
set -euo pipefail

VLLM=${VLLM:-/opt/anaconda3/envs/yllm/bin/vllm}
export HF_HOME=${HF_HOME:-/data5/user/hf_cache}
export HF_HUB_OFFLINE=1                     # weights are cached; never hit the network

MODEL=${AGENT_MODEL:-Qwen/Qwen3.6-35B-A3B}
PORT=${AGENT_PORT:-8000}
TP=${AGENT_TP:-2}
export CUDA_VISIBLE_DEVICES=${AGENT_GPUS:-0,1}

exec "$VLLM" serve "$MODEL" \
  --served-model-name agent \
  --port "$PORT" \
  --tensor-parallel-size "$TP" \
  --max-model-len 65536 \
  --max-logprobs 20 \
  --seed 0
