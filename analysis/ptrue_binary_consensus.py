#!/usr/bin/env python3
"""Agreement between P(True)'s own binary Yes/No verdict and the judge label.

Everything else in this repo scores P(True) as a continuous ranking (AUROC), which needs a
threshold before it can act. But the probe already emits a DECISION: the model answers Yes
or No, and U > 0.5 means it said "No" (this step is wrong). That verdict needs no
calibration, no labelled data and no tuning — it is available online from the first step.

So this compares like with like: the judge's binary label against P(True)'s binary
verdict, per (dataset x target x assessor x scope).

Columns:
  n            steps joined
  base         fraction judge-incorrect (the target's error rate)
  majority     accuracy of always predicting the majority class — the honest floor
  agree        fraction where the P(True) verdict matches the judge label
  lift_maj     agree - majority. NEGATIVE means the probe is worse than a constant answer.
  bal_acc      balanced accuracy, (TPR+TNR)/2 — the base-rate-free reading
  tpr / tnr    recall on incorrect / on correct steps
  say_inc      fraction of steps the probe called incorrect (its own answer rate)
  tp fp tn fn  raw confusion counts, positive class = incorrect

Raw agreement is NOT comparable across cells: with an 89% error rate, always answering
"incorrect" scores 89%. `majority`, `lift_maj` and `bal_acc` are there so that cannot be
misread.

  ptrue_binary_consensus.py [--pivot result/pivot] [--out ...csv]
"""
import argparse
import collections
import csv
import json
import os

SCOPES = ["SPLIT-thought", "SPLIT-action", "AGG-mean", "AGG-true"]


def load_labels(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        r = json.loads(line)
        votes = [v.get("incorrect") for v in (r.get("votes") or {}).values()]
        votes = [v for v in votes if v is not None]
        if votes:
            out[(r["task_id"], r["step_idx"])] = sum(1 for v in votes if v == 0) / len(votes)
    return out


def load_ptrue(paths):
    out = collections.defaultdict(dict)
    for path in paths:
        if not os.path.exists(path):
            continue
        for line in open(path):
            r = json.loads(line)
            if r.get("probe_kind") != "ptrue":
                continue
            u = r.get("U")
            if u is None:
                continue
            f = r.get("metric_field") or ""
            k = ("T" if f.startswith("U_T") else "A" if f.startswith("U_A")
                 else "R" if f.startswith("U_R") else None)
            if k is None:
                k = {"thought": "T", "action": "A", "response": "R"}.get(r.get("stage"))
            if k:
                out[(r.get("task_id"), r.get("step_idx"))][k] = float(u)
    return out


def scoped(v, scope):
    if scope == "SPLIT-thought":
        return v.get("T")
    if scope == "SPLIT-action":
        return v.get("A")
    if scope == "AGG-true":
        return v.get("R")
    if scope == "AGG-mean":
        t, a = v.get("T"), v.get("A")
        return None if t is None or a is None else (t + a) / 2.0
    return None


def assessors_in(xdir):
    seen = set()
    if not os.path.isdir(xdir):
        return seen
    for f in os.listdir(xdir):
        if not f.startswith("ptrue.") or not f.endswith(".jsonl"):
            continue
        stem = f[len("ptrue."):-len(".jsonl")]
        for suf in (".stages", ".response"):
            if stem.endswith(suf):
                seen.add(stem[:-len(suf)])
                break
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--out", default="reports/tables/ptrue_binary_consensus.csv")
    ap.add_argument("--min-n", type=int, default=100)
    a = ap.parse_args()

    rows = []
    xp = os.path.join(a.pivot, "crossprobe")
    for dataset in sorted(d for d in os.listdir(a.pivot)
                          if os.path.isdir(os.path.join(a.pivot, d)) and d != "crossprobe"):
        for target in sorted(os.listdir(os.path.join(a.pivot, dataset))):
            tdir = os.path.join(a.pivot, dataset, target)
            if not os.path.isdir(tdir):
                continue
            labels = load_labels(os.path.join(tdir, "judge.jsonl"))
            if not labels:
                continue

            sources = {target: [os.path.join(tdir, "probes.jsonl"),
                                os.path.join(tdir, "probes.aggtrue.jsonl")]}
            xdir = os.path.join(xp, dataset, target)
            for asr in assessors_in(xdir):
                sources[asr] = [os.path.join(xdir, "ptrue.%s.%s.jsonl" % (asr, p))
                                for p in ("stages", "response")]

            for assessor, paths in sorted(sources.items()):
                probes = load_ptrue(paths)
                for scope in SCOPES:
                    tp = fp = tn = fn = 0
                    for key, v in probes.items():
                        if key not in labels:
                            continue
                        u = scoped(v, scope)
                        if u is None:
                            continue
                        # the probe's OWN answer: U > 0.5 means it answered "No"
                        said_inc = u > 0.5
                        is_inc = labels[key] < 0.5
                        if is_inc and said_inc:
                            tp += 1
                        elif is_inc and not said_inc:
                            fn += 1
                        elif (not is_inc) and said_inc:
                            fp += 1
                        else:
                            tn += 1
                    n = tp + fp + tn + fn
                    if n < a.min_n:
                        continue
                    P, N = tp + fn, tn + fp
                    if P == 0 or N == 0:
                        continue
                    base = P / n
                    agree = (tp + tn) / n
                    majority = max(base, 1 - base)
                    tpr, tnr = tp / P, tn / N
                    rows.append(dict(
                        dataset=dataset, target=target, assessor=assessor,
                        arm="self" if assessor == target else "cross", scope=scope,
                        n=n, base=base, majority=majority, agree=agree,
                        lift_maj=agree - majority, bal_acc=0.5 * (tpr + tnr),
                        tpr=tpr, tnr=tnr, say_inc=(tp + fp) / n,
                        tp=tp, fp=fp, tn=tn, fn=fn))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    cols = ["dataset", "target", "assessor", "arm", "scope", "n", "base", "majority",
            "agree", "lift_maj", "bal_acc", "tpr", "tnr", "say_inc", "tp", "fp", "tn", "fn"]
    with open(a.out, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(cols)
        for r in sorted(rows, key=lambda x: (x["dataset"], x["target"], x["assessor"], x["scope"])):
            w.writerow([r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c] for c in cols])
    print("rows: %d -> %s" % (len(rows), a.out))

    self_rows = [r for r in rows if r["arm"] == "self" and r["scope"] == "SPLIT-action"]
    if self_rows:
        print()
        print("SELF cells, SPLIT-action (agree vs the majority-class floor):")
        print("%-9s %-26s %6s %8s %8s %9s %8s" %
              ("dataset", "model", "base", "majority", "agree", "lift_maj", "bal_acc"))
        for r in sorted(self_rows, key=lambda x: (x["dataset"], -x["bal_acc"])):
            print("%-9s %-26s %6.3f %8.3f %8.3f %+9.3f %8.3f" % (
                r["dataset"], r["target"], r["base"], r["majority"],
                r["agree"], r["lift_maj"], r["bal_acc"]))


if __name__ == "__main__":
    main()
