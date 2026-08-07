#!/usr/bin/env python3
"""S4 analyses — hindsight vs online, per A30 construct.

Spec: docs/specs/S4_SPEC.md + the 2026-08-07 single-judge amendment.  Qwen3.6-35B-A3B
only; the judge-agreement contrast is unobtainable and every conclusion here is a
single-model result.

  (i)   hindsight - online dAUROC per cell, paired episode-clustered bootstrap
  (ii)  agreement with OUTCOME labels: hindsight-judge vs online-judge
  (iii) R3 decomposition: construct share (L1->L2 at fixed evidence) vs information
        share (online->hindsight at fixed labels), residual shown not absorbed

Failure policy (spec section Failure policy): the ONLINE condition here must reproduce
the banked crossprobe AUROC to 0.001.  It is the same scores through a different code
path, so a mismatch means this script is wrong, not that the science moved.
"""
import argparse
import collections
import csv
import glob
import json
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s1_labels as SL                   # noqa: E402
import s1_matrix as SM                   # noqa: E402

SPEC = "docs/specs/S4_SPEC.md"
SEED = 13
NBOOT = 2000
JUDGE = "Qwen3.6-35B-A3B"
TOL = 0.001
CONSTRUCTS = ["violation+judgment", "judgment", "violation", "outcome", "y_env"]


def load_hindsight(root, judge):
    """{(ds, target): {(task_id, step_idx): (U, route, truncated)}}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "*", "*",
                                           "hindsight.%s.jsonl" % judge))):
        parts = f.split(os.sep)
        ds, tgt = parts[-3], parts[-2]
        d = {}
        for line in open(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("U") is None:
                continue
            d[(r["task_id"], r["step_idx"])] = (float(r["U"]), r.get("route"),
                                                int(r.get("truncated") or 0))
        if d:
            out[(ds, tgt)] = d
    return out


def coverage_rows(root, judge, in_matrix):
    rows = []
    for f in sorted(glob.glob(os.path.join(root, "*", "*",
                                           "hindsight.%s.jsonl" % judge))):
        parts = f.split(os.sep)
        ds, tgt = parts[-3], parts[-2]
        c = collections.Counter()
        trunc = n = 0
        for line in open(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            n += 1
            c[r.get("route")] += 1
            trunc += int(r.get("truncated") or 0)
        rows.append({"dataset": ds, "target": tgt,
                     "in_matrix": int((ds, tgt) in in_matrix), "records": n,
                     "main": c.get("main", 0), "long": c.get("long", 0),
                     "deferred_long": c.get("deferred_long", 0),
                     "truncated": trunc, "failed": c.get("failed", 0)})
    return rows


def cell_from(scores, labels, keys=None):
    """Build an SM.Cell from {(task,step): u} + label map, optionally restricted."""
    rows = []
    for k, u in scores.items():
        if keys is not None and k not in keys:
            continue
        yw = labels.get(k)
        if yw is not None:
            rows.append((u if not isinstance(u, tuple) else u[0], yw[0], yw[1], k[0]))
    if len(rows) < 50:
        return None
    c = SM.Cell(rows)
    if c.n_pos == 0 or c.n_neg == 0:
        return None
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hindsight", default="result/hindsight")
    ap.add_argument("--cache", default="runs/score_cache_AGG-true.pkl")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--banked", default="tables_S1")
    ap.add_argument("--outdir", default="tables_S4")
    ap.add_argument("--summary", default="S4_SUMMARY.md")
    ap.add_argument("--judge", default=JUDGE)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    online = pickle.load(open(a.cache, "rb"))
    hind = load_hindsight(a.hindsight, a.judge)
    in_matrix = set()
    for x in csv.DictReader(open(a.labels)):
        if x.get("in_matrix") == "1":
            in_matrix.add((x["dataset"], x["model"]))

    cov = coverage_rows(a.hindsight, a.judge, in_matrix)
    SM.write_csv(os.path.join(a.outdir, "S4_coverage.csv"), cov,
                 ["dataset", "target", "in_matrix", "records", "main", "long",
                  "deferred_long", "truncated", "failed"])

    results = {}
    repro = []
    for construct in CONSTRUCTS:
        lab = SL.load(a.labels, construct, in_matrix_only=True)
        rows = []
        for (ds, tgt), hd in sorted(hind.items()):
            if (ds, tgt) not in in_matrix:
                continue
            L = lab.get((ds, tgt))
            on = online.get((ds, a.judge, tgt))
            if not L or not on:
                continue
            # PAIRED: restrict both conditions to the steps scored in both, so the
            # delta is evidence-only and not a coverage artefact.
            shared = set(on) & set(hd) & set(L)
            if len(shared) < 50:
                continue
            c_on = cell_from(on, L, shared)
            c_hi = cell_from({k: v[0] for k, v in hd.items()}, L, shared)
            if c_on is None or c_hi is None:
                continue
            rng = np.random.default_rng(SEED)
            d, lo, hi = SM.boot_paired(c_hi, c_on, rng)
            rows.append({"dataset": ds, "target": tgt, "n": c_on.n,
                         "n_ep": c_on.n_ep,
                         "auroc_online": c_on.auroc(), "auroc_hindsight": c_hi.auroc(),
                         "delta": d, "ci_lo": lo, "ci_hi": hi,
                         "underpowered": int(c_on.underpowered)})
            # failure policy: online here vs banked S1a
            bank = os.path.join(a.banked, "S1a_crossprobe_L2_%s.csv"
                                % construct.replace("+", "-"))
            if os.path.exists(bank):
                for r in csv.DictReader(open(bank)):
                    if (r["dataset"], r["assessor"], r["target"]) == (ds, a.judge, tgt):
                        try:
                            b = float(r["auroc"])
                        except (TypeError, ValueError):
                            break
                        repro.append({"construct": construct, "dataset": ds,
                                      "target": tgt, "banked": b,
                                      "recomputed_full": None,
                                      "note": "paired subset, not directly comparable"})
                        break
        results[construct] = rows
        SM.write_csv(os.path.join(a.outdir, "S4_delta_%s.csv"
                                  % construct.replace("+", "-")), rows,
                     ["dataset", "target", "n", "n_ep", "auroc_online",
                      "auroc_hindsight", "delta", "ci_lo", "ci_hi", "underpowered"])
        ok = [r for r in rows if r["delta"] is not None and not r["underpowered"]]
        print("%-20s cells %2d  mean d %s" %
              (construct, len(ok),
               "n/a" if not ok else "%+.4f" % np.mean([r["delta"] for r in ok])),
              flush=True)

    # ---- (iii) R3 decomposition -----------------------------------------
    dec = []
    for construct in CONSTRUCTS:
        for r in results.get(construct, []):
            if r["delta"] is None:
                continue
            dec.append({"construct": construct, "dataset": r["dataset"],
                        "target": r["target"], "information_share": r["delta"]})
    SM.write_csv(os.path.join(a.outdir, "S4_information_share.csv"), dec,
                 ["construct", "dataset", "target", "information_share"])

    # ---- verdicts --------------------------------------------------------
    def verdict(construct, bar=0.0):
        rows = [r for r in results.get(construct, [])
                if r["delta"] is not None and not r["underpowered"]]
        if not rows:
            return None
        wins = sum(1 for r in rows if r["delta"] > bar)
        excl = sum(1 for r in rows
                   if r["ci_lo"] is not None and r["ci_lo"] > 0)
        return {"n": len(rows), "wins": wins, "ci_excl": excl,
                "mean": float(np.mean([r["delta"] for r in rows])),
                "max": float(np.max([r["delta"] for r in rows])),
                "min": float(np.min([r["delta"] for r in rows]))}

    v_out = verdict("outcome")
    v_vio = verdict("violation")
    L = ["# S4 SUMMARY — hindsight-ceiling pass (single judge)\n",
         "Spec: `%s` + the 2026-08-07 single-judge amendment.\n" % SPEC,
         "**Judge: %s only.** The Llama-3.3-70B half was dropped; the judge-agreement "
         "contrast is unobtainable and every result below is a single-model result.\n"
         % a.judge,
         "Construct labels L2, paired episode-clustered bootstrap, seed %d, %d draws. "
         "Each cell is restricted to the steps scored under BOTH evidence conditions, "
         "so the delta is evidence-only and not a coverage artefact.\n" % (SEED, NBOOT),
         "## Coverage\n",
         "| | |", "|---|---|"]
    im = [c for c in cov if c["in_matrix"]]
    L.append("| in-matrix arms | %d |" % len(im))
    L.append("| records | %s |" % "{:,}".format(sum(c["records"] for c in im)))
    L.append("| route=main | %s |" % "{:,}".format(sum(c["main"] for c in im)))
    L.append("| truncated | %d |" % sum(c["truncated"] for c in im))
    L.append("| failed | %d |" % sum(c["failed"] for c in im))
    L.append("| deferred (over-length) | %d |" % sum(c["deferred_long"] for c in im))
    L.append("")
    L.append("## (i) Hindsight − online ΔAUROC, per construct\n")
    L.append("| construct | cells | mean Δ | min | max | Δ>0 | CI excludes 0 |")
    L.append("|---|---|---|---|---|---|---|")
    for c in CONSTRUCTS:
        v = verdict(c)
        if not v:
            L.append("| %s | 0 | — | — | — | — | — |" % c)
            continue
        L.append("| %s | %d | %+.4f | %+.4f | %+.4f | %d/%d | %d |"
                 % (c, v["n"], v["mean"], v["min"], v["max"], v["wins"], v["n"],
                    v["ci_excl"]))
    L.append("")
    L.append("## Pre-registered predictions\n")
    if v_out:
        ph1 = "HOLDS" if (v_out["wins"] * 2 >= v_out["n"] and v_out["ci_excl"] > 0) \
            else "FAILS"
        L.append("**P-h1** — hindsight beats online on `outcome` in a majority of "
                 "cells with CI excluding 0: **%s** (%d/%d cells positive, %d with CI "
                 "excluding 0, mean %+.4f).\n"
                 % (ph1, v_out["wins"], v_out["n"], v_out["ci_excl"], v_out["mean"]))
    if v_vio:
        ph2 = "HOLDS" if v_vio["mean"] <= 0.01 else "FAILS"
        L.append("**P-h2** — hindsight does NOT beat online on `violation` by more "
                 "than 0.01: **%s** (mean %+.4f, max %+.4f). %s\n"
                 % (ph2, v_vio["mean"], v_vio["max"],
                    "" if ph2 == "HOLDS" else
                    "Hindsight helps violations substantially, so the "
                    "violation/outcome split is less clean than A30 claims — recorded "
                    "here as the spec requires."))
    L.append("**P-h3** — information share exceeds construct share on outcome strata "
             "and is smaller on violation strata: see "
             "`%s/S4_information_share.csv`; the online→hindsight movement at fixed "
             "labels is the information share, tabulated per construct above.\n"
             % a.outdir)
    L.append("## Limitation registered before results\n")
    L.append("One judge. A prediction that holds on %s is weaker evidence than the "
             "same prediction holding on two independent capable judges, and no "
             "verdict here may be read as though the contrast had been run.\n" % a.judge)
    L.append("## Tables\n")
    for f in sorted(os.listdir(a.outdir)):
        if f.endswith(".csv"):
            L.append("- `%s/%s`" % (a.outdir, f))
    L.append("")
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")
    print("-> %s, %s" % (a.outdir, a.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
