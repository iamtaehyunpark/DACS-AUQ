#!/usr/bin/env bash
# Batch the 3-judge HotpotQA step-labelling pass over one or more finished arms.
#
# Separate from run_hotpot_arm.sh on purpose: the judge is Azure-side and uses no
# GPU, so it runs concurrently with generation instead of blocking a serving
# window. judge_hotpot.py is RESUMABLE — it reads the existing output, collects
# the task_ids already labelled, and appends only what is missing. Re-running a
# partial arm costs nothing and cannot duplicate.
#
# The existing Qwen arm needs exactly this: it stopped at 220/500 trajectories
# (982 of 2235 step-labels) with no DONE line, while the decoupled arm of the
# same size finished. Point this at it and it picks up the remaining 280.
#
# Usage: run_hotpot_judge.sh <arm_dir> [arm_dir ...]
#   arm_dir contains uq_hotpot_entangled.jsonl
set -euo pipefail

# Repo root derived from this script's own location, not hardcoded: the tree has been
# relocated once already (react_validation/* moved up into the parent), which silently
# breaks every absolute path while leaving open file descriptors working — shards keep
# writing but their .done markers cannot be created, so finished work goes unrecorded.
RD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=${HOTPOT_PY:-/opt/anaconda3/envs/Jagent/bin/python}
JUDGE_ENV_FILE=${AZURE_JUDGE_ENV_FILE:-$HOME/.config/azure_judge.env}

[ "$#" -ge 1 ] || { echo "usage: run_hotpot_judge.sh <arm_dir> [arm_dir ...]" >&2; exit 1; }
[ -r "$JUDGE_ENV_FILE" ] || { echo "unreadable judge env: $JUDGE_ENV_FILE" >&2; exit 1; }
# shellcheck disable=SC1090
source "$JUDGE_ENV_FILE"
# gpt-5.6-sol can go direct to OpenAI instead of the Azure deployment; the other two
# judges stay on Azure. Optional — an absent file just means Azure for all three.
OPENAI_JUDGE_ENV_FILE=${OPENAI_JUDGE_ENV_FILE:-$HOME/.config/openai_judge.env}
# shellcheck disable=SC1090
[ -r "$OPENAI_JUDGE_ENV_FILE" ] && source "$OPENAI_JUDGE_ENV_FILE"
[ -n "${AZURE_JUDGE_ENDPOINT:-}" ] && [ -n "${AZURE_JUDGE_KEY:-}" ] || {
  echo "judge env must export AZURE_JUDGE_ENDPOINT and AZURE_JUDGE_KEY" >&2; exit 1; }

cd "$RD/src"

for DIR in "$@"; do
  UQ=$DIR/uq_hotpot_entangled.jsonl
  OUT=$DIR/judge_hotpot_entangled.jsonl
  [ -s "$UQ" ] || { echo "SKIP $DIR — no $UQ" >&2; continue; }

  before=0; [ -e "$OUT" ] && before=$(wc -l < "$OUT")
  echo "=== $DIR (existing labels: $before)"
  # No JUDGE_MAX_TRAJ: that cap is what silently truncates a run.
  unset JUDGE_MAX_TRAJ
  JUDGE_INPUT="$UQ" JUDGE_OUTPUT="$OUT" \
    $PY -u judge_hotpot.py 2>&1 | tee -a "$DIR/run_judge_hotpot_entangled.log"

  after=$(wc -l < "$OUT")
  echo "$DIR: $before -> $after step-labels"
  # Coverage against the source, so a truncated pass is visible instead of assumed.
  $PY - "$UQ" "$OUT" <<'PY'
import json, sys
steps = tasks = 0
seen = set()
for line in open(sys.argv[1]):
    r = json.loads(line)
    if r.get("kind") != "step":
        continue
    steps += 1
    seen.add(r.get("task_id"))
tasks = len(seen)
done = set()
for line in open(sys.argv[2]):
    try:
        done.add(json.loads(line)["task_id"])
    except Exception:
        pass
n = sum(1 for _ in open(sys.argv[2]))
print("  coverage: %d/%d trajectories (%.0f%%), %d/%d step-labels (%.0f%%)"
      % (len(done), tasks, 100.0 * len(done) / max(tasks, 1),
         n, steps, 100.0 * n / max(steps, 1)))
if len(done) < tasks:
    print("  INCOMPLETE — re-run this script to resume")
PY
done
