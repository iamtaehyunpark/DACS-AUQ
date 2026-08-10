#!/usr/bin/env python3
"""GATE-4 Part A — forecast-first validation on untouched targets.

Spec: docs/specs/GATE4_SPEC_A34.md, plus A34.1 (h-noself registered secondary).

Two modes, and the ORDER IS THE EVIDENCE:

  --seal      compute forecasts from h / h-noself and the forecast targets' UNLABELED
              mean-U, write forecasts_A34.csv, and STOP.  No label of any forecast
              target is read in this mode -- the loader is never even given a label
              file.  Commit the CSV; its sha and the commit timestamp are the proof
              that the prediction preceded the answer.
  --evaluate  read the sealed CSV, then read labels, score realised percentile and BA,
              and emit the verdicts.  Refuses to run unless the sealed CSV exists.

h        : OLS(optimal percentile ~ mean-U) over the reference targets of that
           (judge, environment), refit on the full reference set -- no LOTO needed
           because the forecast targets are outside it (spec A.3).
h-noself : identical, with the assessor's OWN cell dropped from the reference set.
           Registered after Part C found the self-cell carries 11.7 points of
           leverage on alfworld/Qwen3.6, which is where self-leniency is known to
           shift the class conditionals.
"""
import argparse
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
FLATNESS = 8.0            # percentile points, the registered tolerance band
FORECAST = [("alfworld", "Qwen3.5-4B"), ("alfworld", "Qwen3.5-9B"),
            ("alfworld", "Qwen3.5-27B"), ("hotpotqa", "Qwen3.5-4B"),
            ("hotpotqa", "Qwen3.5-9B")]
EXTRAPOLATION = {("alfworld", "Qwen3.5-27B")}   # larger than any reference target


def load_ptrue_cell(pivot, ds, target, assessor, scope="AGG-true"):
    """Unlabeled scores for one (assessor -> target) cell."""
    xp = os.path.join(pivot, "crossprobe", ds, target)
    paths = [os.path.join(xp, "ptrue.%s.%s.jsonl" % (assessor, p))
             for p in ("stages", "response")]
    pr = G.load_ptrue(paths)
    out = {}
    for k, v in pr.items():
        u, _ = G.scoped(v, scope)
        if u is not None:
            out[k] = u
    return out


def best_cut_pct(us, ys):
    us = np.asarray(us, float); ys = np.asarray(ys)
    if len(set(ys.tolist())) < 2:
        return None, None
    o = np.argsort(us); su, sy = us[o], ys[o]
    P, N = int((sy == 1).sum()), int((sy == 0).sum())
    tp = P - np.cumsum(sy == 1) + (sy == 1)
    tn = np.cumsum(sy == 0) - (sy == 0)
    ba = 0.5 * (tp / P + tn / N)
    i = int(np.argmax(ba))
    return float((us < float(su[i])).mean()), float(ba[i])


def bal_acc(us, ys, thr):
    us = np.asarray(us); ys = np.asarray(ys)
    flag = us >= thr
    P, N = ys == 1, ys == 0
    if P.sum() == 0 or N.sum() == 0:
        return None
    return float(0.5 * ((flag & P).sum() / P.sum() + (~flag & N).sum() / N.sum()))


def ols(xs, ys):
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    if len(xs) < 2 or len(set(xs.tolist())) < 2:
        return None
    b = ((xs - xs.mean()) * (ys - ys.mean())).sum() / ((xs - xs.mean()) ** 2).sum()
    return float(b), float(ys.mean() - b * xs.mean())


def reference_points(pivot, labels_csv, construct, judge, env):
    """(target -> (mean_u, optimal_pct, flatness_curve)) over REFERENCE targets only.

    Reference targets are the in-matrix ones -- the same set every gate fitted on.
    Forecast targets are excluded by construction: they are not in_matrix.
    """
    lab = SL.load(labels_csv, construct, in_matrix_only=True)
    out = {}
    for (ds, tgt) in sorted(lab):
        if ds != env:
            continue
        us_map = load_ptrue_cell(pivot, ds, tgt, judge)
        if not us_map:
            continue
        L = lab[(ds, tgt)]
        us, ys = [], []
        for k, u in us_map.items():
            yw = L.get(k)
            if yw is not None:
                us.append(u); ys.append(yw[0])
        if len(us) < 50 or len(set(ys)) < 2:
            continue
        pct, ba = best_cut_pct(us, ys)
        if pct is None:
            continue
        # flatness curve: BA as a function of cut percentile, for the predicted-BA band
        curve = {}
        for p in range(1, 100):
            curve[p] = bal_acc(us, ys, float(np.quantile(us, p / 100.0)))
        out[tgt] = {"mean_u": float(np.mean(us)), "pct": pct, "ba": ba,
                    "curve": curve, "n": len(us)}
    return out


def fit_h(refs, drop_self_for=None):
    pts = [(v["mean_u"], v["pct"]) for t, v in refs.items() if t != drop_self_for]
    return ols([p[0] for p in pts], [p[1] for p in pts]), \
        sorted(t for t in refs if t != drop_self_for)


def predicted_ba(refs, pct, exclude=None):
    """Mean reference BA at the forecast percentile, with a +-FLATNESS band."""
    p = int(round(pct * 100))
    p = min(max(p, 1), 99)
    vals, lo_vals, hi_vals = [], [], []
    for t, v in refs.items():
        if exclude and t == exclude:
            continue
        c = v["curve"]
        if c.get(p) is not None:
            vals.append(c[p])
        band = [c[q] for q in range(max(1, p - int(FLATNESS)),
                                    min(99, p + int(FLATNESS)) + 1)
                if c.get(q) is not None]
        if band:
            lo_vals.append(min(band)); hi_vals.append(max(band))
    if not vals:
        return None, None, None
    return (float(np.mean(vals)),
            float(np.mean(lo_vals)) if lo_vals else None,
            float(np.mean(hi_vals)) if hi_vals else None)


def do_seal(a):
    """NO LABELS OF FORECAST TARGETS ARE READ HERE."""
    rows = []
    missing = []
    for judge in CAPABLE:
        for env in ("alfworld", "hotpotqa"):
            refs = reference_points(a.pivot, a.labels, a.construct, judge, env)
            if len(refs) < 3:
                continue
            for variant, drop in (("h", None), ("h-noself", judge)):
                fit, used = fit_h(refs, drop_self_for=drop)
                if fit is None:
                    continue
                for (ds, tgt) in FORECAST:
                    if ds != env:
                        continue
                    us_map = load_ptrue_cell(a.pivot, ds, tgt, judge)
                    if not us_map:
                        missing.append("%s/%s/%s" % (judge, ds, tgt))
                        continue
                    us = np.array(list(us_map.values()), dtype=float)
                    mu = float(us.mean())
                    pct = float(min(max(fit[0] * mu + fit[1], 0.0), 1.0))
                    cut = float(np.quantile(us, pct))
                    ba, lo, hi = predicted_ba(refs, pct, exclude=drop)
                    rows.append({
                        "variant": variant, "judge": judge, "dataset": ds,
                        "target": tgt, "construct": a.construct,
                        "n_scores": len(us), "mean_u": mu,
                        "slope": fit[0], "intercept": fit[1],
                        "reference_targets": ";".join(used),
                        "pi_hat": pct, "cut": cut,
                        "ba_hat": ba, "ba_lo": lo, "ba_hi": hi,
                        "extrapolation": int((ds, tgt) in EXTRAPOLATION)})
    if missing:
        sys.exit("SEAL ABORTED — scores absent for %d forecast cells: %s\n"
                 "Spec A.2 is blocking: partial forecasting invites selection."
                 % (len(missing), ", ".join(sorted(set(missing)))))
    cols = ["variant", "judge", "dataset", "target", "construct", "n_scores",
            "mean_u", "slope", "intercept", "reference_targets", "pi_hat", "cut",
            "ba_hat", "ba_lo", "ba_hi", "extrapolation"]
    with open(a.forecasts, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows:
            w.writerow([r[c] if isinstance(r[c], (str, int)) else
                        ("" if r[c] is None else "%.6f" % r[c]) for c in cols])
    print("SEALED %d forecasts -> %s" % (len(rows), a.forecasts))
    print("  variants: h, h-noself   judges: %s" % ", ".join(CAPABLE))
    print("  NO forecast-target labels were read in this mode.")
    print("  COMMIT THIS FILE NOW; its sha and timestamp are the lock.")
    return 0


def do_evaluate(a):
    """Score the SEALED cuts against every construct.

    The forecast is a fixed number per cell; the construct only changes the yardstick
    it is measured against. Evaluating all of them touches nothing in the lock, and it
    is what recovers the 27B extrapolation cell: the judge ensemble never ran on that
    arm, so `judgment` is empty and the violation+judgment composite collapses to a
    single class -- but violation / outcome / y_env are environment-labelled and fully
    evaluable there.
    """
    if not os.path.exists(a.forecasts):
        sys.exit("No sealed forecasts at %s — run --seal first." % a.forecasts)
    sealed = list(csv.DictReader(open(a.forecasts)))
    rows = []
    for construct in [c.strip() for c in a.eval_constructs.split(",") if c.strip()]:
        lab = SL.load(a.labels, construct, in_matrix_only=False)
        rows.extend(_eval_one(a, sealed, lab, construct))
    cols = list(sealed[0].keys()) + ["eval_construct", "n", "n_pos", "n_neg",
                                     "realised_pct", "ba_at_cut", "ba_star", "V",
                                     "note"]
    os.makedirs(a.outdir, exist_ok=True)
    p = os.path.join(a.outdir, "A_forecast_evaluation.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("evaluated %d rows (%d cells x %d constructs) -> %s"
          % (len(rows), len(sealed), len(a.eval_constructs.split(",")), p))
    return 0


def _eval_one(a, sealed, lab, construct):
    rows = []
    for r in sealed:
        ds, tgt, judge = r["dataset"], r["target"], r["judge"]
        us_map = load_ptrue_cell(a.pivot, ds, tgt, judge)
        L = lab.get((ds, tgt)) or {}
        us, ys = [], []
        for k, u in us_map.items():
            yw = L.get(k)
            if yw is not None:
                us.append(u); ys.append(yw[0])
        npos = sum(1 for y in ys if y == 1)
        if len(us) < 50 or len(set(ys)) < 2:
            rows.append(dict(r, eval_construct=construct, n=len(us), n_pos=npos,
                             n_neg=len(ys) - npos, realised_pct="", ba_at_cut="",
                             ba_star="", V="",
                             note="single class under this construct"))
            continue
        pct_star, ba_star = best_cut_pct(us, ys)
        ba_cut = bal_acc(us, ys, float(r["cut"]))
        # V anchor: the argmax verdict on the same steps
        pr = G.load_ptrue([os.path.join(a.pivot, "crossprobe", ds, tgt,
                                        "ptrue.%s.%s.jsonl" % (judge, p))
                           for p in ("stages", "response")])
        vv, vy = [], []
        for k, v in pr.items():
            u, said = G.scoped(v, "AGG-true")
            yw = L.get(k)
            if u is not None and said is not None and yw is not None:
                vv.append(said); vy.append(yw[0])
        V = None
        if vv and len(set(vy)) > 1:
            vv = np.array(vv); vy = np.array(vy)
            P, N = vy == 1, vy == 0
            if P.sum() and N.sum():
                V = float(0.5 * (((vv == 1) & P).sum() / P.sum()
                                 + ((vv == 0) & N).sum() / N.sum()))
        rows.append(dict(r, eval_construct=construct, n=len(us), n_pos=npos,
                         n_neg=len(ys) - npos, realised_pct="%.6f" % pct_star,
                         ba_at_cut="" if ba_cut is None else "%.6f" % ba_cut,
                         ba_star="%.6f" % ba_star,
                         V="" if V is None else "%.6f" % V,
                         note=""))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--construct", default="violation+judgment")
    ap.add_argument("--forecasts", default="forecasts_A34.csv")
    ap.add_argument("--outdir", default="tables_gate4")
    ap.add_argument("--eval-constructs",
                    default="violation+judgment,judgment,violation,outcome,y_env")
    ap.add_argument("--seal", action="store_true")
    ap.add_argument("--evaluate", action="store_true")
    a = ap.parse_args()
    if a.seal == a.evaluate:
        sys.exit("choose exactly one of --seal / --evaluate")
    return do_seal(a) if a.seal else do_evaluate(a)


if __name__ == "__main__":
    raise SystemExit(main())
