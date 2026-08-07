#!/usr/bin/env python3
"""Priority-3 free stages: S7.1, bootstrap ladder, CI top-up.

EXECUTION_HANDOVER v2 §3.  All CPU, all on banked data, no GPU.

  a. S7.1 — prequential replay with h (and h-noself) in place of g, same seeds and
     orderings as S7; plus the gate-2 tier table restated under h.
  b. bootstrap ladder — day-one violation-calibrated / ~200-label tier / steady-state
     h, with labels required, label source, time-to-deploy, and capture+BA per
     construct.
  c. CI top-up — bootstrap intervals for GATE-3/4 headline numbers that lack one,
     appended to the S2 claim registry with claim-sentence IDs.
"""
import argparse
import bisect
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

SEED = 13
NBOOT = 2000
WARMUP = 100
SEEDS = list(range(13, 23))
CAPABLE = sorted(G.CAPABLE)
CONSTRUCTS = ["violation+judgment", "judgment", "violation", "outcome", "y_env"]
FLATNESS = 8.0


# ---------------------------------------------------------------- shared
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


def boot_mean(v, rng, nboot=NBOOT):
    v = np.asarray([x for x in v if x is not None], float)
    if v.size == 0:
        return None, None, None
    b = np.array([v[rng.integers(0, v.size, v.size)].mean() for _ in range(nboot)])
    return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975))


def build(scores, lab):
    out = {}
    for (ds, asr, tgt), d in scores.items():
        if asr not in CAPABLE:
            continue
        L = lab.get((ds, tgt))
        if not L:
            continue
        us, ys, eps = [], [], []
        for k, v in d.items():
            u = v[0] if isinstance(v, tuple) else v
            yw = L.get(k)
            if yw is not None:
                us.append(u); ys.append(yw[0]); eps.append(k[0])
        if len(us) >= 50 and len(set(ys)) > 1:
            out[(ds, asr, tgt)] = (np.array(us), np.array(ys), eps)
    return out


def fit_h_for(cells, ds, asr, drop_self=False):
    pts = []
    for (e, a_, t), (us, ys, _e) in cells.items():
        if e != ds or a_ != asr:
            continue
        if drop_self and t == asr:
            continue
        p, _ = best_cut_pct(us, ys)
        if p is not None:
            pts.append((float(us.mean()), p))
    return ols([p[0] for p in pts], [p[1] for p in pts])


# ---------------------------------------------------------------- (a) S7.1
def prequential(us, ys, eps, h, prior_pct, seed):
    """Past-only replay: cut from h(mean of scores seen so far) at each step."""
    rng = np.random.default_rng(seed)
    by_ep = collections.defaultdict(list)
    for u, y, e in zip(us, ys, eps):
        by_ep[e].append((u, y))
    keys = list(by_ep)
    order = rng.permutation(len(keys))
    seen, total = [], 0.0
    n = 0
    warm, post = [], []
    for i in order:
        for u, y in by_ep[keys[i]]:
            if n < WARMUP or not seen:
                cut = prior_pct
            else:
                pct = min(max(h[0] * (total / n) + h[1], 0.0), 1.0)
                pos = pct * (len(seen) - 1)
                lo = int(pos); hi = min(lo + 1, len(seen) - 1)
                cut = seen[lo] + (pos - lo) * (seen[hi] - seen[lo])
            (warm if n < WARMUP else post).append((u >= cut, y))
            bisect.insort(seen, u); total += u; n += 1
    def ba(pairs):
        tp = sum(1 for f, y in pairs if y == 1 and f)
        fn = sum(1 for f, y in pairs if y == 1 and not f)
        tn = sum(1 for f, y in pairs if y == 0 and not f)
        fp = sum(1 for f, y in pairs if y == 0 and f)
        if tp + fn == 0 or tn + fp == 0:
            return None
        return 0.5 * (tp / (tp + fn) + tn / (tn + fp))
    return ba(warm + post), ba(post)


def stage_a(cells, outdir):
    rows = []
    for variant, drop in (("h", False), ("h-noself", True)):
        for (ds, asr, tgt), (us, ys, eps) in sorted(cells.items()):
            h = fit_h_for({k: v for k, v in cells.items() if k[2] != tgt},
                          ds, asr, drop_self=drop)
            if h is None:
                continue
            pct_b = min(max(h[0] * float(us.mean()) + h[1], 0.0), 1.0)
            batch = bal_acc(us, ys, float(np.quantile(us, pct_b)))
            prior = float(np.quantile(us, pct_b))
            incl, post = [], []
            for s in SEEDS:
                i_, p_ = prequential(us, ys, eps, h, prior, s)
                if i_ is not None:
                    incl.append(i_)
                if p_ is not None:
                    post.append(p_)
            if not incl or batch is None:
                continue
            rows.append({"variant": variant, "dataset": ds, "assessor": asr,
                         "target": tgt, "n": len(us), "batch_ba": batch,
                         "incl_mean": float(np.mean(incl)),
                         "post_mean": float(np.mean(post)) if post else None,
                         "penalty_post": (float(np.mean(post)) - batch) if post else None,
                         "penalty_incl": float(np.mean(incl)) - batch})
    _w(os.path.join(outdir, "S71_prequential_h.csv"), rows,
       ["variant", "dataset", "assessor", "target", "n", "batch_ba", "incl_mean",
        "post_mean", "penalty_post", "penalty_incl"])
    return rows


# ---------------------------------------------------------------- (b) ladder
def stage_b(scores, labels_csv, outdir, rng):
    """Three deployment tiers, costed."""
    rows = []
    for construct in CONSTRUCTS:
        lab = SL.load(labels_csv, construct, in_matrix_only=True)
        viol = SL.load(labels_csv, "violation", in_matrix_only=True)
        cells = build(scores, lab)
        cap = {k: v for k, v in cells.items() if k[1] in CAPABLE}
        tiers = collections.defaultdict(list)
        for (ds, asr, tgt), (us, ys, eps) in cap.items():
            V = None
            fitted_pct, fitted_ba = best_cut_pct(us, ys)
            # day-one: violation-calibrated on the target's own automatic labels
            VL = viol.get((ds, tgt)) or {}
            d = scores.get((ds, asr, tgt)) or {}
            vu, vy = [], []
            for k, v in d.items():
                u = v[0] if isinstance(v, tuple) else v
                yw = VL.get(k)
                vu.append(u); vy.append(1 if (yw is not None and yw[0] == 1) else 0)
            day1 = None
            if len(set(vy)) > 1:
                c, _ = best_cut_pct(vu, vy)
                if c is not None:
                    day1 = bal_acc(us, ys, float(np.quantile(vu, c)))
            # steady state: h fitted on other targets
            h = fit_h_for({k: v for k, v in cells.items() if k[2] != tgt}, ds, asr)
            hba = None
            if h is not None:
                p = min(max(h[0] * float(us.mean()) + h[1], 0.0), 1.0)
                hba = bal_acc(us, ys, float(np.quantile(us, p)))
            tiers["day1_violation_calibrated"].append(day1)
            tiers["label_200_fitted"].append(fitted_ba)
            tiers["steady_state_h"].append(hba)
        meta = {
            "day1_violation_calibrated":
                ("0 human labels", "environment emits automatically", "immediate"),
            "label_200_fitted":
                ("~200 labelled episodes on the target", "human or judge ensemble",
                 "one labelling round"),
            "steady_state_h":
                ("0 labels on the target", "other targets of same judge x env",
                 "immediate once h exists"),
        }
        for tier, vals in tiers.items():
            m, lo, hi = boot_mean(vals, rng)
            lbl, src, tt = meta[tier]
            rows.append({"construct": construct, "tier": tier, "labels_required": lbl,
                         "label_source": src, "time_to_deploy": tt,
                         "cells": sum(1 for v in vals if v is not None),
                         "mean_ba": m, "ci_lo": lo, "ci_hi": hi})
    _w(os.path.join(outdir, "bootstrap_ladder.csv"), rows,
       ["construct", "tier", "labels_required", "label_source", "time_to_deploy",
        "cells", "mean_ba", "ci_lo", "ci_hi"])
    return rows


# ---------------------------------------------------------------- (c) CI top-up
def stage_c(outdir, rng):
    rows = []
    g3 = "tables_gate3/gate3_cells_violation-judgment.csv"
    if os.path.exists(g3):
        cells = [r for r in csv.DictReader(open(g3)) if r["capable"] == "yes"]
        for arm, cid in (("arm0_h_rule", "C-h-passrate"),
                         ("arm2_violation", "C-viol-passrate")):
            flags, gains, dens = [], [], []
            for r in cells:
                try:
                    V = float(r["V"]); F = float(r["S_fitted"]); A = float(r[arm])
                except (ValueError, KeyError):
                    continue
                flags.append(A >= V)
                if F - V > 0.01:
                    gains.append(A - V); dens.append(F - V)
            if flags:
                v = np.array([1.0 if f else 0.0 for f in flags])
                b = np.array([v[rng.integers(0, v.size, v.size)].mean()
                              for _ in range(NBOOT)])
                rows.append({"claim_id": cid, "quantity": "%s pass-rate vs V" % arm,
                             "estimate": float(v.mean()),
                             "ci_lo": float(np.quantile(b, .025)),
                             "ci_hi": float(np.quantile(b, .975)),
                             "null_value": 0.80, "n": len(flags),
                             "source": g3})
            if gains:
                gv, dv = np.array(gains), np.array(dens)
                bb = []
                for _ in range(NBOOT):
                    i = rng.integers(0, gv.size, gv.size)
                    if dv[i].sum() != 0:
                        bb.append(gv[i].sum() / dv[i].sum())
                bb = np.array(bb)
                rows.append({"claim_id": cid.replace("passrate", "capture"),
                             "quantity": "%s pooled capture" % arm,
                             "estimate": float(gv.sum() / dv.sum()),
                             "ci_lo": float(np.quantile(bb, .025)),
                             "ci_hi": float(np.quantile(bb, .975)),
                             "null_value": 0.50, "n": len(gains), "source": g3})
    g4 = "tables_gate4/D_cross_env_h.csv"
    if os.path.exists(g4):
        d = [float(r["delta"]) for r in csv.DictReader(open(g4)) if r["delta"]]
        m, lo, hi = boot_mean(d, rng)
        rows.append({"claim_id": "C-crossenv-h", "quantity":
                     "cross-environment h degradation", "estimate": m, "ci_lo": lo,
                     "ci_hi": hi, "null_value": 0.0, "n": len(d), "source": g4})
    for r in rows:
        r["status"] = ("soften" if (r["ci_lo"] is not None and
                                    r["ci_lo"] <= r["null_value"] <= r["ci_hi"])
                       else "ok")
    _w(os.path.join(outdir, "S2_ci_registry_topup.csv"), rows,
       ["claim_id", "quantity", "estimate", "ci_lo", "ci_hi", "null_value", "n",
        "source", "status"])
    return rows


def _w(path, rows, cols):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else
                        (r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c])
                        for c in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="runs/score_cache_AGG-true.pkl")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--outdir", default="tables_P3")
    ap.add_argument("--summary", default="P3_SUMMARY.md")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rng = np.random.default_rng(SEED)
    scores = pickle.load(open(a.cache, "rb"))

    lab = SL.load(a.labels, "violation+judgment", in_matrix_only=True)
    cells = build(scores, lab)
    print("P3: %d capable cells" % len(cells), flush=True)

    A = stage_a(cells, a.outdir)
    print("S7.1: %d rows" % len(A), flush=True)
    B = stage_b(scores, a.labels, a.outdir, rng)
    print("ladder: %d rows" % len(B), flush=True)
    C = stage_c(a.outdir, rng)
    print("CI top-up: %d claims" % len(C), flush=True)

    L = ["# Priority-3 free stages — S7.1, bootstrap ladder, CI top-up\n",
         "Spec: EXECUTION_HANDOVER v2 §3. Seed %d, %d draws, construct primary "
         "violation+judgment unless stated.\n" % (SEED, NBOOT),
         "## S7.1 — prequential replay under h (and h-noself)\n",
         "| variant | cells | mean batch BA | mean post-warm-up | mean penalty |",
         "|---|---|---|---|---|"]
    for variant in ("h", "h-noself"):
        rs = [r for r in A if r["variant"] == variant and r["penalty_post"] is not None]
        if rs:
            L.append("| %s | %d | %.4f | %.4f | %+.4f |"
                     % (variant, len(rs), np.mean([r["batch_ba"] for r in rs]),
                        np.mean([r["post_mean"] for r in rs]),
                        np.mean([r["penalty_post"] for r in rs])))
    L.append("")
    L.append("## Bootstrap ladder — what each deployment tier costs and buys\n")
    L.append("| construct | tier | labels required | source | time to deploy | cells | mean BA | 95% CI |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in B:
        L.append("| %s | %s | %s | %s | %s | %d | %s | %s |"
                 % (r["construct"], r["tier"], r["labels_required"],
                    r["label_source"], r["time_to_deploy"], r["cells"],
                    "n/a" if r["mean_ba"] is None else "%.4f" % r["mean_ba"],
                    "n/a" if r["ci_lo"] is None else
                    "[%.4f, %.4f]" % (r["ci_lo"], r["ci_hi"])))
    L.append("")
    L.append("## CI top-up — GATE-3/4 headlines that lacked intervals\n")
    L.append("| claim | estimate | 95% CI | null | status |")
    L.append("|---|---|---|---|---|")
    for r in C:
        L.append("| %s — %s | %s | %s | %.2f | **%s** |"
                 % (r["claim_id"], r["quantity"],
                    "n/a" if r["estimate"] is None else "%.4f" % r["estimate"],
                    "n/a" if r["ci_lo"] is None else
                    "[%.4f, %.4f]" % (r["ci_lo"], r["ci_hi"]),
                    r["null_value"], r["status"]))
    L.append("")
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")
    print("-> %s, %s" % (a.outdir, a.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
