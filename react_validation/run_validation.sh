#!/usr/bin/env bash
# Pure ReAct ALFWorld validation — pure-Python, no jupyter, no clone.
# Original upstream loop (react_alfworld.py) with one backend swap (llm -> served Qwen).
# Requires: vLLM server up (serve.sh), openai, and alfworld + its data (ALFWORLD_DATA set).
set -euo pipefail
cd "$(dirname "$0")"

curl -s http://localhost:8000/v1/models || { echo "no vLLM server at :8000 — run serve.sh first"; exit 1; }

python3 react_alfworld.py 2>&1 | tee run.log
echo "done -> $(pwd)/run.log"
