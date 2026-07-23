#!/usr/bin/env bash
# Full HotpotQA acquisition pipeline: 2 arms x (UQ calls, post-hoc probes, trajectory judge).
# Usage: run_hotpot_acquisition.sh [OUTPUT_DIR=runs/hotpot_acquisition] [N_EPISODES=10]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_ARG="${1:-runs/hotpot_acquisition}"
N_EPISODES="${2:-10}"
PY="${REACT_PY:-python3}"
SEED="${REACT_SEED:-233}"
JUDGE_ENV_FILE="${AZURE_JUDGE_ENV_FILE:-/home/user/.config/azure_judge.env}"

if [[ ! -r "$JUDGE_ENV_FILE" ]]; then
  echo "Azure judge env file is not readable: $JUDGE_ENV_FILE" >&2
  echo "set AZURE_JUDGE_ENV_FILE if the server stores it elsewhere" >&2
  exit 1
fi
# Server-owned chmod-600 file; values are inherited by both judge_hotpot.py processes.
# shellcheck disable=SC1090
source "$JUDGE_ENV_FILE"

case "$OUT_ARG" in
  /*) OUT_DIR="$OUT_ARG" ;;
  *) OUT_DIR="$REPO_ROOT/$OUT_ARG" ;;
esac

mkdir -p "$OUT_DIR"
DEC_UQ="$OUT_DIR/uq_hotpot_decoupled.jsonl"
ENT_UQ="$OUT_DIR/uq_hotpot_entangled.jsonl"
DEC_PROBES="$OUT_DIR/probes_hotpot_decoupled.jsonl"
ENT_PROBES="$OUT_DIR/probes_hotpot_entangled.jsonl"
DEC_JUDGE="$OUT_DIR/judge_hotpot_decoupled.jsonl"
ENT_JUDGE="$OUT_DIR/judge_hotpot_entangled.jsonl"

for target in "$DEC_UQ" "$ENT_UQ" "$DEC_PROBES" "$ENT_PROBES" "$DEC_JUDGE" "$ENT_JUDGE"; do
  if [[ -e "$target" ]]; then
    echo "refusing to append to existing acquisition artifact: $target" >&2
    echo "choose a fresh OUTPUT_DIR" >&2
    exit 1
  fi
done

curl -sS http://localhost:8000/v1/models >/dev/null || {
  echo "no model server at :8000 — run scripts/serve.sh first" >&2
  exit 1
}
if [[ -z "${AZURE_JUDGE_ENDPOINT:-}" || -z "${AZURE_JUDGE_KEY:-}" ]]; then
  echo "Azure judge env file must export AZURE_JUDGE_ENDPOINT and AZURE_JUDGE_KEY" >&2
  exit 1
fi

cd "$REPO_ROOT/src"
echo "phase 1/3: HotpotQA agent acquisition (same sample seed=$SEED, n=$N_EPISODES)"
REACT_N_EPISODES="$N_EPISODES" REACT_SEED="$SEED" \
REACT_RUN_ID="hotpot_decoupled" REACT_UQLOG="$DEC_UQ" \
  "$PY" -u chat_react_hotpot.py 2>&1 | tee "$OUT_DIR/run_hotpot_decoupled.log"
REACT_N_EPISODES="$N_EPISODES" REACT_SEED="$SEED" \
REACT_RUN_ID="hotpot_entangled" REACT_UQLOG="$ENT_UQ" \
  "$PY" -u chat_react_hotpot_entangled.py 2>&1 | tee "$OUT_DIR/run_hotpot_entangled.log"
"$PY" audit_hotpot.py "$DEC_UQ" decoupled | tee "$OUT_DIR/audit_hotpot_decoupled.log"
"$PY" audit_hotpot.py "$ENT_UQ" entangled | tee "$OUT_DIR/audit_hotpot_entangled.log"

echo "phase 2/3: frozen-trajectory post-hoc probes"
# Decoupled keeps the full ALFWorld probe roster. Entangled excludes the targeted q_t
# probe by design, matching the ALFWorld arm contract. Both add only whole-response P(True).
PROBE_INPUT="$DEC_UQ" PROBE_OUTPUT="$DEC_PROBES" \
PROBE_KINDS="ptrue,sep_verbalized,posthoc_numeric,targeted" \
PROBE_STAGES="thought,action" PROBE_RESPONSE_KINDS="ptrue" \
  "$PY" -u run_probes.py 2>&1 | tee "$OUT_DIR/run_probes_hotpot_decoupled.log"
PROBE_INPUT="$ENT_UQ" PROBE_OUTPUT="$ENT_PROBES" \
PROBE_KINDS="ptrue,sep_verbalized,posthoc_numeric" \
PROBE_STAGES="thought,action" PROBE_RESPONSE_KINDS="ptrue" \
  "$PY" -u run_probes.py 2>&1 | tee "$OUT_DIR/run_probes_hotpot_entangled.log"

echo "phase 3/3: whole-trajectory judge, separately per arm"
JUDGE_INPUT="$DEC_UQ" JUDGE_OUTPUT="$DEC_JUDGE" \
  "$PY" -u judge_hotpot.py 2>&1 | tee "$OUT_DIR/run_judge_hotpot_decoupled.log"
JUDGE_INPUT="$ENT_UQ" JUDGE_OUTPUT="$ENT_JUDGE" \
  "$PY" -u judge_hotpot.py 2>&1 | tee "$OUT_DIR/run_judge_hotpot_entangled.log"
"$PY" audit_hotpot_outputs.py "$DEC_UQ" "$DEC_PROBES" "$DEC_JUDGE" decoupled \
  | tee "$OUT_DIR/audit_hotpot_outputs_decoupled.log"
"$PY" audit_hotpot_outputs.py "$ENT_UQ" "$ENT_PROBES" "$ENT_JUDGE" entangled \
  | tee "$OUT_DIR/audit_hotpot_outputs_entangled.log"

echo "DONE: six HotpotQA acquisition artifacts -> $OUT_DIR"
printf '%s\n' "$DEC_UQ" "$DEC_PROBES" "$DEC_JUDGE" "$ENT_UQ" "$ENT_PROBES" "$ENT_JUDGE"
