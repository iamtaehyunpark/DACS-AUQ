#!/usr/bin/env python3
"""P(True) read as a VERDICT vs read as a VALUE, with an out-of-sample threshold.

Both readings come from the same probe call. The verdict is the model's own answer —
U > 0.5 means it preferred "No", i.e. this step is wrong — and needs no calibration. The
value is U thresholded at a fitted cut, which does.

The earlier in-sample version fitted the threshold on the same steps it scored, so
`value@opt` was an upper bound. That optimism is not uniform: models whose U distribution
is compressed (Mistral, gemma sit at 0.01-0.15) give a sweep more room to find a lucky
cut, so the weak assessors were flattered most — exactly the cells where the reported gain
was largest. This version fits the threshold on one split and scores on the other.

Splitting is by EPISODE, not by step: steps within a trajectory are dependent, so a random
step split would leak neighbouring steps of the same episode across the boundary and
restore most of the optimism it is meant to remove.

Reported per (dataset, target, assessor, scope):
  verdict      balanced accuracy at the model's own cut (U > 0.5), no fitting
  value_in     balanced accuracy at the in-sample Youden cut  (the optimistic number)
  value_out    balanced accuracy out-of-sample, averaged over both fold directions
  optimism     value_in - value_out
  gain_out     value_out - verdict   <- the honest gain from reading the value

  verdict_vs_value.py [--pivot result/pivot] [--scope AGG-true] [--folds 2] [--out ...csv]
"""
import argparse
import collections
import csv
import json
import os
import statistics

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


def bal_acc(rows, thr):
    """rows = [(u, is_incorrect)]; predict incorrect iff u >= thr."""
    P = sum(1 for _, y in rows if y)
    N = len(rows) - P
    if P == 0 or N == 0:
        return None
    tp = sum(1 for u, y in rows if y and u >= thr)
    tn = sum(1 for u, y in rows if not y and u < thr)
    return 0.5 * (tp / P + tn / N)


def fit_threshold(rows):
    """Youden-J optimal cut on these rows."""
    P = sum(1 for _, y in rows if y)
    N = len(rows) - P
    if P == 0 or N == 0:
        return None
    best = (-2.0, None)
    for thr in sorted({u for u, _ in rows}):
        tp = sum(1 for u, y in rows if y and u >= thr)
        fp = sum(1 for u, y in rows if not y and u >= thr)
        j = tp / P - fp / N
        if j > best[0]:
            best = (j, thr)
    return best[1]


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
    ap.add_argument("--scope", default="AGG-true")
    ap.add_argument("--out", default="reports/tables/verdict_vs_value.csv")
    ap.add_argument("--min-n", type=int, default=200)
    a = ap.parse_args()

    rows_out = []
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
            for asr in assessors_in(os.path.join(xp, dataset, target)):
                sources[asr] = [os.path.join(xp, dataset, target,
                                             "ptrue.%s.%s.jsonl" % (asr, p))
                                for p in ("stages", "response")]

            for assessor, paths in sorted(sources.items()):
                probes = load_ptrue(paths)
                by_ep = collections.defaultdict(list)
                for key, v in probes.items():
                    if key not in labels:
                        continue
                    u = scoped(v, a.scope)
                    if u is None:
                        continue
                    by_ep[key[0]].append((u, labels[key] < 0.5))
                allrows = [r for v in by_ep.values() for r in v]
                if len(allrows) < a.min_n:
                    continue

                verdict = bal_acc(allrows, 0.5000001)   # strictly U > 0.5
                thr_in = fit_threshold(allrows)
                value_in = bal_acc(allrows, thr_in) if thr_in is not None else None

                # two-fold, split by episode, both directions averaged
                eps = sorted(by_ep)
                if len(eps) < 4:
                    continue
                half = len(eps) // 2
                folds = [(eps[:half], eps[half:]), (eps[half:], eps[:half])]
                outs = []
                for fit_eps, score_eps in folds:
                    fit_rows = [r for e in fit_eps for r in by_ep[e]]
                    sc_rows = [r for e in score_eps for r in by_ep[e]]
                    t = fit_threshold(fit_rows)
                    if t is None:
                        continue
                    b = bal_acc(sc_rows, t)
                    if b is not None:
                        outs.append(b)
                if not outs or verdict is None or value_in is None:
                    continue
                value_out = statistics.mean(outs)
                rows_out.append(dict(
                    dataset=dataset, target=target, assessor=assessor,
                    arm="self" if assessor == target else "cross",
                    scope=a.scope, n=len(allrows), n_ep=len(eps),
                    verdict=verdict, value_in=value_in, value_out=value_out,
                    optimism=value_in - value_out, gain_out=value_out - verdict))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    cols = ["dataset", "target", "assessor", "arm", "scope", "n", "n_ep",
            "verdict", "value_in", "value_out", "optimism", "gain_out"]
    with open(a.out, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(cols)
        for r in sorted(rows_out, key=lambda x: (x["dataset"], x["assessor"], x["target"])):
            w.writerow([r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c] for c in cols])
    print("rows: %d -> %s" % (len(rows_out), a.out))

    agg = collections.defaultdict(list)
    for r in rows_out:
        agg[r["assessor"]].append(r)
    print()
    print("scope=%s   verdict = own cut (no fitting) | value_out = fitted OUT-OF-SAMPLE" % a.scope)
    print("%-26s %3s %9s %9s %10s %9s %9s" %
          ("assessor", "n", "verdict", "value_in", "value_out", "optimism", "gain_out"))
    for asr in sorted(agg, key=lambda x: -statistics.mean([r["value_out"] for r in agg[x]])):
        v = agg[asr]
        if len(v) < 3:
            continue
        print("%-26s %3d %9.3f %9.3f %10.3f %9.3f %+9.3f" % (
            asr, len(v),
            statistics.mean([r["verdict"] for r in v]),
            statistics.mean([r["value_in"] for r in v]),
            statistics.mean([r["value_out"] for r in v]),
            statistics.mean([r["optimism"] for r in v]),
            statistics.mean([r["gain_out"] for r in v])))
    allr = rows_out
    print("%-26s %3d %9.3f %9.3f %10.3f %9.3f %+9.3f" % (
        "ALL", len(allr),
        statistics.mean([r["verdict"] for r in allr]),
        statistics.mean([r["value_in"] for r in allr]),
        statistics.mean([r["value_out"] for r in allr]),
        statistics.mean([r["optimism"] for r in allr]),
        statistics.mean([r["gain_out"] for r in allr])))
    print()
    print("cells where the VALUE still beats the VERDICT out-of-sample: %d/%d"
          % (sum(1 for r in allr if r["gain_out"] > 0), len(allr)))


if __name__ == "__main__":
    main()
