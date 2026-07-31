#!/usr/bin/env bash
# E1 primary generation driver: 4 sequential runs under one served agent.
# Resume-safe (src.run generate skips completed episodes). Called by
# run_with_teardown.sh AFTER the agent server is ready; server is torn down by
# that wrapper on exit. Generation only — NO judging.
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

run configs/e1_primary.yaml       entangled_auq   && \
run configs/e1_primary.yaml       decoupled       && \
run configs/e1b_contamination.yaml decoupled_conf  && \
run configs/e1b_contamination.yaml decoupled_noconf
final=$?
echo "[E1 ALL RUNS COMPLETE final_rc=${final}] @ $(date -Iseconds)"
exit $final
