#!/usr/bin/env python3
"""Gate-1 Phase 5 — rerun the existing analyses against the environment label.

Runs, unmodified except for the label input:
  crossprobe_matrix_auroc.py     all cells, all four scopes
  uncertainty_levels.py          mu_inc / mu_cor / gap / Youden
  percentile_consistency.py      lift@k, precision/recall@k
and fits g (mean U vs target error rate, per assessor) from the levels CSV.

Each is run in three label conditions:
  ensemble        the published 3-judge label over all judged steps (the baseline)
  env-restricted  y_env, over only the steps y_env can label            [brief's (i)]
  env-full        y_env over every step, unlabelled as negative-class   [brief's (ii)]
plus `ensemble-on-env-support`: the 3-judge label over exactly the env-restricted step
universe. Without it, an ensemble-vs-env delta mixes a label change with a step-set
change and neither can be read off.

  gate1_phase5.py [--pivot DIR] [--outdir tables_gate1] [--boot N]
"""
import argparse
import collections
import csv
import json
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

CONDITIONS = [
    # (tag, extra args)
    ("ensemble", ["--labels", "ensemble"]),
    ("ensemble_on_env_support", ["--labels", "ensemble_on_env_support",
                                 "--label-mode", "restricted"]),
    ("env_restricted", ["--labels", "env", "--label-mode", "restricted"]),
    ("env_full", ["--labels", "env", "--label-mode", "full"]),
]


def run(script, args, label_file, outdir, tag, extra):
    out = os.path.join(outdir, tag)
    os.makedirs(out, exist_ok=True)
    stem = script.replace(".py", "")
    cmd = [sys.executable, os.path.join(HERE, script), "--pivot", args.pivot,
           "--label-file", label_file] + extra
    if script == "crossprobe_matrix_auroc.py":
        cmd += ["--out", os.path.join(out, "crossprobe_matrix.md"),
                "--json", os.path.join(out, "crossprobe_matrix.json"),
                "--csv", os.path.join(out, "crossprobe_matrix.csv"),
                "--boot", str(args.boot)]
    else:
        cmd += ["--out", os.path.join(out, stem + ".md"),
                "--csv", os.path.join(out, stem + ".csv")]
        if args.scope:
            cmd += ["--scope", args.scope]
    sys.stderr.write("[%s] %s\n" % (tag, script))
    sys.stderr.flush()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-2000:] + r.stderr[-4000:])
        raise SystemExit("%s failed under %s" % (script, tag))
    return out


def read_csv(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def fit_g(levels_rows):
    """g = per-assessor correlation between pooled mean U and the target error rate.

    Error rate comes from the same rows the levels script produced (n_inc / n), so it
    is the error rate under whichever label that run used — which is the point.
    """
    by = collections.defaultdict(list)
    for r in levels_rows:
        try:
            ni, nc = float(r["n_inc"]), float(r["n_cor"])
            lvl = float(r["level"])
        except (ValueError, KeyError, TypeError):
            continue
        if ni + nc <= 0:
            continue
        by[(r["dataset"], r["assessor"])].append((lvl, ni / (ni + nc)))
    out = {}
    for key, pts in sorted(by.items()):
        out["%s/%s" % key] = {
            "n_targets": len(pts),
            "r": pearson([p[0] for p in pts], [p[1] for p in pts]),
        }
    # pooled across datasets, per assessor
    by_a = collections.defaultdict(list)
    for r in levels_rows:
        try:
            ni, nc, lvl = float(r["n_inc"]), float(r["n_cor"]), float(r["level"])
        except (ValueError, KeyError, TypeError):
            continue
        if ni + nc > 0:
            by_a[r["assessor"]].append((lvl, ni / (ni + nc)))
    for asr, pts in sorted(by_a.items()):
        out["ALL/%s" % asr] = {"n_targets": len(pts),
                               "r": pearson([p[0] for p in pts], [p[1] for p in pts])}
    return out


def f3(v):
    return "—" if v is None or v == "" else ("%.3f" % float(v))


def normalised_separation(ranks_rows, pct_rows):
    """f = (observed median percentile of the incorrect pool - 50) / (bound - 50).

    The perfect-ranking bound for an error rate p is 100*(1 - p/2): a flawless ranker
    puts the incorrect pool in the top p, so its median sits there by construction.
    Dividing it out is what makes f base-rate free — this is R1's quantity, and the
    formula is reproduced from OPERATING_POINT_REPORT.md §5 unchanged.
    """
    base = {}
    for r in pct_rows:
        key = (r["dataset"], r["target"], r["assessor"])
        try:
            base[key] = float(r["base"])          # identical across k for a cell
        except (ValueError, TypeError, KeyError):
            pass
    out = {}
    for r in ranks_rows:
        key = (r["dataset"], r["target"], r["assessor"])
        p = base.get(key)
        if p is None or not (0 < p < 1):
            continue
        try:
            med = float(r["inc_med"])
        except (ValueError, TypeError, KeyError):
            continue
        bound = 100.0 * (1 - p / 2.0)
        if abs(bound - 50.0) < 1e-9:
            continue
        out[key] = (med - 50.0) / (bound - 50.0)
    return out


def f_by_assessor(fmap):
    by = collections.defaultdict(list)
    for (_ds, _tgt, asr), v in fmap.items():
        by[asr].append(v)
    return {a: {"mean": statistics.mean(v), "min": min(v), "max": max(v),
                "range": max(v) - min(v), "n_cells": len(v)}
            for a, v in sorted(by.items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels-csv", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--outdir", default="reports/gate1/tables_gate1")
    ap.add_argument("--scope", default="SPLIT-action")
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    dirs = {}
    for tag, extra in CONDITIONS:
        for script in ("crossprobe_matrix_auroc.py", "uncertainty_levels.py",
                       "percentile_consistency.py"):
            dirs[tag] = run(script, a, a.labels_csv, a.outdir, tag, extra)

    gfits, fsep = {}, {}
    for tag, _ in CONDITIONS:
        rows = read_csv(os.path.join(a.outdir, tag, "uncertainty_levels.csv"))
        gfits[tag] = fit_g(rows)
        fsep[tag] = f_by_assessor(normalised_separation(
            read_csv(os.path.join(a.outdir, tag, "percentile_consistency_ranks.csv")),
            read_csv(os.path.join(a.outdir, tag, "percentile_consistency.csv"))))
    with open(os.path.join(a.outdir, "g_fit.json"), "w") as f:
        json.dump(gfits, f, indent=2)
    with open(os.path.join(a.outdir, "separation_f.json"), "w") as f:
        json.dump(fsep, f, indent=2)

    side_by_side(a.outdir, gfits, a.scope)
    write_separation(a.outdir, fsep)
    print("wrote %s" % a.outdir)


def side_by_side(outdir, gfits, scope):
    tags = [t for t, _ in CONDITIONS]

    # ---- crossprobe AUROC, per (dataset, target, assessor, scope)
    mats = {t: read_csv(os.path.join(outdir, t, "crossprobe_matrix.csv")) for t in tags}
    key_of = None
    for t in tags:
        if mats[t]:
            cols = mats[t][0].keys()
            for cand in (("dataset", "target", "assessor", "scope"),):
                if all(c in cols for c in cand):
                    key_of = cand
            break
    L = ["# Gate-1 Phase 5 — crossprobe AUROC, ensemble label vs environment label", "",
         "Positive class = incorrect. `ensemble` is the published number. "
         "`ens@env` is the same 3-judge label restricted to the steps `y_env` can "
         "label, so `ens@env` -> `env_restricted` isolates the label change. "
         "`R3` flags any cell whose AUROC moves by more than 0.05 from `ensemble`.", ""]
    if not key_of:
        L.append("_crossprobe CSV missing the expected key columns; see the per-condition "
                 "directories._")
    else:
        idx = {t: {tuple(r[c] for c in key_of): r for r in mats[t]} for t in tags}
        allkeys = sorted(set().union(*[set(idx[t]) for t in tags]))
        L += ["| dataset | target | assessor | scope | " +
              " | ".join(tags) + " | n(env) | Δ vs ensemble | R3 |",
              "|---|---|---|---|" + "---|" * (len(tags) + 3)]
        n_flag = 0
        for k in allkeys:
            vals = {}
            for t in tags:
                r = idx[t].get(k)
                vals[t] = None if not r else (r.get("auroc") or None)
            base = vals.get("ensemble")
            envr = vals.get("env_restricted")
            d = (None if base in (None, "") or envr in (None, "")
                 else float(envr) - float(base))
            flag = "**FLAG**" if d is not None and abs(d) > 0.05 else ""
            n_flag += bool(flag)
            n_env = (idx["env_restricted"].get(k) or {}).get("n", "")
            # `k` is the 4-tuple key and expands to four columns once joined, so this
            # row has 4 + len(tags) + 3 cells against the header above.
            L.append("| %s | %s | %s | %s | %s |" % (
                " | ".join(k), " | ".join(f3(vals[t]) for t in tags), n_env,
                "—" if d is None else "%+.3f" % d, flag))
        L += ["", "**R3: %d of %d cells move by more than 0.05.**" % (n_flag, len(allkeys))]
    write(os.path.join(outdir, "crossprobe_side_by_side.md"), L)

    # ---- uncertainty levels
    lv = {t: read_csv(os.path.join(outdir, t, "uncertainty_levels.csv")) for t in tags}
    L = ["# Gate-1 Phase 5 — uncertainty levels, ensemble vs environment label",
         "", "Scope %s. `gap` = mu_inc - mu_cor." % scope, "",
         "| dataset | target | assessor | " +
         " | ".join("%s gap" % t for t in tags) + " | n_inc(env) | n_cor(env) |",
         "|---|---|---|" + "---|" * (len(tags) + 2)]
    idx = {t: {(r["dataset"], r["target"], r["assessor"]): r for r in lv[t]} for t in tags}
    for k in sorted(set().union(*[set(idx[t]) for t in tags])):
        er = idx["env_restricted"].get(k, {})
        L.append("| %s | %s | %s |" % (
            " | ".join(k),
            " | ".join(f3((idx[t].get(k) or {}).get("gap")) for t in tags),
            " %s | %s " % (er.get("n_inc", ""), er.get("n_cor", ""))))
    write(os.path.join(outdir, "uncertainty_levels_side_by_side.md"), L)

    # ---- percentile consistency
    pc = {t: read_csv(os.path.join(outdir, t, "percentile_consistency.csv")) for t in tags}
    L = ["# Gate-1 Phase 5 — percentile consistency, ensemble vs environment label",
         "", "Scope %s. `lift` = precision in the top k%% divided by the base rate." % scope, ""]
    if pc["ensemble"]:
        cols = pc["ensemble"][0].keys()
        kcols = [c for c in ("dataset", "target", "assessor", "k") if c in cols]
        idx = {t: {tuple(r[c] for c in kcols): r for r in pc[t]} for t in tags}
        L += ["| " + " | ".join(kcols) + " | " + " | ".join("%s lift" % t for t in tags) +
              " | base(env) |",
              "|" + "---|" * (len(kcols) + len(tags) + 1)]
        for k in sorted(set().union(*[set(idx[t]) for t in tags])):
            L.append("| %s | %s | %s |" % (
                " | ".join(k),
                " | ".join(f3((idx[t].get(k) or {}).get("lift")) for t in tags),
                f3((idx["env_restricted"].get(k) or {}).get("base"))))
    write(os.path.join(outdir, "percentile_consistency_side_by_side.md"), L)

    # ---- g fit
    L = ["# Gate-1 Phase 5 — the g fit (mean U vs target error rate)", "",
         "Per assessor, the correlation across its targets between pooled mean U and "
         "the target's error rate. R2 asks whether this drops below 0.85 for the "
         "capable judges under the environment label.", "",
         "| assessor scope | " + " | ".join(tags) + " | n targets |",
         "|---|" + "---|" * (len(tags) + 1)]
    keys = sorted(set().union(*[set(gfits[t]) for t in tags]))
    for k in keys:
        n = (gfits["env_restricted"].get(k) or {}).get("n_targets", "")
        L.append("| %s | %s | %s |" % (
            k, " | ".join(f3((gfits[t].get(k) or {}).get("r")) for t in tags), n))
    write(os.path.join(outdir, "g_fit_side_by_side.md"), L)


def write_separation(outdir, fsep):
    tags = [t for t, _ in CONDITIONS]
    L = ["# Gate-1 Phase 5 — normalised separation f, ensemble vs environment label", "",
         "`f = (median percentile of the incorrect pool - 50) / (perfect-ranking bound "
         "- 50)`, bound `= 100*(1 - p/2)` for error rate p. Base-rate free. This is the "
         "quantity R1's floor is stated on (f >= 0.70, range width <= 0.25).", "",
         "| assessor | " + " | ".join("%s mean (range)" % t for t in tags) + " | cells |",
         "|---|" + "---|" * (len(tags) + 1)]
    assessors = sorted(set().union(*[set(fsep[t]) for t in tags]))
    for asr in assessors:
        cells = []
        for t in tags:
            d = fsep[t].get(asr)
            cells.append("—" if not d else "%.3f (%.2f–%.2f)"
                         % (d["mean"], d["min"], d["max"]))
        n = (fsep["env_restricted"].get(asr) or {}).get("n_cells", "")
        L.append("| %s | %s | %s |" % (asr, " | ".join(cells), n))
    write(os.path.join(outdir, "separation_f_side_by_side.md"), L)


def write(path, lines):
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
