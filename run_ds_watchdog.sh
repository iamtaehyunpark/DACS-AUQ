#!/bin/bash
# Watchdog that chips away at the DeepSeek entangled AGG-true tail across many quota windows.
#
# Why a watchdog and not just a retry loop: the NVIDIA allowance replenishes in small bursts
# (~hundreds of calls), so a run starts fine and then dies mid-corpus. The preflight only
# checks at START, so once quota dies the workers keep going and turn UNPROBED steps into
# SKIPPED ones — worse than never running, because unprobed is recoverable.
#
# Each cycle:
#   1. run the selective finish (it re-derives what's missing, so nothing is ever redone)
#   2. watch records vs skips; if records stall while skips climb -> quota died -> kill workers
#   3. merge whatever was banked, so progress accumulates across cycles
#   4. stop entirely once nothing is missing
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
OUT=$RD/result/deepseek4flash
CYCLES=${DS_CYCLES:-48}          # hourly cycles (~2 days)
STALL_CHECKS=3                   # consecutive 60s checks with no new records => stalled

merge_and_count() {
  cat $OUT/probes_bf_agg.w*.jsonl >> $OUT/probes_entangled_ds.aggtrue_ptrue.jsonl 2>/dev/null
  rm -f $OUT/probes_bf_agg.w*.jsonl
  wc -l < $OUT/probes_entangled_ds.aggtrue_ptrue.jsonl 2>/dev/null || echo 0
}

for cyc in $(seq 1 $CYCLES); do
  # how much is left?
  missing=$($PY - <<'PYEOF'
import json, os
OUT = "/data5/kje/MULTIAGENT/DACS-AUQ/react_validation/result/deepseek4flash"
have = set()
p = os.path.join(OUT, "probes_entangled_ds.aggtrue_ptrue.jsonl")
if os.path.exists(p):
    for l in open(p):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("metric_field") == "U_R_ptrue" and r.get("U") is not None:
            have.add((r["task_id"], r["step_idx"]))
allst = set()
for l in open(os.path.join(OUT, "uq_entangled_ds.jsonl")):
    try:
        r = json.loads(l)
    except Exception:
        continue
    if r.get("kind") == "step":
        allst.add((r.get("task_id"), r.get("step_idx")))
print(len(allst - have))
PYEOF
)
  echo "WD_CYCLE $cyc missing=$missing $(date +%H:%M)"
  if [ "${missing:-1}" -eq 0 ]; then echo "WD_COMPLETE all AGG-true steps covered"; break; fi

  bash $RD/run_ds_finish_selective.sh > /tmp/ds_finish.out 2>&1 &
  RUN=$!

  # ---- in-run stall detection ----
  prev=-1; stall=0
  while kill -0 $RUN 2>/dev/null; do
    sleep 60
    now=$(cat $OUT/probes_bf_agg.w*.jsonl 2>/dev/null | wc -l)
    if [ "$now" -eq "$prev" ] && [ "$now" -ge 0 ]; then
      stall=$((stall+1))
    else
      stall=0
    fi
    prev=$now
    if [ "$stall" -ge "$STALL_CHECKS" ]; then
      if pgrep -f run_probes.py >/dev/null 2>&1; then
        echo "WD_STALL cycle $cyc — quota died mid-run, killing workers to protect unprobed steps"
        for p in $(pgrep -f run_probes.py); do kill -9 $p 2>/dev/null; done
      fi
      kill -9 $RUN 2>/dev/null
      break
    fi
  done
  wait $RUN 2>/dev/null

  total=$(merge_and_count)
  echo "WD_BANKED cycle $cyc aggtrue_total=$total"
  sleep 3600
done
echo "WD_DONE"
