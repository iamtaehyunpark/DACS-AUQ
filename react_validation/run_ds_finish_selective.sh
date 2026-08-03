#!/bin/bash
# Finish DeepSeek entangled: AGG-true tail (~1255 steps) + the 256 skipped thought/action steps.
#
#  1. SELECTIVE — builds a filtered uq log of ONLY steps that still lack a probe, so a restart
#     never re-spends quota on completed work.
#  2. PREFLIGHT ABORT — if the API is unavailable, exit rather than grind the corpus into
#     "skipped" steps (unprobed is recoverable; skipped looks like completed-but-empty).
#  Exit 1 on abort so an outer gate can retry later.
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/deepseek
NW=4
cd $RD
source ~/.config/nvidia_api.env
export UQ_API_MODE=1 UQ_RPM=12 UQ_RATE_FILE=/tmp/uq_rate_slot.lock
export UQ_MAX_RETRY=8 UQ_BACKOFF_BASE=4 UQ_BACKOFF_CAP=60
export PROBE_API_KEY=$NVIDIA_API_KEY

if ! $PY - <<'PYEOF'
import os, sys
from openai import OpenAI
c = OpenAI(base_url="https://integrate.api.nvidia.com/v1",
           api_key=os.environ["NVIDIA_API_KEY"], max_retries=0)
try:
    c.chat.completions.create(model=os.environ["NVIDIA_MODEL"],
                              messages=[{"role": "user", "content": "hi"}], max_tokens=3)
    sys.exit(0)
except Exception as e:
    print("  preflight failed: %s" % repr(e)[:90]); sys.exit(1)
PYEOF
then
  echo "DSF_ABORT API unavailable — not starting"
  exit 1
fi
echo "DSF_QUOTA_OK $(date)"

$PY - <<'PYEOF'
import json, os
OUT = "/data5/kje/MULTIAGENT/DACS-AUQ/react_validation/result/deepseek"
uq = os.path.join(OUT, "uq_entangled_ds.jsonl")

def covered(path, fields):
    s = set()
    if not os.path.exists(path):
        return s
    for l in open(path):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("metric_field") in fields and r.get("U") is not None:
            s.add((r["task_id"], r["step_idx"]))
    return s

have_agg = covered(os.path.join(OUT, "probes_entangled_ds.aggtrue_ptrue.jsonl"), {"U_R_ptrue"})
have_ta = covered(os.path.join(OUT, "probes_entangled_ds.jsonl"), {"U_T_ptrue", "U_A_ptrue"})

allsteps, recs = set(), []
for l in open(uq):
    try:
        r = json.loads(l)
    except Exception:
        continue
    if r.get("kind") in ("call", "step"):
        recs.append((r.get("task_id"), r.get("step_idx"), l))
        allsteps.add((r.get("task_id"), r.get("step_idx")))

for tag, have in (("agg", have_agg), ("ta", have_ta)):
    miss = allsteps - have
    p = os.path.join(OUT, "uq_missing_%s.jsonl" % tag)
    with open(p, "w") as f:
        for t, s, l in recs:
            if (t, s) in miss:
                f.write(l)
    print("  %-4s covered=%d missing=%d" % (tag, len(have), len(miss)))
PYEOF

probe() {   # inputfile outbase stages label
  inp=$1; out=$2; stages=$3; label=$4
  nsteps=$(grep -c '"kind": "step"' $inp 2>/dev/null || echo 0)
  if [ "${nsteps:-0}" -eq 0 ]; then echo "DSF_SKIP $label (nothing missing)"; return; fi
  echo "DSF_START $label steps=$nsteps"
  rm -f ${out%.jsonl}.w*.jsonl
  pids=()
  for w in $(seq 0 $((NW-1))); do
    PROBE_INPUT=$inp PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
      PROBE_NUM_WORKERS=$NW PROBE_WORKER_ID=$w \
      PROBE_BASE_URL=https://integrate.api.nvidia.com/v1 PROBE_MODEL=$NVIDIA_MODEL \
      PROBE_TOKENIZER=none PROBE_KINDS=ptrue PROBE_STAGES="$stages" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  n=$(cat ${out%.jsonl}.w*.jsonl 2>/dev/null | wc -l)
  sk=$(cat ${out%.jsonl}_w*.log 2>/dev/null | grep -ac "^ERROR step")
  echo "DSF_DONE $label new_records=$n skipped=$sk"
}

probe $OUT/uq_missing_agg.jsonl $OUT/probes_bf_agg.jsonl "response"       "aggtrue-backfill"
probe $OUT/uq_missing_ta.jsonl  $OUT/probes_bf_ta.jsonl  "thought,action" "thoughtaction-backfill"

cat $OUT/probes_bf_agg.w*.jsonl >> $OUT/probes_entangled_ds.aggtrue_ptrue.jsonl 2>/dev/null
cat $OUT/probes_bf_ta.w*.jsonl  >> $OUT/probes_entangled_ds.jsonl 2>/dev/null
echo "DSF_MERGED aggtrue=$(wc -l < $OUT/probes_entangled_ds.aggtrue_ptrue.jsonl) ta=$(wc -l < $OUT/probes_entangled_ds.jsonl)"
echo "DSF_ALL_DONE"
