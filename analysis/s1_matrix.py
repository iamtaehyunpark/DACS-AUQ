#!/usr/bin/env python3
"""S1a/b/c — stratified crossprobe matrix, independence restatement, A30 §4 check.

Spec: docs/specs/S1_SPEC.md.  Label constructs come from s1_labels (one definition
site).  Scores come from the banked pivot through gate2b_cut_transfer's loaders, so
this shares the score path with the gate-2 arms rather than reimplementing it.

y = 1 means INCORRECT throughout.  No orientation flips (ground rule 4): U is always
"higher = more likely incorrect", and AUROC is computed in that direction everywhere.
"""
import argparse
import collections
import csv
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate2b_cut_transfer as G          # noqa: E402
import s1_labels as SL                   # noqa: E402

SPEC = "docs/specs/S1_SPEC.md"
SEED = 13
NBOOT = 2000
N_FLOOR = 100          # spec §0
MINORITY_FLOOR = 10    # spec §0
CAPABLE = G.CAPABLE


# ---------------------------------------------------------------- AUROC
def auroc_w(rows):
    """Weighted AUROC.  rows = [(u, y, w)].  Rank-based with tie correction:
    sum over positive/negative pairs of w_p*w_n*(1 if u_p>u_n else 0.5 if equal)."""
    pos = [(u, w) for u, y, w in rows if y == 1]
    neg = [(u, w) for u, y, w in rows if y == 0]
    if not pos or not neg:
        return None
    srt = sorted(rows, key=lambda r: r[0])
    # Sweep once: accumulate negative weight below and tied-with each positive.
    i = 0
    wneg_below = 0.0
    num = 0.0
    Wn = sum(w for _, w in neg)
    Wp = sum(w for _, w in pos)
    while i < len(srt):
        j = i
        while j < len(srt) and srt[j][0] == srt[i][0]:
            j += 1
        tie_pos = sum(w for _, y, w in srt[i:j] if y == 1)
        tie_neg = sum(w for _, y, w in srt[i:j] if y == 0)
        num += tie_pos * (wneg_below + 0.5 * tie_neg)
        wneg_below += tie_neg
        i = j
    return num / (Wp * Wn)


def boot_auroc(by_ep, rng, nboot=NBOOT):
    """Episode-clustered bootstrap: resample EPISODES, not steps.  Steps inside an
    episode are not independent, so a step-level bootstrap understates the CI."""
    eps = list(by_ep.values())
    if not eps:
        return None, None
    out = []
    n = len(eps)
    for _ in range(nboot):
        rows = []
        for _ in range(n):
            rows.extend(eps[rng.randrange(n)])
        a = auroc_w(rows)
        if a is not None:
            out.append(a)
    if not out:
        return None, None
    out.sort()
    return out[int(0.025 * len(out))], out[min(int(0.975 * len(out)), len(out) - 1)]


def boot_paired(by_ep_a, by_ep_b, rng, nboot=NBOOT):
    """CI on the PAIRED difference auroc(a) - auroc(b) over shared episodes.  The two
    arms score the same episodes, so resampling them independently would inflate the
    interval; episodes are drawn once and applied to both."""
    keys = sorted(set(by_ep_a) & set(by_ep_b))
    if not keys:
        return None, None, None
    base = None
    aa, ab = auroc_w([r for k in keys for r in by_ep_a[k]]), \
        auroc_w([r for k in keys for r in by_ep_b[k]])
    if aa is not None and ab is not None:
        base = aa - ab
    out = []
    n = len(keys)
    for _ in range(nboot):
        pick = [keys[rng.randrange(n)] for _ in range(n)]
        ra = [r for k in pick for r in by_ep_a[k]]
        rb = [r for k in pick for r in by_ep_b[k]]
        x, y = auroc_w(ra), auroc_w(rb)
        if x is not None and y is not None:
            out.append(x - y)
    if not out:
        return base, None, None
    out.sort()
    return base, out[int(0.025 * len(out))], out[min(int(0.975 * len(out)), len(out) - 1)]


# ---------------------------------------------------------------- collect
def collect(pivot, labels_by_arm, scope):
    """-> {(ds, assessor, target): {"by_ep": {ep: [(u,y,w)]}, ...}}"""
    cells = {}
    xp = os.path.join(pivot, "crossprobe")
    for ds in sorted(d for d in os.listdir(pivot)
                     if os.path.isdir(os.path.join(pivot, d)) and d != "crossprobe"):
        for tgt in sorted(os.listdir(os.path.join(pivot, ds))):
            tdir = os.path.join(pivot, ds, tgt)
            if not os.path.isdir(tdir):
                continue
            lab = labels_by_arm.get((ds, tgt))
            if not lab:
                continue
            src = {tgt: [os.path.join(tdir, "probes.jsonl"),
                         os.path.join(tdir, "probes.aggtrue.jsonl")]}
            for asr in G.assessors_in(os.path.join(xp, ds, tgt)):
                src[asr] = [os.path.join(xp, ds, tgt, "ptrue.%s.%s.jsonl" % (asr, p))
                            for p in ("stages", "response")]
            for asr, paths in src.items():
                pr = G.load_ptrue(paths)
                by_ep = collections.defaultdict(list)
                for key, v in pr.items():
                    yw = lab.get(key)
                    if yw is None:
                        continue
                    u, _said = G.scoped(v, scope)
                    if u is None:
                        continue
                    by_ep[key[0]].append((u, yw[0], yw[1]))
                flat = [r for rs in by_ep.values() for r in rs]
                if not flat:
                    continue
                npos = sum(1 for r in flat if r[1] == 1)
                cells[(ds, asr, tgt)] = {
                    "by_ep": dict(by_ep), "n": len(flat), "n_pos": npos,
                    "n_neg": len(flat) - npos, "n_ep": len(by_ep),
                    "self": asr == tgt, "capable": asr in CAPABLE,
                    "underpowered": (len(flat) < N_FLOOR
                                     or min(npos, len(flat) - npos) < MINORITY_FLOOR),
                }
    return cells


# ---------------------------------------------------------------- stages
def s1a(cells, rng):
    rows = []
    for (ds, asr, tgt), c in sorted(cells.items()):
        flat = [r for rs in c["by_ep"].values() for r in rs]
        a = auroc_w(flat)
        lo, hi = (None, None) if a is None else boot_auroc(c["by_ep"], rng)
        rows.append({"dataset": ds, "assessor": asr, "target": tgt,
                     "self": int(c["self"]), "capable": int(c["capable"]),
                     "n": c["n"], "n_pos": c["n_pos"], "n_neg": c["n_neg"],
                     "n_ep": c["n_ep"], "auroc": a, "ci_lo": lo, "ci_hi": hi,
                     "underpowered": int(c["underpowered"])})
    return rows


def s1b(cells, rng):
    """Per arm: best-self vs best-external, paired CI on the difference."""
    by_arm = collections.defaultdict(dict)
    for (ds, asr, tgt), c in cells.items():
        by_arm[(ds, tgt)][asr] = c
    rows = []
    for (ds, tgt), d in sorted(by_arm.items()):
        usable = {a: c for a, c in d.items() if not c["underpowered"]}
        selfc = usable.get(tgt)
        ext = {a: c for a, c in usable.items() if a != tgt}
        if not selfc or not ext:
            rows.append({"dataset": ds, "target": tgt, "best_external": "",
                         "self_auroc": None, "ext_auroc": None, "delta": None,
                         "ci_lo": None, "ci_hi": None, "n_ext_cells": len(ext),
                         "note": "no countable self or external cell"})
            continue
        scored = []
        for a, c in ext.items():
            v = auroc_w([r for rs in c["by_ep"].values() for r in rs])
            if v is not None:
                scored.append((v, a, c))
        if not scored:
            continue
        scored.sort(reverse=True)
        bv, ba, bc = scored[0]
        sv = auroc_w([r for rs in selfc["by_ep"].values() for r in rs])
        delta, lo, hi = boot_paired(bc["by_ep"], selfc["by_ep"], rng)
        rows.append({"dataset": ds, "target": tgt, "best_external": ba,
                     "self_auroc": sv, "ext_auroc": bv, "delta": delta,
                     "ci_lo": lo, "ci_hi": hi, "n_ext_cells": len(ext), "note": ""})
    return rows


def s1c_i(cells_vj, rng):
    """(i) capable external superiority intact on violation+judgment."""
    by_tgt = collections.defaultdict(dict)
    for (ds, asr, tgt), c in cells_vj.items():
        if asr == tgt or c["underpowered"]:
            continue
        by_tgt[(ds, tgt)][asr] = c
    wins = tot = 0
    diffs = []
    for (ds, tgt), d in sorted(by_tgt.items()):
        cap = {a: c for a, c in d.items() if a in CAPABLE}
        non = {a: c for a, c in d.items() if a not in CAPABLE}
        if not cap or not non:
            continue
        cv = max(auroc_w([r for rs in c["by_ep"].values() for r in rs]) for c in cap.values())
        nv = max(auroc_w([r for rs in c["by_ep"].values() for r in rs]) for c in non.values())
        tot += 1
        if cv >= nv:
            wins += 1
        bc = max(cap.values(), key=lambda c: auroc_w([r for rs in c["by_ep"].values() for r in rs]))
        bn = max(non.values(), key=lambda c: auroc_w([r for rs in c["by_ep"].values() for r in rs]))
        d0, lo, hi = boot_paired(bc["by_ep"], bn["by_ep"], rng)
        diffs.append({"dataset": ds, "target": tgt, "capable": cv, "noncapable": nv,
                      "delta": d0, "ci_lo": lo, "ci_hi": hi})
    pooled = [x["delta"] for x in diffs if x["delta"] is not None]
    plo = phi = None
    if pooled:
        b = []
        for _ in range(NBOOT):
            s = [pooled[rng.randrange(len(pooled))] for _ in range(len(pooled))]
            b.append(sum(s) / len(s))
        b.sort()
        plo, phi = b[int(0.025 * NBOOT)], b[int(0.975 * NBOOT)]
    if tot == 0:
        verdict = "UNDERPOWERED"
    elif wins / tot >= 2 / 3 and plo is not None and plo > 0:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {"verdict": verdict, "wins": wins, "total": tot,
            "pooled_delta": (sum(pooled) / len(pooled)) if pooled else None,
            "pooled_ci": [plo, phi], "cells": diffs}


def s1c_ii(cells_by_c, rng):
    """(ii) self-probe inflation confined to outcome strata: is (self - best-external)
    larger under `outcome` than under `violation+judgment`?"""
    def gaps(cells):
        by_arm = collections.defaultdict(dict)
        for (ds, asr, tgt), c in cells.items():
            if not c["underpowered"]:
                by_arm[(ds, tgt)][asr] = c
        out = {}
        for k, d in by_arm.items():
            ds, tgt = k
            if tgt not in d:
                continue
            ext = [(auroc_w([r for rs in c["by_ep"].values() for r in rs]), a)
                   for a, c in d.items() if a != tgt]
            ext = [e for e in ext if e[0] is not None]
            sv = auroc_w([r for rs in d[tgt]["by_ep"].values() for r in rs])
            if not ext or sv is None:
                continue
            out[k] = sv - max(ext)[0]
        return out
    go = gaps(cells_by_c["outcome"])
    gv = gaps(cells_by_c["violation+judgment"])
    shared = sorted(set(go) & set(gv))
    if not shared:
        return {"verdict": "UNDERPOWERED", "arms": 0, "larger": 0,
                "mean_dd": None, "ci": [None, None], "rows": []}
    dd = [go[k] - gv[k] for k in shared]
    larger = sum(1 for d in dd if d > 0)
    b = []
    for _ in range(NBOOT):
        s = [dd[rng.randrange(len(dd))] for _ in range(len(dd))]
        b.append(sum(s) / len(s))
    b.sort()
    lo, hi = b[int(0.025 * NBOOT)], b[int(0.975 * NBOOT)]
    verdict = ("PASS" if larger / len(dd) >= 2 / 3 and lo > 0 else "FAIL")
    return {"verdict": verdict, "arms": len(dd), "larger": larger,
            "mean_dd": sum(dd) / len(dd), "ci": [lo, hi],
            "rows": [{"dataset": k[0], "target": k[1], "gap_outcome": go[k],
                      "gap_viol_judg": gv[k], "dd": go[k] - gv[k]} for k in shared]}


# ---------------------------------------------------------------- io
def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else
                        (r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c])
                        for c in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--scope", default="AGG-true")
    ap.add_argument("--labelpass", default="L2")
    ap.add_argument("--outdir", default="tables_S1")
    ap.add_argument("--constructs", default=",".join(SL.CONSTRUCTS))
    a = ap.parse_args()

    constructs = [c for c in a.constructs.split(",") if c]
    cells_by_c = {}
    summary = {"stage": "S1", "spec": SPEC, "scope": a.scope,
               "labelpass": a.labelpass, "seed": SEED, "constructs": {}}

    for c in constructs:
        rng = random.Random(SEED)          # same draws per construct: comparable CIs
        lab = SL.load(a.labels, c, in_matrix_only=True)
        cells = collect(a.pivot, lab, a.scope)
        cells_by_c[c] = cells
        rows = s1a(cells, rng)
        write_csv(os.path.join(a.outdir, "S1a_crossprobe_%s_%s.csv" % (a.labelpass, c)),
                  rows, ["dataset", "assessor", "target", "self", "capable", "n",
                         "n_pos", "n_neg", "n_ep", "auroc", "ci_lo", "ci_hi",
                         "underpowered"])
        ind = s1b(cells, rng)
        write_csv(os.path.join(a.outdir, "S1b_independence_%s_%s.csv" % (a.labelpass, c)),
                  ind, ["dataset", "target", "best_external", "self_auroc",
                        "ext_auroc", "delta", "ci_lo", "ci_hi", "n_ext_cells", "note"])
        ok = [r for r in rows if not r["underpowered"] and r["auroc"] is not None]
        summary["constructs"][c] = {
            "cells": len(rows), "underpowered": sum(r["underpowered"] for r in rows),
            "countable": len(ok),
            "mean_auroc": (sum(r["auroc"] for r in ok) / len(ok)) if ok else None,
            "independence_rows": len(ind),
        }
        print("%-20s cells %3d  countable %3d  underpowered %3d  mean AUROC %s"
              % (c, len(rows), len(ok), sum(r["underpowered"] for r in rows),
                 "%.4f" % summary["constructs"][c]["mean_auroc"]
                 if ok else "n/a"))

    if "violation+judgment" in cells_by_c:
        rng = random.Random(SEED)
        ci = s1c_i(cells_by_c["violation+judgment"], rng)
        summary["A30_pred_i"] = {k: v for k, v in ci.items() if k != "cells"}
        write_csv(os.path.join(a.outdir, "S1c_pred_i_%s.csv" % a.labelpass), ci["cells"],
                  ["dataset", "target", "capable", "noncapable", "delta", "ci_lo", "ci_hi"])
        print("A30 (i) capable-external superiority on violation+judgment: %s "
              "(%d/%d cells, pooled delta %s CI [%s, %s])"
              % (ci["verdict"], ci["wins"], ci["total"],
                 "%.4f" % ci["pooled_delta"] if ci["pooled_delta"] is not None else "n/a",
                 "%.4f" % ci["pooled_ci"][0] if ci["pooled_ci"][0] is not None else "n/a",
                 "%.4f" % ci["pooled_ci"][1] if ci["pooled_ci"][1] is not None else "n/a"))
        if "outcome" in cells_by_c:
            rng = random.Random(SEED)
            cii = s1c_ii(cells_by_c, rng)
            summary["A30_pred_ii"] = {k: v for k, v in cii.items() if k != "rows"}
            write_csv(os.path.join(a.outdir, "S1c_pred_ii_%s.csv" % a.labelpass),
                      cii["rows"], ["dataset", "target", "gap_outcome",
                                    "gap_viol_judg", "dd"])
            print("A30 (ii) self-inflation confined to outcome strata: %s "
                  "(%d/%d arms, mean dd %s CI [%s, %s])"
                  % (cii["verdict"], cii["larger"], cii["arms"],
                     "%.4f" % cii["mean_dd"] if cii["mean_dd"] is not None else "n/a",
                     "%.4f" % cii["ci"][0] if cii["ci"][0] is not None else "n/a",
                     "%.4f" % cii["ci"][1] if cii["ci"][1] is not None else "n/a"))

    os.makedirs(a.outdir, exist_ok=True)
    with open(os.path.join(a.outdir, "S1abc_%s.json" % a.labelpass), "w") as f:
        json.dump(summary, f, indent=1)
    print("-> %s" % a.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
