#!/usr/bin/env python3
"""Step-level AUROC for every self-assessment metric x scope, per (dataset x model).

Reads the CSVs written by selfassess_table.py — not the raw jsonl. The extraction layer
already resolved spans, stages and probe kinds, so this stays a pure scoring pass and any
fix to metric definitions happens in exactly one place.

Scopes
  SPLIT-thought  <metric>_T          SPLIT-action  <metric>_A
  AGG-mean       mean of the two     AGG-true      <metric>_R, or _J for in-generation
                                                   signals that are emitted once per step

AUROC is SOFT: weighted by judge_correct_frac, positive class = incorrect. A metric whose
AUROC is below 0.5 is INVERTED for its family — reported as-is rather than flipped, since
a consistently inverted signal is a finding (the metric is anti-correlated with error),
while silently flipping it would hide that.

Orientation note: MTE / MaxTE / PPL / SP and every U-style probe are all "higher = more
uncertain", so the positive class (incorrect) should score higher. c-hat and the
verbalized confidences are CONFIDENCE, so they are negated before scoring — otherwise
they would appear inverted for a purely definitional reason.

  selfassess_auroc.py [--indir reports/tables/selfassess] [--out ...md] [--csv ...csv]
"""
import argparse
import collections
import csv
import glob
import math
import os

SCOPES = ["SPLIT-thought", "SPLIT-action", "AGG-mean", "AGG-true"]
# stems that are CONFIDENCE (higher = more certain) and must be negated to align with
# the uncertainty convention shared by every other metric
CONFIDENCE_STEMS = {"chat_ingen", "sep_verbalized", "posthoc_num"}
NON_METRIC = {"task_id", "step_idx", "tau", "loop_flag", "obs_changed",
              "in_admissible", "judge_correct_frac", "judge_n_valid"}


def soft_auroc(vals, cs):
    wpos = [1 - c for c in cs]
    wneg = list(cs)
    P, N = sum(wpos), sum(wneg)
    if P <= 0 or N <= 0:
        return None
    idx = sorted(range(len(vals)), key=lambda i: vals[i])
    num = cum = 0.0
    i = 0
    while i < len(idx):
        j = i
        while j < len(idx) and vals[idx[j]] == vals[idx[i]]:
            j += 1
        gp = sum(wpos[idx[k]] for k in range(i, j))
        gn = sum(wneg[idx[k]] for k in range(i, j))
        num += gp * (cum + 0.5 * gn)
        cum += gn
        i = j
    return num / (P * N)


def boot_ci(rows, stem, scope, tasks_by, boot, seed=11):
    """95% CI, resampled by EPISODE. Steps within a trajectory are dependent, so
    step-level resampling would understate the interval."""
    import random
    rng = random.Random(seed)
    tasks = list(tasks_by)
    if len(tasks) < 3 or boot <= 0:
        return None, None
    draws = []
    for _ in range(boot):
        sample = [tasks[rng.randrange(len(tasks))] for _ in range(len(tasks))]
        v, c = [], []
        for t in sample:
            for val, lab in tasks_by[t]:
                v.append(val)
                c.append(lab)
        au = soft_auroc(v, c) if v else None
        if au is not None:
            draws.append(au)
    if not draws:
        return None, None
    draws.sort()
    return draws[int(0.025 * len(draws))], draws[min(len(draws) - 1, int(0.975 * len(draws)))]


def scope_series(rows, stem, scope):
    """-> [(task_id, value, label)] for one metric stem under one scope."""
    out = []
    for r in rows:
        lab = r.get("judge_correct_frac")
        if lab is None:
            continue
        t, a = r.get(stem + "_T"), r.get(stem + "_A")
        if scope == "SPLIT-thought":
            v = t
        elif scope == "SPLIT-action":
            v = a
        elif scope == "AGG-mean":
            v = None if t is None or a is None else (t + a) / 2.0
        else:
            v = r.get(stem + "_R")
            if v is None:
                v = r.get(stem + "_J")
        if v is None:
            continue
        if stem in CONFIDENCE_STEMS:
            v = -v
        out.append((r["task_id"], v, lab))
    return out


def load_csv(path):
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            out = {"task_id": r["task_id"], "step_idx": r["step_idx"]}
            for k, v in r.items():
                if k in ("task_id", "step_idx") or v == "":
                    continue
                try:
                    out[k] = float(v)
                except ValueError:
                    out[k] = v
            rows.append(out)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", default="reports/tables/selfassess")
    ap.add_argument("--out", default="reports/tables/selfassess_auroc.md")
    ap.add_argument("--csv", default="reports/tables/selfassess_auroc.csv")
    ap.add_argument("--boot", type=int, default=0, help="episode bootstrap draws; 0 = skip CIs")
    ap.add_argument("--min-n", type=int, default=30)
    a = ap.parse_args()

    all_rows = []
    per_cell = []
    for path in sorted(glob.glob(os.path.join(a.indir, "*__*.csv"))):
        base = os.path.basename(path)[:-4]
        if base == "summary":
            continue
        dataset, model = base.split("__", 1)
        rows = load_csv(path)
        stems = sorted({c.rsplit("_", 1)[0] for r in rows for c in r
                        if c not in NON_METRIC and c.rsplit("_", 1)[-1] in ("T", "A", "R", "J")})
        cell = []
        for stem in stems:
            for scope in SCOPES:
                series = scope_series(rows, stem, scope)
                if len(series) < a.min_n:
                    continue
                vals = [s[1] for s in series]
                labs = [s[2] for s in series]
                au = soft_auroc(vals, labs)
                if au is None:
                    continue
                lo = hi = None
                if a.boot:
                    tasks_by = collections.defaultdict(list)
                    for tid, v, l in series:
                        tasks_by[tid].append((v, l))
                    lo, hi = boot_ci(rows, stem, scope, tasks_by, a.boot)
                rec = dict(dataset=dataset, model=model, metric=stem, scope=scope,
                           n=len(series), auroc=au, lo=lo, hi=hi)
                cell.append(rec)
                all_rows.append(rec)
        cell.sort(key=lambda r: -r["auroc"])
        per_cell.append((dataset, model, cell))
        if cell:
            b = cell[0]
            print("%-9s %-26s best=%s/%s %.3f  (rows=%d)"
                  % (dataset, model, b["metric"], b["scope"], b["auroc"], len(cell)))

    os.makedirs(os.path.dirname(a.csv), exist_ok=True)
    with open(a.csv, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["dataset", "model", "metric", "scope", "n", "auroc", "ci_lo", "ci_hi"])
        for r in all_rows:
            w.writerow([r["dataset"], r["model"], r["metric"], r["scope"], r["n"],
                        "%.6f" % r["auroc"],
                        "" if r["lo"] is None else "%.6f" % r["lo"],
                        "" if r["hi"] is None else "%.6f" % r["hi"]])

    lines = ["# Self-assessment AUROC per (dataset x model)", "",
             "Step-level soft AUROC vs the 3-judge ensemble, positive class = incorrect.",
             "**Judge-anchored, therefore provisional** until gate-1 recomputation.", "",
             "Confidence-valued signals (c-hat, separate verbalized, post-hoc numeric) are",
             "negated so that every row shares the 'higher = more uncertain' convention.",
             "AUROC below 0.5 means the signal is anti-correlated with error; reported as-is",
             "rather than flipped, because a consistently inverted metric is a finding.", ""]

    lines += ["## Best metric per cell", "",
              "| dataset | model | metric | scope | n | AUROC |", "|---|---|---|---|---|---|"]
    for dataset, model, cell in per_cell:
        if cell:
            b = cell[0]
            lines.append("| %s | %s | %s | %s | %d | %.3f |"
                         % (dataset, model, b["metric"], b["scope"], b["n"], b["auroc"]))
    lines.append("")

    for dataset, model, cell in per_cell:
        lines += ["## %s / %s" % (dataset, model), "",
                  "| rank | metric | scope | n | AUROC | 95% CI |", "|---|---|---|---|---|---|"]
        for i, r in enumerate(cell, 1):
            ci = "—" if r["lo"] is None else "[%.3f, %.3f]" % (r["lo"], r["hi"])
            lines.append("| %d | %s | %s | %d | %.3f | %s |"
                         % (i, r["metric"], r["scope"], r["n"], r["auroc"], ci))
        lines.append("")

    with open(a.out, "w") as fo:
        fo.write("\n".join(lines) + "\n")
    print("\nwrote %s and %s (%d rows)" % (a.out, a.csv, len(all_rows)))


if __name__ == "__main__":
    main()
