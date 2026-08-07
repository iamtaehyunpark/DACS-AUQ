#!/usr/bin/env python3
"""GATE-4 (A34) Parts B, C, D — mechanism, stability, cross-environment boundary.

Spec: docs/specs/GATE4_SPEC_A34.md.  These parts need no GPU and no forecast lock, so
they run alongside Part A's scoring pass.

  B  conditional-invariance overlay: are f(u|correct) and f(u|incorrect) the same
     shape across targets within a (judge, env)?  That invariance is what h
     presupposes.  Criterion: median within-class between-target 1-Wasserstein
     distance < 1/3 of the class-separation distance.  Self-cells are plotted but
     EXCLUDED from the criterion -- known self-leniency shifts the conditionals, so
     their deviation is a positive control rather than a failure.
  C  fit-stability: jackknife the h fit by dropping each reference target, and report
     the swing in predicted percentile against the +-8 point flatness budget.  Answers
     the small-m objection with numbers rather than assurances.
  D  family granularity: fit h on one environment, apply to the other.  Expected to
     degrade; the number is the measured boundary of "per environment family".

Everything is per (judge, environment).  No cross-environment pooling except Part D,
whose purpose is to measure cross-environment failure (spec §0).
"""
import argparse
import collections
import csv
import json
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate2b_cut_transfer as G          # noqa: E402
import s1_labels as SL                   # noqa: E402

SPEC = "docs/specs/GATE4_SPEC_A34.md"
SEED = 13
NBOOT = 2000
CAPABLE = sorted(G.CAPABLE)
FLATNESS = 8.0          # percentile points (spec §A.5 / §C)
EPS = 1e-4


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def wasserstein1(a, b):
    """1-D 1-Wasserstein via inverse-CDF quadrature on a shared grid."""
    a = np.sort(np.asarray(a, dtype=float))
    b = np.sort(np.asarray(b, dtype=float))
    if a.size == 0 or b.size == 0:
        return None
    q = np.linspace(0, 1, 512)
    return float(np.mean(np.abs(np.quantile(a, q) - np.quantile(b, q))))


def best_cut_pct(us, ys):
    """Balanced-accuracy-optimal cut, returned as a PERCENTILE of the target's own
    score distribution -- the quantity h predicts."""
    us = np.asarray(us, dtype=float); ys = np.asarray(ys)
    if len(set(ys.tolist())) < 2:
        return None, None
    o = np.argsort(us)
    su, sy = us[o], ys[o]
    P, N = int((sy == 1).sum()), int((sy == 0).sum())
    tp = P - np.cumsum(sy == 1) + (sy == 1)
    tn = np.cumsum(sy == 0) - (sy == 0)
    ba = 0.5 * (tp / P + tn / N)
    i = int(np.argmax(ba))
    thr = float(su[i])
    return float((us < thr).mean()), float(ba[i])


def ols(xs, ys):
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    if len(xs) < 2 or len(set(xs.tolist())) < 2:
        return None
    b = ((xs - xs.mean()) * (ys - ys.mean())).sum() / ((xs - xs.mean()) ** 2).sum()
    return b, ys.mean() - b * xs.mean()


def build(scores, lab):
    """{(env, judge, target): (us, ys)} for capable judges, in-matrix targets."""
    out = {}
    for (ds, asr, tgt), d in scores.items():
        if asr not in CAPABLE:
            continue
        L = lab.get((ds, tgt))
        if not L:
            continue
        us, ys = [], []
        for k, v in d.items():
            u = v[0] if isinstance(v, tuple) else v
            yw = L.get(k)
            if yw is not None:
                us.append(u); ys.append(yw[0])
        if len(us) >= 50 and len(set(ys)) > 1:
            out[(ds, asr, tgt)] = (np.array(us), np.array(ys))
    return out


# ------------------------------------------------------------------ Part B
def part_b(cells, outdir):
    rows, verdicts = [], []
    for env in sorted({k[0] for k in cells}):
        for judge in CAPABLE:
            sel = {k[2]: v for k, v in cells.items() if k[0] == env and k[1] == judge}
            if len(sel) < 3:
                continue
            cond = {}
            for tgt, (us, ys) in sel.items():
                cond[tgt] = (logit(us[ys == 0]), logit(us[ys == 1]))   # correct, incorrect
            # class separation: median over targets of W1(correct, incorrect)
            sep = [wasserstein1(c, i) for c, i in cond.values()]
            sep = [s for s in sep if s is not None]
            sep_med = float(np.median(sep)) if sep else None
            # within-class between-target distances, self-cells EXCLUDED (spec §B)
            ext = [t for t in cond if t != judge]
            within = []
            for ci, cls in ((0, "correct"), (1, "incorrect")):
                for i, a in enumerate(ext):
                    for b in ext[i + 1:]:
                        d = wasserstein1(cond[a][ci], cond[b][ci])
                        if d is not None:
                            within.append(d)
                            rows.append({"env": env, "judge": judge, "class": cls,
                                         "target_a": a, "target_b": b, "w1": d})
            # self-cell distances reported as the positive control
            for ci, cls in ((0, "correct"), (1, "incorrect")):
                if judge in cond:
                    for b in ext:
                        d = wasserstein1(cond[judge][ci], cond[b][ci])
                        if d is not None:
                            rows.append({"env": env, "judge": judge,
                                         "class": cls + "_SELF", "target_a": judge,
                                         "target_b": b, "w1": d})
            wmed = float(np.median(within)) if within else None
            ok = (wmed is not None and sep_med and wmed < sep_med / 3.0)
            verdicts.append({"env": env, "judge": judge, "within_median": wmed,
                             "class_separation": sep_med,
                             "ratio": (wmed / sep_med) if (wmed and sep_med) else None,
                             "CI_supported": "yes" if ok else "no",
                             "n_targets_ext": len(ext)})
    _w(os.path.join(outdir, "B_wasserstein_pairs.csv"), rows,
       ["env", "judge", "class", "target_a", "target_b", "w1"])
    _w(os.path.join(outdir, "B_invariance_verdict.csv"), verdicts,
       ["env", "judge", "within_median", "class_separation", "ratio",
        "CI_supported", "n_targets_ext"])
    return verdicts


# ------------------------------------------------------------------ Part C
def part_c(cells, outdir, rng):
    rows, summary = [], []
    for env in sorted({k[0] for k in cells}):
        for judge in CAPABLE:
            sel = {k[2]: v for k, v in cells.items() if k[0] == env and k[1] == judge}
            pts = {}
            for tgt, (us, ys) in sel.items():
                pct, _ba = best_cut_pct(us, ys)
                if pct is not None:
                    pts[tgt] = (float(us.mean()), pct)
            if len(pts) < 3:
                continue
            names = sorted(pts)
            full = ols([pts[t][0] for t in names], [pts[t][1] for t in names])
            if full is None:
                continue
            # jackknife: drop each reference target, refit, predict at every other
            max_swing = 0.0
            swings = []
            leverage = []
            for drop in names:
                keep = [t for t in names if t != drop]
                f = ols([pts[t][0] for t in keep], [pts[t][1] for t in keep])
                if f is None:
                    continue
                worst = 0.0
                for t in keep:
                    p_full = full[0] * pts[t][0] + full[1]
                    p_jack = f[0] * pts[t][0] + f[1]
                    sw = abs(p_full - p_jack) * 100.0     # percentile points
                    swings.append(sw)
                    worst = max(worst, sw)
                    rows.append({"env": env, "judge": judge, "dropped": drop,
                                 "at_target": t, "swing_pts": sw})
                max_swing = max(max_swing, worst)
                if worst > FLATNESS:
                    leverage.append("%s(%.1f)" % (drop, worst))
            # pairs bootstrap on slope/intercept
            xs = np.array([pts[t][0] for t in names])
            ys = np.array([pts[t][1] for t in names])
            bs, bi = [], []
            for _ in range(NBOOT):
                i = rng.integers(0, len(names), len(names))
                f = ols(xs[i], ys[i])
                if f:
                    bs.append(f[0]); bi.append(f[1])
            summary.append({
                "env": env, "judge": judge, "n_targets": len(names),
                "slope": full[0], "intercept": full[1],
                "slope_lo": float(np.quantile(bs, .025)) if bs else None,
                "slope_hi": float(np.quantile(bs, .975)) if bs else None,
                "max_jackknife_swing_pts": max_swing,
                "median_swing_pts": float(np.median(swings)) if swings else None,
                "stable": "yes" if max_swing <= FLATNESS else "no",
                "leverage_targets": ";".join(leverage)})
    _w(os.path.join(outdir, "C_jackknife_swings.csv"), rows,
       ["env", "judge", "dropped", "at_target", "swing_pts"])
    _w(os.path.join(outdir, "C_fit_stability.csv"), summary,
       ["env", "judge", "n_targets", "slope", "intercept", "slope_lo", "slope_hi",
        "max_jackknife_swing_pts", "median_swing_pts", "stable", "leverage_targets"])
    return summary


# ------------------------------------------------------------------ Part D
def part_d(cells, outdir):
    """Fit h on one env, apply to the other.  No success criterion (spec §D)."""
    fits, pts_by = {}, {}
    for env in sorted({k[0] for k in cells}):
        for judge in CAPABLE:
            pts = {}
            for (e, j, t), (us, ys) in cells.items():
                if e != env or j != judge:
                    continue
                pct, _ = best_cut_pct(us, ys)
                if pct is not None:
                    pts[t] = (float(us.mean()), pct)
            if len(pts) >= 3:
                fits[(env, judge)] = ols([p[0] for p in pts.values()],
                                         [p[1] for p in pts.values()])
                pts_by[(env, judge)] = pts
    rows = []
    for (env, judge), f in fits.items():
        other = "hotpotqa" if env == "alfworld" else "alfworld"
        if (other, judge) not in fits or f is None:
            continue
        for (e, j, t), (us, ys) in sorted(cells.items()):
            if e != other or j != judge:
                continue
            own = fits[(other, judge)]
            def ba_at(fit):
                pct = min(max(fit[0] * float(us.mean()) + fit[1], 0.0), 1.0)
                cut = float(np.quantile(us, pct))
                flag = us >= cut
                P, N = ys == 1, ys == 0
                if P.sum() == 0 or N.sum() == 0:
                    return None
                return float(0.5 * ((flag & P).sum() / P.sum()
                                    + (~flag & N).sum() / N.sum()))
            cross, within = ba_at(f), ba_at(own)
            rows.append({"judge": judge, "fit_env": env, "applied_env": other,
                         "target": t, "ba_cross": cross, "ba_within": within,
                         "delta": (cross - within) if (cross is not None
                                                       and within is not None) else None})
    _w(os.path.join(outdir, "D_cross_env_h.csv"), rows,
       ["judge", "fit_env", "applied_env", "target", "ba_cross", "ba_within", "delta"])
    return rows


def _w(path, rows, cols):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else
                        (r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c])
                        for c in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="runs/score_cache_v2_AGG-true.pkl")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--construct", default="violation+judgment")
    ap.add_argument("--outdir", default="tables_gate4")
    ap.add_argument("--summary", default="GATE4_BCD_PARTIAL.md")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rng = np.random.default_rng(SEED)

    scores = pickle.load(open(a.cache, "rb"))
    lab = SL.load(a.labels, a.construct, in_matrix_only=True)
    cells = build(scores, lab)
    print("gate4 B/C/D: %d capable cells, construct=%s" % (len(cells), a.construct))

    B = part_b(cells, a.outdir)
    C = part_c(cells, a.outdir, rng)
    D = part_d(cells, a.outdir)

    L = ["# GATE-4 Parts B/C/D (Part A pending scoring pass)\n",
         "Spec: `%s`. Construct **%s**, capable judges, per (judge, environment).\n"
         % (SPEC, a.construct),
         "## Part B — conditional invariance\n",
         "Criterion: median within-class between-target 1-Wasserstein < 1/3 of the "
         "class-separation distance. Self-cells excluded (positive control).\n",
         "| env | judge | within-median | class-separation | ratio | CI supported |",
         "|---|---|---|---|---|---|"]
    for r in B:
        L.append("| %s | %s | %s | %s | %s | **%s** |"
                 % (r["env"], r["judge"],
                    "n/a" if r["within_median"] is None else "%.3f" % r["within_median"],
                    "n/a" if r["class_separation"] is None else "%.3f" % r["class_separation"],
                    "n/a" if r["ratio"] is None else "%.3f" % r["ratio"],
                    r["CI_supported"]))
    L.append("")
    L.append("## Part C — fit stability (disclosure, not a gate)\n")
    L.append("Stable iff max jackknife swing <= %.0f percentile points in >=3 of 4 fits.\n"
             % FLATNESS)
    L.append("| env | judge | targets | slope | slope 95% CI | max swing (pts) | "
             "median swing | stable | leverage |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in C:
        L.append("| %s | %s | %d | %.3f | [%s, %s] | %.1f | %s | **%s** | %s |"
                 % (r["env"], r["judge"], r["n_targets"], r["slope"],
                    "n/a" if r["slope_lo"] is None else "%.3f" % r["slope_lo"],
                    "n/a" if r["slope_hi"] is None else "%.3f" % r["slope_hi"],
                    r["max_jackknife_swing_pts"],
                    "n/a" if r["median_swing_pts"] is None else "%.1f" % r["median_swing_pts"],
                    r["stable"], r["leverage_targets"] or "—"))
    n_stable = sum(1 for r in C if r["stable"] == "yes")
    L.append("\n**%d of %d fits stable** (criterion: >=3 of 4).\n" % (n_stable, len(C)))
    L.append("## Part D — cross-environment h (no success criterion; expected to degrade)\n")
    L.append("| judge | fit env | applied to | target | BA cross | BA within | delta |")
    L.append("|---|---|---|---|---|---|---|")
    for r in D:
        L.append("| %s | %s | %s | %s | %s | %s | %s |"
                 % (r["judge"], r["fit_env"], r["applied_env"], r["target"],
                    "n/a" if r["ba_cross"] is None else "%.3f" % r["ba_cross"],
                    "n/a" if r["ba_within"] is None else "%.3f" % r["ba_within"],
                    "n/a" if r["delta"] is None else "%+.3f" % r["delta"]))
    ds = [r["delta"] for r in D if r["delta"] is not None]
    if ds:
        L.append("\nMean cross-environment degradation **%+.3f** balanced accuracy "
                 "(min %+.3f, max %+.3f), over %d cells. This number is the measured "
                 "boundary of \"per environment family\" and goes verbatim into the "
                 "limitations section.\n"
                 % (float(np.mean(ds)), min(ds), max(ds), len(ds)))
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")
    print("-> %s, %s" % (a.outdir, a.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
