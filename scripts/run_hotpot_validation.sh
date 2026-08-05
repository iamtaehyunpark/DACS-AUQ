#!/usr/bin/env bash
# Pure ReAct HotpotQA validation — pure-Python, no jupyter, no clone.
# Original upstream loop (react_hotpotqa.py) with one backend swap (llm -> served Qwen).
# Requires: vLLM server up (serve.sh), openai, gym, beautifulsoup4, numpy, requests,
# AND outbound internet (the env hits live en.wikipedia.org on every search[]).
set -euo pipefail
cd "$(dirname "$0")/../src"

curl -s http://localhost:8000/v1/models || { echo "no vLLM server at :8000 — run serve.sh first"; exit 1; }

# REACT_NO_STOP=1 -> our modified react (unrestricted generation; harness parses the Action label).
REACT_NO_STOP=1 python3 react_hotpotqa.py 2>&1 | tee run_hotpot.log
echo "done -> $(pwd)/run_hotpot.log"
