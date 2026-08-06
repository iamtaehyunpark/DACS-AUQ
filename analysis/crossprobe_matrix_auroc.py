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


def cell_auroc(probes, labels, keep=None):
    """AUROC per scope for one (assessor, target) cell, plus the joined n.

    keep is an optional dict that receives the per-step rows the bootstrap needs:
    task_id (the resampling unit) and the value of every scope for that step."""
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
    if keep is not None:
        rows = []
        for key, vals in probes.items():
            if key not in labels:
                continue
            rows.append((key[0], labels[key], {s: scoped(vals, s) for s in SCOPES}))
        keep["rows"] = rows
    return res


def invariance_delta(rows, fixed_scope, boot=1000, seed=17):
    """Cost of using ONE fixed scope instead of this target's best, with a CI.

    This is the gate-2' quantity. Reporting the argmax alone is not enough: where AUROC
    sits near chance the winner is noise, and a bare argmax manufactures "the recipe
    flipped" out of nothing. What matters is whether fixing the recipe COSTS anything,
    so the delta is what gets a confidence interval.

    Resampling is by episode (task_id), not by step: steps within a trajectory are
    strongly dependent, and resampling them independently would understate the interval.
    """
    import random
    by_task = collections.defaultdict(list)
    for task_id, c, vals in rows:
        by_task[task_id].append((c, vals))
    tasks = list(by_task)
    if len(tasks) < 3:
        return None

    def auroc_for(sample_tasks, scope):
        v, c = [], []
        for t in sample_tasks:
            for cc, vals in by_task[t]:
                u = vals.get(scope)
                if u is not None:
                    v.append(u)
                    c.append(cc)
        return soft_auroc(v, c) if v else None

    def delta_for(sample_tasks):
        scores = {s: auroc_for(sample_tasks, s) for s in SCOPES}
        avail = {s: a for s, a in scores.items() if a is not None}
        if not avail or fixed_scope not in avail:
            return None
        return max(avail.values()) - avail[fixed_scope]

    point = delta_for(tasks)
    if point is None:
        return None
    rng = random.Random(seed)
    draws = []
    for _ in range(boot):
        sample = [tasks[rng.randrange(len(tasks))] for _ in range(len(tasks))]
        d = delta_for(sample)
        if d is not None:
            draws.append(d)
    if not draws:
        return {"delta": point, "lo": None, "hi": None}
    draws.sort()
    return {"delta": point,
            "lo": draws[int(0.025 * len(draws))],
            "hi": draws[min(len(draws) - 1, int(0.975 * len(draws)))]}



# ---------------------------------------------------------------- gate 1
# Gate 1 swaps the LABEL INPUT and nothing else. No statistic below this line
# changes: the dict shape returned here — {(task_id, step_idx): fraction of
# judges voting CORRECT} — is exactly what the ensemble loader returned, with
# environment labels entering as hard 0.0 / 1.0.
def _gate1_labels(args, dataset, target, tdir):
    which = getattr(args, "labels", "ensemble")
    if which == "ensemble":
        return load_labels(os.path.join(tdir, "judge.jsonl"))
    import gate1_label_source
    if which == "ensemble_on_env_support":
        return gate1_label_source.load_ensemble_labels(
            args.label_file, dataset, target, mode=args.label_mode,
            column=args.label_column)
    return gate1_label_source.load_env_labels(
        args.label_file, dataset, target, mode=args.label_mode,
        column=args.label_column)


def _gate1_add_args(ap):
    ap.add_argument("--labels", default="ensemble",
                    choices=["ensemble", "env", "ensemble_on_env_support"],
                    help="ensemble: the published 3-judge label over all judged steps. "
                         "env: gate-1 y_env. ensemble_on_env_support: the 3-judge label "
                         "over exactly the y_env-labelable steps, so a side-by-side "
                         "isolates the label change from the step-set change")
    ap.add_argument("--label-file", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--label-mode", choices=["restricted", "full"], default="restricted",
                    help="restricted: only y_env-labelable steps. "
                         "full: all steps, unlabelled as negative-class-with-noise")
    ap.add_argument("--label-column", default="y_env")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--out", default="reports/tables/crossprobe_matrix.md")
    ap.add_argument("--json", default="reports/tables/crossprobe_matrix.json")
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--csv", default="reports/tables/crossprobe_matrix.csv",
                    help="flat one-row-per-(cell,scope) table; the JSON is nested and "
                         "awkward to sort or paste, so this is the sharable artifact")
    _gate1_add_args(ap)
    a = ap.parse_args()

    xp_root = os.path.join(a.pivot, "crossprobe")
    results = {}
    steprows = {}

    for dataset in sorted(d for d in os.listdir(a.pivot)
                          if os.path.isdir(os.path.join(a.pivot, d)) and d != "crossprobe"):
        ds_dir = os.path.join(a.pivot, dataset)
        for target in sorted(os.listdir(ds_dir)):
            tdir = os.path.join(ds_dir, target)
            if not os.path.isdir(tdir):
                continue
            labels = _gate1_labels(a, dataset, target, tdir)
            if not labels:
                continue

            # Diagonal: the arm's own probes, produced at generation time. BOTH files —
            # HotpotQA wrote whole-response P(True) inline, ALFWorld to a separate
            # probes.aggtrue.jsonl. Reading only probes.jsonl silently drops AGG-true
            # from every ALFWorld self cell while leaving it present in the cross cells,
            # which makes the self column look scope-poorer than it is.
            self_probes = load_ptrue([os.path.join(tdir, "probes.jsonl"),
                                      os.path.join(tdir, "probes.aggtrue.jsonl")])
            if self_probes:
                keep = {}
                results[(dataset, target, target)] = cell_auroc(self_probes, labels, keep)
                steprows[(dataset, target, target)] = keep.get("rows", [])

            # off-diagonal
            xdir = os.path.join(xp_root, dataset, target)
            if not os.path.isdir(xdir):
                continue
            # Strip the known prefix/suffix instead of splitting on "." — model names
            # contain dots (Qwen3.6-35B-A3B, Mistral-7B-Instruct-v0.3, Llama-3.3-70B),
            # so f.split(".")[1] silently yields "Qwen3" and drops those assessors.
            assessors = set()
            for f in os.listdir(xdir):
                if not f.startswith("ptrue.") or not f.endswith(".jsonl"):
                    continue
                stem = f[len("ptrue."):-len(".jsonl")]
                for suf in (".stages", ".response"):
                    if stem.endswith(suf):
                        stem = stem[: -len(suf)]
                        break
                else:
                    continue          # per-shard part file, not a merged output
                if stem:
                    assessors.add(stem)
            assessors = sorted(assessors)
            for assessor in assessors:
                paths = [os.path.join(xdir, "ptrue.%s.%s.jsonl" % (assessor, p))
                         for p in ("stages", "response")]
                probes = load_ptrue(paths)
                if probes:
                    keep = {}
                    results[(dataset, target, assessor)] = cell_auroc(probes, labels, keep)
                    steprows[(dataset, target, assessor)] = keep.get("rows", [])

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

    # ---- gate 2' : does FIXING the recipe cost anything, per target? ----
    lines.append("")
    lines.append("## Invariance: cost of a single fixed scope vs the per-target best")
    lines.append("")
    lines.append("For each assessor the fixed scope is the one with the best MEAN AUROC")
    lines.append("across its targets. delta = (per-target best) - (fixed), so delta >= 0 and")
    lines.append("SMALL means fixing the recipe is cheap. CI is a 95% episode-clustered")
    lines.append("bootstrap on the delta itself - an argmax alone manufactures 'the recipe")
    lines.append("flipped' wherever AUROC sits near chance.")
    lines.append("")
    lines.append("| dataset | assessor | fixed scope | target | delta | 95% CI |")
    lines.append("|---|---|---|---|---|---|")
    for dataset in datasets:
        for assessor in sorted({k[2] for k in results if k[0] == dataset}):
            cells = {k[1]: v for k, v in results.items()
                     if k[0] == dataset and k[2] == assessor}
            means = {}
            for scope in SCOPES:
                vals = [c[scope]["auroc"] for c in cells.values() if c[scope]["auroc"] is not None]
                if vals:
                    means[scope] = sum(vals) / len(vals)
            if not means:
                continue
            fixed = max(means, key=means.get)
            for target in sorted(cells):
                rows = steprows.get((dataset, target, assessor)) or []
                d = invariance_delta(rows, fixed, boot=a.boot) if rows else None
                if not d:
                    continue
                ci = ("[%.3f, %.3f]" % (d["lo"], d["hi"])) if d["lo"] is not None else "-"
                lines.append("| %s | %s | %s | %s | %.3f | %s |"
                             % (dataset, assessor, fixed, target, d["delta"], ci))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fo:
        fo.write("\n".join(lines) + "\n")
    with open(a.json, "w") as fo:
        json.dump({"%s|%s|%s" % k: v for k, v in results.items()}, fo, indent=2)

    # Flat table: one row per (dataset, target, assessor, scope). `arm` marks whether the
    # row is the model reading its own trajectories or someone else's — the single most
    # common filter, and easy to get wrong by string-matching model names after the fact.
    import csv as _csv
    with open(a.csv, "w", newline="") as fo:
        w = _csv.writer(fo)
        w.writerow(["dataset", "target", "assessor", "arm", "scope", "n", "auroc"])
        for (ds, tgt, asr) in sorted(results):
            cell = results[(ds, tgt, asr)]
            arm = "self" if asr == tgt else "cross"
            for scope in SCOPES:
                au = cell[scope]["auroc"]
                if au is None:
                    continue
                w.writerow([ds, tgt, asr, arm, scope, cell[scope]["n"], "%.6f" % au])
    print("wrote %s" % a.csv)
    print("cells: %d" % len(results))
    print("wrote %s and %s" % (a.out, a.json))


if __name__ == "__main__":
    main()
