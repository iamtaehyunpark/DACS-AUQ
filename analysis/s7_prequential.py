#!/usr/bin/env python3
"""S7 — prequential replay of the label-free cut.

Spec: docs/specs/S7_SPEC.md.  Measures the COST OF GOING ONLINE, not whether the
rule works: S1d put the batch g-rule at G2b1-R3 FAIL on the A30-primary construct,
and a sequential form cannot rescue a batch rule it is strictly harder than.  Each
cell is compared against the batch g-rule ON THE SAME CONSTRUCT, whatever its verdict.

S7 has no gate and may not be used to revisit a G2b1 verdict (ground rule 2).
"""
import argparse
import collections
import csv
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate2b_cut_transfer as G          # noqa: E402
import s1_labels as SL                   # noqa: E402

SPEC = "docs/specs/S7_SPEC.md"
WARMUP = 100          # spec §3
SEEDS = list(range(13, 23))   # 10 orderings, spec §6
CAPABLE = G.CAPABLE
PCLIP = (0.02, 0.98)


def bal_acc(pairs):
    """pairs = [(flagged, y)] with y=1 incorrect.  Balanced accuracy."""
    tp = sum(1 for f, y in pairs if y == 1 and f)
    fn = sum(1 for f, y in pairs if y == 1 and not f)
    tn = sum(1 for f, y in pairs if y == 0 and not f)
    fp = sum(1 for f, y in pairs if y == 0 and f)
    if (tp + fn) == 0 or (tn + fp) == 0:
        return None
    return 0.5 * (tp / (tp + fn) + tn / (tn + fp))


def fit_g(points):
    """OLS of true error rate on mean score, one point per other target (macro)."""
    if len(points) < 2:
        return None
    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)
    if len(set(xs.tolist())) < 2:
        return None
    b = ((xs - xs.mean()) * (ys - ys.mean())).sum() / ((xs - xs.mean()) ** 2).sum()
    return b, ys.mean() - b * xs.mean()


def batch_g_cut(scores, ghat):
    """The A28.1 batch rule: p-hat from g(mean of ALL scores), cut at that percentile
    of the FULL frozen distribution.  This is the comparator, reproduced here so the
    penalty is measured against the same estimator rather than a re-derived one."""
    if ghat is None or not scores:
        return None, None
    b, c = ghat
    p = min(max(b * float(np.mean(scores)) + c, PCLIP[0]), PCLIP[1])
    return float(np.quantile(scores, 1.0 - p)), p


def run_cell(rows_by_ep, ghat, seed):
    """One prequential pass.  rows_by_ep: {episode: [(u, y), ...]} in step order.

    Past-only throughout: the cut applied to step t is computed from steps < t only.
    Nothing is revisited, and no statistic ever sees a future score.
    """
    rng = np.random.default_rng(seed)
    eps = list(rows_by_ep)
    order = rng.permutation(len(eps))
    seen = []                       # past scores
    warm_pairs, post_pairs = [], []
    trace = []
    n = 0
    for i in order:
        for u, y in rows_by_ep[eps[i]]:
            # --- decide with past-only state -----------------------------
            if n < WARMUP or not seen:
                cut = prior_cut                    # noqa: F821 (bound by caller)
                phat = prior_p                     # noqa: F821
            else:
                b, c = ghat if ghat else (0.0, float(np.mean(seen)))
                phat = min(max(b * float(np.mean(seen)) + c, PCLIP[0]), PCLIP[1])
                cut = float(np.quantile(seen, 1.0 - phat))
            flagged = (cut is not None) and (u >= cut)
            (warm_pairs if n < WARMUP else post_pairs).append((flagged, y))
            trace.append((n, phat, cut))
            # --- only now does the step enter the past --------------------
            seen.append(u)
            n += 1
    return warm_pairs, post_pairs, trace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="runs/score_cache_AGG-true.pkl")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--constructs", default="violation+judgment,judgment")
    ap.add_argument("--outdir", default="tables_S7")
    ap.add_argument("--summary", default="S7_SUMMARY.md")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    if not os.path.exists(a.cache):
        raise SystemExit("S7: score cache absent (%s) — run s1_matrix first" % a.cache)
    scores = pickle.load(open(a.cache, "rb"))

    all_rows, summary_lines = [], []
    for construct in [c for c in a.constructs.split(",") if c]:
        lab = SL.load(a.labels, construct, in_matrix_only=True)
        # assemble per-cell step lists
        cells = {}
        for (ds, asr, tgt), d in scores.items():
            if asr not in CAPABLE:
                continue
            L = lab.get((ds, tgt))
            if not L:
                continue
            by_ep = collections.defaultdict(list)
            for (task, step), u in sorted(d.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
                yw = L.get((task, step))
                if yw is not None:
                    by_ep[task].append((u, yw[0]))
            if by_ep:
                cells[(ds, asr, tgt)] = dict(by_ep)

        # g is fitted on the OTHER targets of the same assessor x dataset, exactly as
        # A28.1 does, and is never refitted on the stream.
        stats = {}
        for k, by_ep in cells.items():
            flat = [r for rs in by_ep.values() for r in rs]
            stats[k] = (float(np.mean([u for u, _ in flat])),
                        float(np.mean([y for _, y in flat])), flat)

        rows = []
        for (ds, asr, tgt), by_ep in sorted(cells.items()):
            pool = [(stats[k][0], stats[k][1]) for k in cells
                    if k[0] == ds and k[1] == asr and k[2] != tgt]
            if len(pool) < 3:                 # A28 cell-counting rule
                continue
            ghat = fit_g(pool)
            flat = stats[(ds, asr, tgt)][2]
            us = [u for u, _ in flat]
            bcut, bp = batch_g_cut(us, ghat)
            batch = bal_acc([(u >= bcut, y) for u, y in flat]) if bcut is not None else None

            # prior cut from the pool, used during warm-up
            pool_us = [u for k in cells if k[0] == ds and k[1] == asr and k[2] != tgt
                       for u, _ in stats[k][2]]
            pool_p = float(np.mean([stats[k][1] for k in cells
                                    if k[0] == ds and k[1] == asr and k[2] != tgt]))
            global prior_cut, prior_p
            prior_p = min(max(pool_p, PCLIP[0]), PCLIP[1])
            prior_cut = float(np.quantile(pool_us, 1.0 - prior_p)) if pool_us else None

            warm_accs, post_accs = [], []
            traces = []
            for s in SEEDS:
                wp, pp, tr = run_cell(by_ep, ghat, s)
                incl = bal_acc(wp + pp)
                post = bal_acc(pp)
                if incl is not None:
                    warm_accs.append(incl)
                if post is not None:
                    post_accs.append(post)
                traces.append(tr)
            if not warm_accs or not post_accs or batch is None:
                continue
            rows.append({
                "construct": construct, "dataset": ds, "assessor": asr, "target": tgt,
                "n": len(flat), "n_ep": len(by_ep),
                "batch_bal_acc": batch, "batch_phat": bp,
                "incl_mean": float(np.mean(warm_accs)), "incl_sd": float(np.std(warm_accs)),
                "post_mean": float(np.mean(post_accs)), "post_sd": float(np.std(post_accs)),
                "penalty_post": float(np.mean(post_accs)) - batch,
                "penalty_incl": float(np.mean(warm_accs)) - batch,
            })
            # curve: mean p_hat and cut over orderings, subsampled
            cpath = os.path.join(a.outdir, "S7_curves_%s.csv"
                                 % construct.replace("+", "-"))
            newf = not os.path.exists(cpath)
            with open(cpath, "a", newline="") as f:
                w = csv.writer(f)
                if newf:
                    w.writerow(["construct", "dataset", "assessor", "target", "t",
                                "phat_mean", "cut_mean"])
                T = min(len(t) for t in traces)
                for t in range(0, T, max(1, T // 200)):
                    ph = [tr[t][1] for tr in traces if tr[t][1] is not None]
                    cu = [tr[t][2] for tr in traces if tr[t][2] is not None]
                    w.writerow([construct, ds, asr, tgt, t,
                                "%.4f" % np.mean(ph) if ph else "",
                                "%.4f" % np.mean(cu) if cu else ""])
        all_rows.extend(rows)

        cols = ["construct", "dataset", "assessor", "target", "n", "n_ep",
                "batch_bal_acc", "batch_phat", "incl_mean", "incl_sd", "post_mean",
                "post_sd", "penalty_post", "penalty_incl"]
        p = os.path.join(a.outdir, "S7_prequential_%s.csv" % construct.replace("+", "-"))
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c]
                            for c in cols])

        pseq = sum(1 for r in rows if abs(r["penalty_post"]) <= 0.01)
        pwarm = sum(1 for r in rows if r["penalty_incl"] < -0.01)
        summary_lines.append((construct, len(rows), pseq, pwarm, rows))
        print("%-20s cells %2d  P-seq %2d/%d  P-warm %2d/%d"
              % (construct, len(rows), pseq, len(rows), pwarm, len(rows)), flush=True)

    L = ["# S7 SUMMARY — prequential replay (cost of going online)\n",
         "Spec: `%s`. Warm-up %d steps, %d episode orderings (seeds %d-%d).\n"
         % (SPEC, WARMUP, len(SEEDS), SEEDS[0], SEEDS[-1]),
         "Each cell is compared against the batch g-rule **on the same construct**. "
         "S1d put that batch rule at G2b1-R3 FAIL on `violation+judgment`; S7 measures "
         "the sequential penalty relative to it and has no gate of its own.\n",
         "| construct | cells | P-seq (post within 0.01) | P-warm (incl worse by >0.01) "
         "| mean post penalty | mean incl penalty |",
         "|---|---|---|---|---|---|"]
    for construct, n, pseq, pwarm, rows in summary_lines:
        if not rows:
            continue
        L.append("| %s | %d | %d/%d | %d/%d | %+.4f | %+.4f |"
                 % (construct, n, pseq, n, pwarm, n,
                    float(np.mean([r["penalty_post"] for r in rows])),
                    float(np.mean([r["penalty_incl"] for r in rows]))))
    L.append("")
    L.append("**P-seq**: post-warm-up balanced accuracy within 0.01 of the batch rule "
             "in a majority of capable cells.")
    L.append("**P-warm**: the warm-up-inclusive number is worse than batch by more "
             "than 0.01 in a majority of capable cells — the warm-up is not free.\n")
    for construct, n, pseq, pwarm, rows in summary_lines:
        if not rows:
            continue
        L.append("- **%s**: P-seq %s (%d/%d), P-warm %s (%d/%d)"
                 % (construct, "HOLDS" if pseq * 2 >= n else "FAILS", pseq, n,
                    "HOLDS" if pwarm * 2 >= n else "FAILS", pwarm, n))
    L.append("\nA sequential form that tracks a batch rule which fails its own gate is "
             "faithful to a rule that does not work; per spec §Prediction that is the "
             "honest outcome and is not a success.\n")
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")
    print("-> %s, %s" % (a.outdir, a.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
