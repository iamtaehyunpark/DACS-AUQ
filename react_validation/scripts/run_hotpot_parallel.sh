#!/usr/bin/env bash
# Parallel HotpotQA validation: N_WORKERS processes stride-shard ONE drawn sample across the
# shared vLLM server (concurrent requests -> ~Nx speedup). Draws a RANDOM sample by default
# (fresh seed each run); set REACT_SEED to reproduce a specific sample (233 = upstream's fixed set).
# Usage: run_hotpot_parallel.sh [N_EPISODES=100] [N_WORKERS=4]
# Requires: vLLM server up (serve.sh), the ReAct deps env, outbound internet (live Wikipedia).
# REACT_PY overrides the interpreter (must have openai/gym/bs4/numpy/requests).
set -euo pipefail
cd "$(dirname "$0")/../src"
curl -s http://localhost:8000/v1/models >/dev/null || { echo "no vLLM server at :8000 — run serve.sh first"; exit 1; }

N_EPISODES="${1:-100}"
N_WORKERS="${2:-4}"
PY="${REACT_PY:-python3}"
SEED="${REACT_SEED:-$($PY -c 'import random;print(random.randrange(1,2**31))')}"
echo "seed=$SEED episodes=$N_EPISODES workers=$N_WORKERS interpreter=$PY"

pids=()
for w in $(seq 0 $((N_WORKERS-1))); do
  REACT_NO_STOP=1 REACT_SEED="$SEED" REACT_N_EPISODES="$N_EPISODES" \
  REACT_NUM_WORKERS="$N_WORKERS" REACT_WORKER_ID="$w" \
    "$PY" -u react_hotpotqa.py > "run_hotpot_w${w}.log" 2>&1 &
  pids+=($!)
done
echo "launched workers: ${pids[*]}"
wait
echo "=== per-worker FINAL ==="
grep -h '^FINAL' run_hotpot_w*.log || true
"$PY" - <<'PY'
import glob, re
num = den = ov = er = 0
for f in sorted(glob.glob('run_hotpot_w*.log')):
    tail = open(f).read().split('FINAL')[-1]
    m = re.search(r'EM (\d+)/(\d+)', tail)
    o = re.search(r'overflow-skipped (\d+)', tail)
    e = re.search(r'error-skipped (\d+)', tail)
    if m: num += int(m.group(1)); den += int(m.group(2))
    if o: ov += int(o.group(1))
    if e: er += int(e.group(1))
print('MERGED: EM %d/%d = %.4f | overflow-skipped %d | error-skipped %d'
      % (num, den, (num/den if den else 0.0), ov, er))
PY
