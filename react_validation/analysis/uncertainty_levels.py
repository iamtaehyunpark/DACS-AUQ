#!/usr/bin/env python3
"""Mean uncertainty by correct/incorrect step group, for every (assessor x target) cell.

AUROC says whether a judge RANKS steps correctly. It says nothing about WHERE its scores
sit, and a deployed instrument needs a threshold, not a ranking. This asks the separate
question: does a given judge put its scores in the same place regardless of what it is
reading?

If an assessor's mean-U level and its optimal cut point are stable across targets, the
threshold is a property of the judge and can be characterised once — the same
amortisation claim as recipe invariance, but for calibration. If they move per target,
the threshold has to be re-fit per deployment even when the recipe transfers.

Per cell it reports:
  mu_inc / mu_cor   mean U on judge-incorrect and judge-correct steps
  gap               mu_inc - mu_cor  (discrimination in RAW score units, not rank)
  level             pooled mean U    (where the judge sits overall)
  thr               Youden-J optimal threshold
  bal_acc           balanced accuracy at that threshold

Steps are split hard at judge_correct_frac >= 0.5; ties in the 3-judge ensemble
(frac == 0.5 is impossible with 3 valid votes, but 2 valid votes can split) fall to the
incorrect side, matching the conservative reading used elsewhere.

  uncertainty_levels.py [--pivot result/pivot] [--scope SPLIT-action] [--out ...md]
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


def youden(pairs):
    """(threshold, balanced accuracy) maximising TPR-FPR. pairs = [(u, is_incorrect)]."""
    if not pairs:
        return None, None
    P = sum(1 for _, y in pairs if y)
    N = len(pairs) - P
    if P == 0 or N == 0:
        return None, None
    best = (-1.0, None)
    for thr in sorted({u for u, _ in pairs}):
        tp = sum(1 for u, y in pairs if y and u >= thr)
        fp = sum(1 for u, y in pairs if not y and u >= thr)
        j = tp / P - fp / N
        if j > best[0]:
            best = (j, thr)
    thr = best[1]
    tp = sum(1 for u, y in pairs if y and u >= thr)
    tn = sum(1 for u, y in pairs if not y and u < thr)
    return thr, 0.5 * (tp / P + tn / N)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--scope", default="SPLIT-action",
                    help="scope to report; the level question is per-scope")
    ap.add_argument("--out", default="reports/tables/uncertainty_levels.md")
    ap.add_argument("--csv", default="reports/tables/uncertainty_levels.csv")
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
            if os.path.isdir(xdir):
                seen = set()
                for f in os.listdir(xdir):
                    if not f.startswith("ptrue.") or not f.endswith(".jsonl"):
                        continue
                    stem = f[len("ptrue."):-len(".jsonl")]
                    for suf in (".stages", ".response"):
                        if stem.endswith(suf):
                            stem = stem[:-len(suf)]
                            break
                    else:
                        continue
                    seen.add(stem)
                for asr in seen:
                    sources[asr] = [os.path.join(xdir, "ptrue.%s.%s.jsonl" % (asr, p))
                                    for p in ("stages", "response")]

            for assessor, paths in sources.items():
                probes = load_ptrue(paths)
                inc, cor, pairs = [], [], []
                for key, v in probes.items():
                    if key not in labels:
                        continue
                    u = scoped(v, a.scope)
                    if u is None:
                        continue
                    is_inc = labels[key] < 0.5
                    (inc if is_inc else cor).append(u)
                    pairs.append((u, is_inc))
                if len(inc) < 20 or len(cor) < 20:
                    continue
                thr, bacc = youden(pairs)
                rows.append(dict(
                    dataset=dataset, target=target, assessor=assessor,
                    arm="self" if assessor == target else "cross",
                    n_inc=len(inc), n_cor=len(cor),
                    mu_inc=statistics.mean(inc), mu_cor=statistics.mean(cor),
                    gap=statistics.mean(inc) - statistics.mean(cor),
                    level=statistics.mean(inc + cor),
                    sd=statistics.pstdev(inc + cor),
                    thr=thr, bal_acc=bacc))

    os.makedirs(os.path.dirname(a.csv), exist_ok=True)
    with open(a.csv, "w", newline="") as fo:
        w = csv.writer(fo)
        cols = ["dataset", "target", "assessor", "arm", "n_inc", "n_cor",
                "mu_inc", "mu_cor", "gap", "level", "sd", "thr", "bal_acc"]
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] if isinstance(r[c], (str, int)) else
                        ("" if r[c] is None else "%.4f" % r[c]) for c in cols])

    lines = ["# Uncertainty level by correct/incorrect group — scope %s" % a.scope, "",
             "AUROC measures ranking; this measures WHERE the scores sit. A judge whose",
             "level and optimal cut point hold across targets can have its threshold",
             "characterised once. One whose level moves must be re-calibrated per target",
             "even if its recipe transfers.", "",
             "`gap` = mean U on judge-incorrect minus mean U on judge-correct steps.",
             "Labels are the 3-judge ensemble, so provisional until gate 1.", ""]

    for dataset in sorted({r["dataset"] for r in rows}):
        lines += ["## %s" % dataset, "",
                  "| assessor | target | arm | mu_inc | mu_cor | gap | level | thr | bal_acc | n |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in sorted([x for x in rows if x["dataset"] == dataset],
                        key=lambda x: (x["assessor"], x["target"])):
            lines.append("| %s | %s | %s | %.3f | %.3f | %+.3f | %.3f | %s | %s | %d |" % (
                r["assessor"], r["target"], r["arm"], r["mu_inc"], r["mu_cor"], r["gap"],
                r["level"],
                "—" if r["thr"] is None else "%.3f" % r["thr"],
                "—" if r["bal_acc"] is None else "%.3f" % r["bal_acc"],
                r["n_inc"] + r["n_cor"]))
        lines.append("")

    # The characterisation question, stated directly: per assessor, how much do the
    # level and the optimal threshold move as the target changes?
    lines += ["## Is the operating point a property of the assessor?", "",
              "Spread of `level` and `thr` across that assessor's targets. Small spread =",
              "one threshold serves every target; large = re-fit per deployment.", "",
              "| dataset | assessor | targets | level mean | level range | thr mean | thr range |",
              "|---|---|---|---|---|---|---|"]
    for dataset in sorted({r["dataset"] for r in rows}):
        for asr in sorted({r["assessor"] for r in rows if r["dataset"] == dataset}):
            sub = [r for r in rows if r["dataset"] == dataset and r["assessor"] == asr]
            if len(sub) < 2:
                continue
            lv = [r["level"] for r in sub]
            th = [r["thr"] for r in sub if r["thr"] is not None]
            lines.append("| %s | %s | %d | %.3f | %.3f–%.3f | %s | %s |" % (
                dataset, asr, len(sub), statistics.mean(lv), min(lv), max(lv),
                "%.3f" % statistics.mean(th) if th else "—",
                "%.3f–%.3f" % (min(th), max(th)) if th else "—"))

    with open(a.out, "w") as fo:
        fo.write("\n".join(lines) + "\n")
    print("cells: %d" % len(rows))
    print("wrote %s and %s" % (a.out, a.csv))


if __name__ == "__main__":
    main()
