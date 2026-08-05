#!/usr/bin/env bash
# Standard vLLM OpenAI-compatible server. Substitute your Qwen checkpoint.
# Served name is fixed to "qwen" so run_validation.sh's llm() shim matches.
set -euo pipefail

MODEL="${1:-Qwen/Qwen2.5-7B-Instruct}"

vllm serve "$MODEL" --served-model-name qwen
# -> http://localhost:8000 ; check: curl -s http://localhost:8000/v1/models
