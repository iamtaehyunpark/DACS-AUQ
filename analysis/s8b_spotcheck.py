#!/usr/bin/env python3
"""S8b — human spot-check package for the disputed label strata.

EXECUTION_HANDOVER.md §9b, A30 §5.5.  Samples 150 steps from the strata where the
constructs disagree, renders annotation sheets BLINDED to every label, and holds the
answer key out in spotcheck/key.json.

Strata (A30 §5.5):
  * A4            — zero-result search: the one Tier-A rule where the environment's
                    verdict and a step-quality verdict can honestly diverge.
  * TierB_x_ens   — Tier-B says incorrect, the ensemble says correct: the contested
                    band the 2.0% ensemble floor was NOT measured on.
  * control       — 20 violation steps (A1/A2/A3), where all constructs agree. These
                    are the calibration controls: an annotator who misses these is not
                    disagreeing about constructs, and their sheet is discounted.

The key is written to a separate file that the annotation sheets do not reference, so
the sheets can be handed over without leaking labels.
"""
import argparse
import csv
import json
import os
import random

N_TOTAL = 150
N_CONTROL = 20
SEED = 13


def strata_of(x):
    """Which disputed stratum a label row belongs to, or None."""
    viol = any(x.get(k) == "1" for k in ("A1", "A2", "A3"))
    if viol:
        return "control"
    if x.get("A4") == "1":
        return "A4"
    if x.get("y_tier_b") == "1" and x.get("y_ensemble") == "0":
        return "TierB_x_ens"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--outdir", default="spotcheck")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rng = random.Random(SEED)

    pools = {"A4": [], "TierB_x_ens": [], "control": []}
    for x in csv.DictReader(open(a.labels)):
        if x.get("in_matrix") != "1":
            continue
        s = strata_of(x)
        if s:
            pools[s].append(x)

    n_disputed = N_TOTAL - N_CONTROL
    per = n_disputed // 2
    picked = []
    for s, n in (("A4", per), ("TierB_x_ens", n_disputed - per),
                 ("control", N_CONTROL)):
        pool = pools[s]
        if not pool:
            continue
        # stratify within by dataset so one environment cannot dominate a stratum
        by_ds = {}
        for x in pool:
            by_ds.setdefault(x["dataset"], []).append(x)
        order = sorted(by_ds)
        take = {d: n // len(order) for d in order}
        for d in order[:n - sum(take.values())]:
            take[d] += 1
        for d in order:
            rng.shuffle(by_ds[d])
            for x in by_ds[d][:take[d]]:
                picked.append((s, x))
    rng.shuffle(picked)

    key, sheet = [], []
    for i, (s, x) in enumerate(picked, 1):
        item = "S%03d" % i
        key.append({"item": item, "stratum": s, "dataset": x["dataset"],
                    "model": x["model"], "task_id": x["task_id"],
                    "step_idx": x["step_idx"], "y_env": x["y_env"],
                    "y_tier_b": x["y_tier_b"], "y_ensemble": x["y_ensemble"],
                    "judge_frac_correct": x.get("judge_frac_correct", ""),
                    "A1": x["A1"], "A2": x["A2"], "A3": x["A3"], "A4": x["A4"],
                    "action_parsed": x.get("action_parsed", "")})
        sheet.append({"item": item, "dataset": x["dataset"],
                      "task_id": x["task_id"], "step_idx": x["step_idx"],
                      "action_parsed": x.get("action_parsed", ""),
                      "annotator_verdict": "", "annotator_note": ""})

    with open(os.path.join(a.outdir, "key.json"), "w") as f:
        json.dump({"seed": SEED, "n": len(key),
                   "strata": {s: sum(1 for k in key if k["stratum"] == s)
                              for s in pools},
                   "items": key}, f, indent=1)
    cols = ["item", "dataset", "task_id", "step_idx", "action_parsed",
            "annotator_verdict", "annotator_note"]
    with open(os.path.join(a.outdir, "sheet.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sheet:
            w.writerow([r[c] for c in cols])

    with open(os.path.join(a.outdir, "INSTRUCTIONS.md"), "w") as f:
        f.write("""# Spot check — instructions

150 agent steps, blinded. For each, answer ONE question:

> Given only the information the agent had **at that moment** — the task, the
> history so far, and the action it proposed — was proposing this action a
> **reasonable decision**?

Write `ok` or `bad` in `annotator_verdict`. Use `annotator_note` for anything
you found ambiguous.

**This is an ex-ante judgement, not hindsight.** An action that was sensible to
try and happened not to work is `ok`. That distinction is the entire point of
the exercise: it is where the label families disagree, and your answer is what
decides which one matches human judgement on the contested band.

You are not being asked whether the step made progress, and you cannot see
whether it did.

Do not open `key.json` before finishing. It holds the labels, including 20
calibration controls whose answer is not in dispute.

Return `sheet.csv` with the verdict column filled. Agreement per construct is
computed on return.
""")
    print("S8b: %d items -> %s/sheet.csv (blinded), key held in %s/key.json"
          % (len(key), a.outdir, a.outdir))
    for s in pools:
        print("   %-14s pool %6d  sampled %3d"
              % (s, len(pools[s]), sum(1 for k in key if k["stratum"] == s)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
