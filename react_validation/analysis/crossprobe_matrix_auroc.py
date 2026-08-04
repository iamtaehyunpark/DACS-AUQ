#!/usr/bin/env python3
"""Assessor x target step-level AUROC over the pivot layout.

Replaces crossprobe_auroc.py, which hardcoded four ALFWorld arms and a single Qwen
assessor and could only express SELF-vs-QWEN. This walks result/pivot and builds the
full matrix, with each arm's own probes.jsonl as the diagonal.

Scopes (the recipe axis whose stability across targets is the thesis):
  SPLIT-thought  U_T_ptrue      SPLIT-action  U_A_ptrue
  AGG-mean       mean of the two               AGG-true   U_R_ptrue (whole response)

Labels are the 3-judge ensemble, weighted by the fraction voting CORRECT (soft AUROC,
positive class = incorrect). That makes every number here judge-anchored, which is the
circularity problem gate 1 exists for — these are NOT headline numbers until recomputed
against environment-anchored labels. Printed as a reminder, not a footnote.

  crossprobe_matrix_auroc.py [--pivot DIR] [--out matrix.md] [--json matrix.json]
"""
import argparse
import collections
import json
import os


def soft_auroc(vals, cs):
    """cs = fraction of judges voting CORRECT; positive class = incorrect. Ties handled."""
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


def load_labels(path):
    """(task_id, step_idx) -> fraction of judges voting correct."""
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
    """(task_id, step_idx) -> {'T': u, 'A': u, 'R': u} from any number of probe files."""
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
            key = (r.get("task_id"), r.get("step_idx"))
            field = r.get("metric_field") or ""
            if field.startswith("U_T"):
                out[key]["T"] = u
            elif field.startswith("U_A"):
                out[key]["A"] = u
            elif field.startswith("U_R"):
                out[key]["R"] = u
    return out


def scoped(vals, scope):
    if scope == "SPLIT-thought":
        return vals.get("T")
    if scope == "SPLIT-action":
        return vals.get("A")
    if scope == "AGG-true":
        return vals.get("R")
    if scope == "AGG-mean":
        t, a = vals.get("T"), vals.get("A")
        return None if t is None or a is None else (t + a) / 2.0
    return None


SCOPES = ["SPLIT-thought", "SPLIT-action", "AGG-mean", "AGG-true"]


def cell_auroc(probes, labels):
    """AUROC per scope for one (assessor, target) cell, plus the joined n."""
    res = {}
    for scope in SCOPES:
        v, c = [], []
        for key, vals in probes.items():
            if key not in labels:
                continue
            u = scoped(vals, scope)
            if u is None:
                continue
            v.append(u)
            c.append(labels[key])
        res[scope] = {"auroc": soft_auroc(v, c) if v else None, "n": len(v)}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--out", default="reports/tables/crossprobe_matrix.md")
    ap.add_argument("--json", default="reports/tables/crossprobe_matrix.json")
    a = ap.parse_args()

    xp_root = os.path.join(a.pivot, "crossprobe")
    results = {}

    for dataset in sorted(d for d in os.listdir(a.pivot)
                          if os.path.isdir(os.path.join(a.pivot, d)) and d != "crossprobe"):
        ds_dir = os.path.join(a.pivot, dataset)
        for target in sorted(os.listdir(ds_dir)):
            tdir = os.path.join(ds_dir, target)
            if not os.path.isdir(tdir):
                continue
            labels = load_labels(os.path.join(tdir, "judge.jsonl"))
            if not labels:
                continue

            # diagonal: the arm's own probes, produced at generation time
            self_probes = load_ptrue([os.path.join(tdir, "probes.jsonl")])
            if self_probes:
                results[(dataset, target, target)] = cell_auroc(self_probes, labels)

            # off-diagonal
            xdir = os.path.join(xp_root, dataset, target)
            if not os.path.isdir(xdir):
                continue
            assessors = sorted({f.split(".")[1] for f in os.listdir(xdir)
                                if f.startswith("ptrue.") and f.endswith(".jsonl")
                                and not f.endswith(".log")})
            for assessor in assessors:
                paths = [os.path.join(xdir, "ptrue.%s.%s.jsonl" % (assessor, p))
                         for p in ("stages", "response")]
                probes = load_ptrue(paths)
                if probes:
                    results[(dataset, target, assessor)] = cell_auroc(probes, labels)

    datasets = sorted({k[0] for k in results})
    lines = ["# Cross-probe matrix — step-level AUROC (soft, 3-judge labels)", ""]
    lines.append("Positive class = judge-incorrect. **Labels are LLM-derived**: these are")
    lines.append("not headline numbers until recomputed against environment-anchored")
    lines.append("targets (gate 1). Diagonal = the arm's own probes (self-assessment).")
    lines.append("")

    for dataset in datasets:
        targets = sorted({k[1] for k in results if k[0] == dataset})
        assessors = sorted({k[2] for k in results if k[0] == dataset})
        for scope in SCOPES:
            lines.append("## %s — %s" % (dataset, scope))
            lines.append("")
            lines.append("| assessor \\ target | " + " | ".join(targets) + " |")
            lines.append("|---" * (len(targets) + 1) + "|")
            for assessor in assessors:
                row = ["**%s**" % assessor]
                for target in targets:
                    cell = results.get((dataset, target, assessor))
                    if not cell or cell[scope]["auroc"] is None:
                        row.append("—")
                    else:
                        mark = " *(self)*" if assessor == target else ""
                        row.append("%.3f%s" % (cell[scope]["auroc"], mark))
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")

    # The thesis view: for a fixed assessor, does the winning scope stay the same as the
    # target changes? Scattered winners down a column would falsify recipe invariance.
    lines.append("## Winning scope per (assessor, target) — the invariance view")
    lines.append("")
    lines.append("| dataset | assessor | " + " | ".join(["winner per target"]) + " |")
    lines.append("|---|---|---|")
    for dataset in datasets:
        for assessor in sorted({k[2] for k in results if k[0] == dataset}):
            wins = []
            for target in sorted({k[1] for k in results if k[0] == dataset}):
                cell = results.get((dataset, target, assessor))
                if not cell:
                    continue
                avail = [(s, cell[s]["auroc"]) for s in SCOPES if cell[s]["auroc"] is not None]
                if avail:
                    wins.append("%s:%s" % (target.split("-")[0], max(avail, key=lambda x: x[1])[0]))
            if wins:
                lines.append("| %s | %s | %s |" % (dataset, assessor, ", ".join(wins)))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fo:
        fo.write("\n".join(lines) + "\n")
    with open(a.json, "w") as fo:
        json.dump({"%s|%s|%s" % k: v for k, v in results.items()}, fo, indent=2)
    print("cells: %d" % len(results))
    print("wrote %s and %s" % (a.out, a.json))


if __name__ == "__main__":
    main()
