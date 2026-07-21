#!/usr/bin/env bash
# 10-episode PILOT — first smoke test of the structure on the server.
# Same pure-Python loop as run_validation.sh, capped at 10 episodes via REACT_N_EPISODES.
# Requires: vLLM server up (serve.sh), openai, alfworld + its data (ALFWORLD_DATA set).
set -euo pipefail
cd "$(dirname "$0")"

curl -s http://localhost:8000/v1/models || { echo "no vLLM server at :8000 — run serve.sh first"; exit 1; }

REACT_N_EPISODES=10 python3 react_alfworld.py 2>&1 | tee run_pilot.log
echo "done -> $(pwd)/run_pilot.log"
