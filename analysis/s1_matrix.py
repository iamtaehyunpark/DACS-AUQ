#!/usr/bin/env python3
"""S1a/b/c — stratified crossprobe matrix, independence restatement, A30 §4 check.

Spec: docs/specs/S1_SPEC.md.  Label constructs come from s1_labels (one definition
site).  Scores come from the banked pivot through gate2b_cut_transfer's loaders, so
this shares the score path with the gate-2 arms rather than reimplementing it.

y = 1 means INCORRECT throughout.  No orientation flips (ground rule 4): U is always
"higher = more likely incorrect", and AUROC is computed in that direction everywhere.

PERFORMANCE, because it changes what is feasible rather than just how fast it is:
  * Scores are read ONCE for all constructs.  The pivot is 31 GB; re-reading it per
    construct made the stage I/O-bound five times over.
  * The episode-clustered bootstrap is vectorised.  2000 draws x 61 cells x 5
    constructs with a per-draw sort is ~1e11 operations and does not finish; here
    each cell is sorted once and a draw is a bincount over episode multiplicities,
    which is O(n) in numpy.  Same estimator, same seed, same draws.
"""
import argparse
import collections
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate2b_cut_transfer as G          # noqa: E402
import s1_labels as SL                   # noqa: E402

SPEC = "docs/specs/S1_SPEC.md"
SEED = 13
NBOOT = 2000
N_FLOOR = 100          # spec §0
MINORITY_FLOOR = 10    # spec §0
CAPABLE = G.CAPABLE


class Cell(object):
    """Pre-sorted scores + episode index for one (dataset, assessor, target)."""

    __slots__ = ("u", "y", "w", "ep", "g", "n_ep", "n", "n_pos", "n_neg",
                 "self_", "capable", "underpowered", "ep_keys")

    def __init__(self, rows):
        rows.sort(key=lambda r: r[0])
        self.u = np.array([r[0] for r in rows], dtype=np.float64)
        self.y = np.array([r[1] for r in rows], dtype=np.int8)
        self.w = np.array([r[2] for r in rows], dtype=np.float64)
        eps = sorted({r[3] for r in rows})
        idx = {e: i for i, e in enumerate(eps)}
        self.ep = np.array([idx[r[3]] for r in rows], dtype=np.int64)
        self.ep_keys = eps
        self.n_ep = len(eps)
        # tie groups: equal scores share a group, so ties get the 0.5 credit
        _, self.g = np.unique(self.u, return_inverse=True)
        self.n = len(rows)
        self.n_pos = int((self.y == 1).sum())
        self.n_neg = self.n - self.n_pos
        self.underpowered = (self.n < N_FLOOR
                             or min(self.n_pos, self.n_neg) < MINORITY_FLOOR)

    def auroc(self, eff_w=None):
        w = self.w if eff_w is None else eff_w
        wp = np.where(self.y == 1, w, 0.0)
        wn = np.where(self.y == 0, w, 0.0)
        Wp, Wn = wp.sum(), wn.sum()
        if Wp <= 0 or Wn <= 0:
            return None
        k = self.g.max() + 1
        tp = np.bincount(self.g, weights=wp, minlength=k)
        tn = np.bincount(self.g, weights=wn, minlength=k)
        below = np.concatenate(([0.0], np.cumsum(tn)[:-1]))
        return float((tp * (below + 0.5 * tn)).sum() / (Wp * Wn))

    def eff_w(self, mult):
        return self.w * mult[self.ep]


def boot_ci(cell, rng, nboot=NBOOT):
    """Episode-clustered bootstrap: resample EPISODES, not steps.  Steps inside an
    episode are not independent, so a step-level bootstrap understates the CI."""
    if cell.n_ep < 2:
        return None, None
    out = []
    for _ in range(nboot):
        mult = np.bincount(rng.integers(0, cell.n_ep, cell.n_ep),
                           minlength=cell.n_ep).astype(np.float64)
        a = cell.auroc(cell.eff_w(mult))
        if a is not None:
            out.append(a)
    if not out:
        return None, None
    out = np.sort(np.array(out))
    return float(np.quantile(out, 0.025)), float(np.quantile(out, 0.975))


def boot_paired(ca, cb, rng, nboot=NBOOT):
    """CI on the PAIRED difference auroc(a) - auroc(b) over shared episodes.  The two
    arms score the same episodes, so resampling them independently would inflate the
    interval and make a real difference look null."""
    shared = sorted(set(ca.ep_keys) & set(cb.ep_keys))
    if len(shared) < 2:
        return None, None, None
    ia = {e: i for i, e in enumerate(ca.ep_keys)}
    ib = {e: i for i, e in enumerate(cb.ep_keys)}
    sa = np.array([ia[e] for e in shared])
    sb = np.array([ib[e] for e in shared])
    # restrict both cells to the shared episodes via a 0/1 multiplicity vector
    ma = np.zeros(ca.n_ep); ma[sa] = 1.0
    mb = np.zeros(cb.n_ep); mb[sb] = 1.0
    base_a, base_b = ca.auroc(ca.eff_w(ma)), cb.auroc(cb.eff_w(mb))
    base = None if base_a is None or base_b is None else base_a - base_b
    out = []
    n = len(shared)
    for _ in range(nboot):
        pick = rng.integers(0, n, n)
        cnt = np.bincount(pick, minlength=n).astype(np.float64)
        ma = np.zeros(ca.n_ep); ma[sa] = cnt
        mb = np.zeros(cb.n_ep); mb[sb] = cnt
        x, y = ca.auroc(ca.eff_w(ma)), cb.auroc(cb.eff_w(mb))
        if x is not None and y is not None:
            out.append(x - y)
    if not out:
        return base, None, None
    out = np.array(out)
    return base, float(np.quantile(out, 0.025)), float(np.quantile(out, 0.975))


def boot_mean(vals, rng, nboot=NBOOT):
    if not vals:
        return None, None, None
    v = np.array(vals, dtype=np.float64)
    n = len(v)
    b = np.array([v[rng.integers(0, n, n)].mean() for _ in range(nboot)])
    return float(v.mean()), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))


# ---------------------------------------------------------------- scores
def load_scores(pivot, scope, cache=None):
    """{(ds, assessor, target): {(task_id, step_idx): u}} — read once, reused by
    every construct.

    Parsing the pivot costs ~30 min (31 GB of JSONL), and S1's L1 reproduction pass,
    S2 and every other scope need the same scores.  The cache makes that a one-time
    cost.  It is keyed by scope and stores only (key -> u), never a derived quantity,
    so a stale cache cannot silently change a result — and the manifest's sha256 pins
    are what detect upstream drift.
    """
    if cache and os.path.exists(cache):
        import pickle
        with open(cache, "rb") as f:
            out = pickle.load(f)
        print("S1: score cache hit %s (%d cells)" % (cache, len(out)), flush=True)
        return out
    out = {}
    xp = os.path.join(pivot, "crossprobe")
    for ds in sorted(d for d in os.listdir(pivot)
                     if os.path.isdir(os.path.join(pivot, d)) and d != "crossprobe"):
        for tgt in sorted(os.listdir(os.path.join(pivot, ds))):
            tdir = os.path.join(pivot, ds, tgt)
            if not os.path.isdir(tdir):
                continue
            src = {tgt: [os.path.join(tdir, "probes.jsonl"),
                         os.path.join(tdir, "probes.aggtrue.jsonl")]}
            for asr in G.assessors_in(os.path.join(xp, ds, tgt)):
                src[asr] = [os.path.join(xp, ds, tgt, "ptrue.%s.%s.jsonl" % (asr, p))
                            for p in ("stages", "response")]
            for asr, paths in src.items():
                pr = G.load_ptrue(paths)
                d = {}
                for key, v in pr.items():
                    u, _said = G.scoped(v, scope)
                    if u is not None:
                        d[key] = u
                if d:
                    out[(ds, asr, tgt)] = d
            print("  scores %s/%s: %d assessors" % (ds, tgt, len(src)), flush=True)
    if cache:
        import pickle
        tmp = cache + ".tmp"
        with open(tmp, "wb") as f:
            pickle.dump(out, f, protocol=4)
        os.replace(tmp, cache)   # atomic: a killed run never leaves a half cache
        print("S1: score cache written %s" % cache, flush=True)
    return out


def build_cells(scores, labels_by_arm, construct=""):
    """Join scores to labels, and REFUSE to return a silently empty matrix.

    A key-type mismatch produces zero matched rows per cell, and a cell with zero
    rows just does not appear -- the table then looks clean while missing a whole
    dataset.  Any arm that has both scores and labels but joins nothing is a hard
    error here, because there is no benign reason for it."""
    cells = {}
    empty = []
    for (ds, asr, tgt), d in scores.items():
        lab = labels_by_arm.get((ds, tgt))
        if not lab:
            continue
        rows = []
        for key, u in d.items():
            yw = lab.get(key)
            if yw is not None:
                rows.append((u, yw[0], yw[1], key[0]))
        if not rows:
            empty.append((ds, asr, tgt, len(d), len(lab)))
            continue
        c = Cell(rows)
        c.self_ = asr == tgt
        c.capable = asr in CAPABLE
        cells[(ds, asr, tgt)] = c
    if empty:
        msg = ["%s: %d cells have scores AND labels but joined 0 rows "
               "(key-type mismatch?)" % (construct or "build_cells", len(empty))]
        for ds, asr, tgt, ns, nl in empty[:10]:
            msg.append("  %s %s -> %s : %d scored steps, %d labelled steps"
                       % (ds, asr, tgt, ns, nl))
        raise SystemExit("\n".join(msg))
    return cells


# ---------------------------------------------------------------- stages
def s1a(cells, rng):
    rows = []
    for (ds, asr, tgt), c in sorted(cells.items()):
        a = c.auroc()
        lo, hi = (None, None) if a is None else boot_ci(c, rng)
        rows.append({"dataset": ds, "assessor": asr, "target": tgt,
                     "self": int(c.self_), "capable": int(c.capable),
                     "n": c.n, "n_pos": c.n_pos, "n_neg": c.n_neg, "n_ep": c.n_ep,
                     "auroc": a, "ci_lo": lo, "ci_hi": hi,
                     "underpowered": int(c.underpowered)})
    return rows


def _best_external(d, tgt):
    scored = []
    for a, c in d.items():
        if a == tgt or c.underpowered:
            continue
        v = c.auroc()
        if v is not None:
            scored.append((v, a, c))
    if not scored:
        return None
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0]


def s1b(cells, rng):
    by_arm = collections.defaultdict(dict)
    for (ds, asr, tgt), c in cells.items():
        by_arm[(ds, tgt)][asr] = c
    rows = []
    for (ds, tgt), d in sorted(by_arm.items()):
        sc = d.get(tgt)
        be = _best_external(d, tgt)
        if sc is None or sc.underpowered or be is None:
            rows.append({"dataset": ds, "target": tgt, "best_external": "",
                         "self_auroc": None, "ext_auroc": None, "delta": None,
                         "ci_lo": None, "ci_hi": None,
                         "n_ext": sum(1 for a in d if a != tgt),
                         "note": "no countable self or external cell"})
            continue
        bv, ba, bc = be
        delta, lo, hi = boot_paired(bc, sc, rng)
        rows.append({"dataset": ds, "target": tgt, "best_external": ba,
                     "self_auroc": sc.auroc(), "ext_auroc": bv, "delta": delta,
                     "ci_lo": lo, "ci_hi": hi,
                     "n_ext": sum(1 for a in d if a != tgt), "note": ""})
    return rows


def s1c_i(cells, rng):
    """(i) capable external superiority intact on violation+judgment."""
    by_tgt = collections.defaultdict(dict)
    for (ds, asr, tgt), c in cells.items():
        if asr != tgt and not c.underpowered:
            by_tgt[(ds, tgt)][asr] = c
    wins = tot = 0
    out = []
    deltas = []
    for (ds, tgt), d in sorted(by_tgt.items()):
        cap = [(c.auroc(), a, c) for a, c in d.items() if a in CAPABLE]
        non = [(c.auroc(), a, c) for a, c in d.items() if a not in CAPABLE]
        cap = [x for x in cap if x[0] is not None]
        non = [x for x in non if x[0] is not None]
        if not cap or not non:
            continue
        cap.sort(key=lambda t: t[0], reverse=True)
        non.sort(key=lambda t: t[0], reverse=True)
        tot += 1
        if cap[0][0] >= non[0][0]:
            wins += 1
        d0, lo, hi = boot_paired(cap[0][2], non[0][2], rng)
        if d0 is not None:
            deltas.append(d0)
        out.append({"dataset": ds, "target": tgt, "capable_best": cap[0][1],
                    "noncapable_best": non[0][1], "capable": cap[0][0],
                    "noncapable": non[0][0], "delta": d0, "ci_lo": lo, "ci_hi": hi})
    mean, plo, phi = boot_mean(deltas, rng)
    if tot == 0:
        verdict = "UNDERPOWERED"
    elif wins / tot >= 2 / 3 and plo is not None and plo > 0:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {"verdict": verdict, "wins": wins, "total": tot, "pooled_delta": mean,
            "pooled_ci": [plo, phi], "cells": out}


def s1c_ii(cells_by_c, rng):
    """(ii) self-probe inflation confined to outcome strata."""
    def gaps(cells):
        by_arm = collections.defaultdict(dict)
        for (ds, asr, tgt), c in cells.items():
            by_arm[(ds, tgt)][asr] = c
        out = {}
        for (ds, tgt), d in by_arm.items():
            sc = d.get(tgt)
            be = _best_external(d, tgt)
            if sc is None or sc.underpowered or be is None:
                continue
            sv = sc.auroc()
            if sv is not None:
                out[(ds, tgt)] = sv - be[0]
        return out
    go, gv = gaps(cells_by_c["outcome"]), gaps(cells_by_c["violation+judgment"])
    shared = sorted(set(go) & set(gv))
    if not shared:
        return {"verdict": "UNDERPOWERED", "arms": 0, "larger": 0,
                "mean_dd": None, "ci": [None, None], "rows": []}
    dd = [go[k] - gv[k] for k in shared]
    larger = sum(1 for x in dd if x > 0)
    mean, lo, hi = boot_mean(dd, rng)
    verdict = "PASS" if (larger / len(dd) >= 2 / 3 and lo is not None and lo > 0) else "FAIL"
    return {"verdict": verdict, "arms": len(dd), "larger": larger, "mean_dd": mean,
            "ci": [lo, hi],
            "rows": [{"dataset": k[0], "target": k[1], "gap_outcome": go[k],
                      "gap_viol_judg": gv[k], "dd": go[k] - gv[k]} for k in shared]}


# ---------------------------------------------------------------- io
def write_csv(path, rows, cols):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else
                        (r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c])
                        for c in cols])


def fmt(x, p="%.4f"):
    return "n/a" if x is None else p % x


def main():
    global NBOOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--scope", default="AGG-true")
    ap.add_argument("--labelpass", default="L2")
    ap.add_argument("--outdir", default="tables_S1")
    ap.add_argument("--constructs", default=",".join(SL.CONSTRUCTS))
    ap.add_argument("--nboot", type=int, default=NBOOT)
    ap.add_argument("--score-cache", default="runs/score_cache_{scope}.pkl",
                    help="{scope} is substituted; empty string disables")
    a = ap.parse_args()

    NBOOT = a.nboot
    constructs = [c for c in a.constructs.split(",") if c]
    os.makedirs(a.outdir, exist_ok=True)

    print("S1: loading scores once (scope=%s) ..." % a.scope, flush=True)
    cache = a.score_cache.replace("{scope}", a.scope) if a.score_cache else None
    if cache:
        os.makedirs(os.path.dirname(cache) or ".", exist_ok=True)
    scores = load_scores(a.pivot, a.scope, cache)
    print("S1: %d score cells" % len(scores), flush=True)

    cells_by_c = {}
    summary = {"stage": "S1", "spec": SPEC, "scope": a.scope, "seed": SEED,
               "labelpass": a.labelpass, "nboot": NBOOT, "constructs": {}}

    for c in constructs:
        rng = np.random.default_rng(SEED)   # same draws per construct
        lab = SL.load(a.labels, c, in_matrix_only=True)
        cells = build_cells(scores, lab, c)
        cells_by_c[c] = cells
        rows = s1a(cells, rng)
        write_csv(os.path.join(a.outdir, "S1a_crossprobe_%s_%s.csv"
                               % (a.labelpass, c.replace("+", "-"))), rows,
                  ["dataset", "assessor", "target", "self", "capable", "n", "n_pos",
                   "n_neg", "n_ep", "auroc", "ci_lo", "ci_hi", "underpowered"])
        ind = s1b(cells, rng)
        write_csv(os.path.join(a.outdir, "S1b_independence_%s_%s.csv"
                               % (a.labelpass, c.replace("+", "-"))), ind,
                  ["dataset", "target", "best_external", "self_auroc", "ext_auroc",
                   "delta", "ci_lo", "ci_hi", "n_ext", "note"])
        ok = [r for r in rows if not r["underpowered"] and r["auroc"] is not None]
        summary["constructs"][c] = {
            "cells": len(rows), "countable": len(ok),
            "underpowered": sum(r["underpowered"] for r in rows),
            "mean_auroc": (sum(r["auroc"] for r in ok) / len(ok)) if ok else None}
        print("%-20s cells %3d  countable %3d  underpowered %3d  mean AUROC %s"
              % (c, len(rows), len(ok), sum(r["underpowered"] for r in rows),
                 fmt(summary["constructs"][c]["mean_auroc"])), flush=True)

    if "violation+judgment" in cells_by_c:
        rng = np.random.default_rng(SEED)
        ci = s1c_i(cells_by_c["violation+judgment"], rng)
        summary["A30_pred_i"] = {k: v for k, v in ci.items() if k != "cells"}
        write_csv(os.path.join(a.outdir, "S1c_pred_i_%s.csv" % a.labelpass), ci["cells"],
                  ["dataset", "target", "capable_best", "noncapable_best", "capable",
                   "noncapable", "delta", "ci_lo", "ci_hi"])
        print("A30 (i) capable-external superiority [violation+judgment]: %s  "
              "%d/%d cells, pooled delta %s CI [%s, %s]"
              % (ci["verdict"], ci["wins"], ci["total"], fmt(ci["pooled_delta"]),
                 fmt(ci["pooled_ci"][0]), fmt(ci["pooled_ci"][1])), flush=True)
        if "outcome" in cells_by_c:
            rng = np.random.default_rng(SEED)
            cii = s1c_ii(cells_by_c, rng)
            summary["A30_pred_ii"] = {k: v for k, v in cii.items() if k != "rows"}
            write_csv(os.path.join(a.outdir, "S1c_pred_ii_%s.csv" % a.labelpass),
                      cii["rows"],
                      ["dataset", "target", "gap_outcome", "gap_viol_judg", "dd"])
            print("A30 (ii) self-inflation confined to outcome: %s  %d/%d arms, "
                  "mean dd %s CI [%s, %s]"
                  % (cii["verdict"], cii["larger"], cii["arms"], fmt(cii["mean_dd"]),
                     fmt(cii["ci"][0]), fmt(cii["ci"][1])), flush=True)

    with open(os.path.join(a.outdir, "S1abc_%s.json" % a.labelpass), "w") as f:
        json.dump(summary, f, indent=1)
    print("-> %s" % a.outdir, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
