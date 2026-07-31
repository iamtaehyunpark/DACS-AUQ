#!/usr/bin/env bash
# Run a PAIR of E1 generations sequentially under one already-served agent.
# Args: cfg1 cond1 cfg2 cond2. Resume-safe. Server torn down by run_with_teardown.
set -uo pipefail
DACS=/data5/kje/MULTIAGENT/DACS-AUQ
PY=/opt/anaconda3/envs/Jagent/bin/python
cd "$DACS"
run() {
  local cfg=$1 cond=$2
  echo "===== [E1 RUN START] ${cfg} :: ${cond} @ $(date -Iseconds) ====="
  local t0=$SECONDS
  env ALFWORLD_DATA=/home/user/.cache/alfworld PYTHONPATH="$DACS" \
      "$PY" -m src.run --config "$cfg" --stage generate --condition "$cond"
  local rc=$?
  echo "===== [E1 RUN END]   ${cfg} :: ${cond} rc=${rc} elapsed=$((SECONDS - t0))s @ $(date -Iseconds) ====="
  return $rc
}
run "$1" "$2" && run "$3" "$4"
final=$?
echo "[E1 PAIR COMPLETE final_rc=${final}] @ $(date -Iseconds)"
exit $final
