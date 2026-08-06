#!/usr/bin/env python3
"""GATE-2b.1 (A28.1) — the error-rate-indexed cut.

Implements docs/GATE2B1_SPEC_A28_1.md, pre-registered at 7df1f66 before any arm was
computed. A28's arms are anchors; A28's verdict is reported alongside, never replaced.

Arms
  V                argmax verdict (top-1 logprob token). Black-box floor.
  S-LOTO-raw       pooled other-target cut, applied raw.
  S-LOTO-quantile  that cut as a percentile of the pool, mapped through the target's
                   own unlabelled scores.
  S-g-quantile     the §6d rule: g = OLS(true error rate ~ mean judge score) fitted MACRO
                   on the other targets (one point each); p-hat = g(target mean score),
                   clipped [0.02, 0.98]; cut at percentile 100*(1 - p-hat) of the
                   target's unlabelled scores. Zero target labels.
  S-oracle-pct     cut at percentile 100*(1 - TRUE base rate). Upper bound, not a method.
  S-mid-gap        midpoint of the widest empty interval in the target's scores.
                   Label-free AND transfer-free; tests the bimodality mechanism.
  S-fitted         per-target labelled cut, episode-split OOS. Ceiling.

REALIZED FLAG RATE. The scores are bimodal with large lumps at near-identical values, so
a requested percentile often cannot be realized: quantile_cut lands inside a lump and the
>= comparison flags the whole lump. An arm can therefore request 33% and flag 65%. Every
cut-based arm records realized_flag_* so "g mis-estimated p-hat" and "the percentile was
unrealizable on this distribution" stay distinguishable — they are different findings.

AUDIT (blocking). Parse rate = verdict-parsed steps / scored steps. If ANY cell is below
99%, every arm is recomputed on the step-matched (parsed-only) subset and that pass is
primary. Not advisory: the run aborts rather than emit unmatched tables silently.
"""
import argparse
import collections
import csv
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate2b_cut_transfer as G

CAPABLE = G.CAPABLE
PARSE_MIN = 0.99


def widest_gap(scores):
    s = sorted(set(scores))
    if len(s) < 2:
        return None, 0.0
    best = (0.0, None, None)
    for a, b in zip(s, s[1:]):
        if b - a > best[0]:
            best = (b - a, a, b)
    w, lo, hi = best
    return ((lo + hi) / 2.0 if lo is not None else None), w


def fit_g(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    n = len(xs)
    if n < 2 or len(set(xs)) < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    return b, my - b * mx


def flag_rate(scores, thr):
    """Fraction actually flagged at this cut — NOT the requested percentile."""
    if thr is None:
        return None
    return sum(1 for u in scores if u >= thr) / len(scores)


def collect(pivot, scope, min_n, matched):
    """matched=True keeps only steps whose verdict token parsed, for every arm."""
    cells = {}
    xp = os.path.join(pivot, "crossprobe")
    for ds in sorted(d for d in os.listdir(pivot)
                     if os.path.isdir(os.path.join(pivot, d)) and d != "crossprobe"):
        for tgt in sorted(os.listdir(os.path.join(pivot, ds))):
            tdir = os.path.join(pivot, ds, tgt)
            if not os.path.isdir(tdir):
                continue
            labels = G.load_labels(os.path.join(tdir, "judge.jsonl"))
            if not labels:
                continue
            src = {tgt: [os.path.join(tdir, "probes.jsonl"),
                         os.path.join(tdir, "probes.aggtrue.jsonl")]}
            for asr in G.assessors_in(os.path.join(xp, ds, tgt)):
                src[asr] = [os.path.join(xp, ds, tgt, "ptrue.%s.%s.jsonl" % (asr, p))
                            for p in ("stages", "response")]
            for asr, paths in src.items():
                pr = G.load_ptrue(paths)
                by_ep = collections.defaultdict(list)
                n_all = n_parsed = 0
                for key, v in pr.items():
                    if key not in labels:
                        continue
                    u, said = G.scoped(v, scope)
                    if u is None:
                        continue
                    n_all += 1
                    if said is not None:
                        n_parsed += 1
                    if matched and said is None:
                        continue
                    by_ep[key[0]].append((u, labels[key] < 0.5, said))
                flat = [r for rs in by_ep.values() for r in rs]
                if len(flat) < min_n:
                    continue
                P = sum(1 for r in flat if r[1])
                if not (0 < P < len(flat)):
                    continue
                cells[(ds, asr, tgt)] = {
                    "by_ep": by_ep, "flat": flat, "base": P / len(flat),
                    # mean over LABEL-MATCHED steps only. Deployment would use all steps;
                    # this is not leakage (no labels enter the value) but the two differ
                    # slightly, so a reviewer should not read it as the deployed quantity.
                    "mean_u": statistics.mean([r[0] for r in flat]),
                    "parse_rate": (n_parsed / n_all) if n_all else 1.0}
    return cells


def build_rows(cells):
    rows = []
    for (ds, asr, tgt), C in sorted(cells.items()):
        flat = C["flat"]
        uy = [(u, y) for u, y, _ in flat]
        scores = [u for u, _, _ in flat]
        prep = G._prep(uy)

        vr = [(sd, y) for _, y, sd in flat if sd is not None]
        Pv = sum(1 for _, y in vr if y)
        Nv = len(vr) - Pv
        if Pv == 0 or Nv == 0:
            continue
        V = 0.5 * (sum(1 for sd, y in vr if y and sd == 1) / Pv
                   + sum(1 for sd, y in vr if not y and sd == 0) / Nv)
        V_flag = sum(1 for sd, _ in vr if sd == 1) / len(vr)

        eps = sorted(C["by_ep"])
        S_fitted = None
        if len(eps) >= 4:
            half = len(eps) // 2
            outs = []
            for fe, se in ((eps[:half], eps[half:]), (eps[half:], eps[:half])):
                fr = [(u, y) for e in fe for u, y, _ in C["by_ep"][e]]
                sr = [(u, y) for e in se for u, y, _ in C["by_ep"][e]]
                t = G.fit_cut(fr)
                if t is None:
                    continue
                b = G.bal_acc_at(sr, t)
                if b is not None:
                    outs.append(b)
            if outs:
                S_fitted = statistics.mean(outs)

        others = [k for k in cells if k[0] == ds and k[1] == asr and k[2] != tgt]
        pool = [(u, y) for k in others for u, y, _ in cells[k]["flat"]]
        S_raw = S_quant = S_g = None
        cut_pool = pct_pool = p_hat = None
        fr_raw = fr_quant = fr_g = None
        g_degenerate = 0
        if others and pool:
            cut_pool = G.fit_cut(pool)
            if cut_pool is not None:
                S_raw = G.bal_acc_at(uy, cut_pool, prep)
                fr_raw = flag_rate(scores, cut_pool)
                pct_pool = G.pct_of([u for u, _ in pool], cut_pool)
                q = G.quantile_cut(scores, pct_pool)
                if q is not None:
                    S_quant = G.bal_acc_at(uy, q, prep)
                    fr_quant = flag_rate(scores, q)
            g = fit_g([(cells[k]["mean_u"], cells[k]["base"]) for k in others])
            if g is None:
                g_degenerate = 1
            else:
                p_hat = min(0.98, max(0.02, g[0] * C["mean_u"] + g[1]))
                qg = G.quantile_cut(scores, 100.0 * (1.0 - p_hat))
                if qg is not None:
                    S_g = G.bal_acc_at(uy, qg, prep)
                    fr_g = flag_rate(scores, qg)

        qo = G.quantile_cut(scores, 100.0 * (1.0 - C["base"]))
        S_oracle = G.bal_acc_at(uy, qo, prep) if qo is not None else None
        fr_oracle = flag_rate(scores, qo)
        mid, gw = widest_gap(scores)
        S_gap = G.bal_acc_at(uy, mid, prep) if mid is not None else None
        fr_gap = flag_rate(scores, mid)
        mass = (sum(1 for u in scores if u < 0.1) + sum(1 for u in scores if u > 0.9)) / len(scores)

        rows.append(dict(
            dataset=ds, assessor=asr, target=tgt,
            arm="self" if asr == tgt else "cross",
            capable="yes" if asr in CAPABLE else "no",
            n=len(flat), n_ep=len(eps), n_pool_targets=len(others),
            parse_rate=C["parse_rate"], g_degenerate=g_degenerate,
            base=C["base"], mean_u=C["mean_u"], p_hat=p_hat,
            V=V, S_LOTO_raw=S_raw, S_LOTO_quantile=S_quant, S_g_quantile=S_g,
            S_oracle_pct=S_oracle, S_mid_gap=S_gap, S_fitted=S_fitted,
            req_pct_quant=pct_pool,
            req_pct_g=(None if p_hat is None else 100.0 * (1.0 - p_hat)),
            req_pct_oracle=100.0 * (1.0 - C["base"]),
            realized_flag_V=V_flag, realized_flag_raw=fr_raw,
            realized_flag_quant=fr_quant, realized_flag_g=fr_g,
            realized_flag_oracle=fr_oracle, realized_flag_gap=fr_gap,
            gap_width=gw, gap_mid=mid, mass_extremes=mass))
    return rows


def boot(vals, stat, nb=2000, seed=13):
    import random
    if len(vals) < 3:
        return None, None
    rng = random.Random(seed)
    d = []
    for _ in range(nb):
        s = [vals[rng.randrange(len(vals))] for _ in range(len(vals))]
        x = stat(s)
        if x is not None:
            d.append(x)
    if not d:
        return None, None
    d.sort()
    return d[int(.025 * len(d))], d[min(len(d) - 1, int(.975 * len(d)))]


ARMS = ["V", "S_LOTO_raw", "S_LOTO_quantile", "S_g_quantile",
        "S_oracle_pct", "S_mid_gap", "S_fitted"]


def report(sub, label, out):
    p = lambda s: (print(s), out.append(s))
    cnt = [r for r in sub if r["n_pool_targets"] >= 3 and r["V"] is not None]
    usable = [r for r in cnt if r["S_fitted"] is not None and (r["S_fitted"] - r["V"]) > 0.01]
    p("\n===== %s =====" % label)
    p("countable %d | unsaturated %d | g-degenerate %d"
      % (len(cnt), len(usable), sum(r["g_degenerate"] for r in cnt)))
    for arm in ARMS:
        vals = [r[arm] for r in cnt if r[arm] is not None]
        if vals:
            lo, hi = boot(vals, lambda v: sum(v) / len(v))
            p("  %-16s mean %.3f%s  (n=%d)" % (arm, statistics.mean(vals),
              ("  95%% CI [%.3f, %.3f]" % (lo, hi)) if lo is not None else "", len(vals)))
    for arm, fk in (("S_LOTO_quantile", "realized_flag_quant"),
                    ("S_g_quantile", "realized_flag_g"),
                    ("S_oracle_pct", "realized_flag_oracle"),
                    ("S_mid_gap", "realized_flag_gap")):
        u = [r for r in usable if r[arm] is not None]
        if not u:
            continue
        pooled = sum(r[arm] - r["V"] for r in u) / sum(r["S_fitted"] - r["V"] for r in u)
        lo, hi = boot([(r[arm] - r["V"], r["S_fitted"] - r["V"]) for r in u],
                      lambda v: (sum(x for x, _ in v) / sum(y for _, y in v))
                      if sum(y for _, y in v) > 0 else None)
        mor = statistics.mean([(r[arm] - r["V"]) / (r["S_fitted"] - r["V"]) for r in u])
        p("  capture(%-16s) pooled %.3f%s   mean-of-ratios %.3f"
          % (arm, pooled, ("  95%% CI [%.3f, %.3f]" % (lo, hi)) if lo is not None else "", mor))
    # requested vs realized flag rate — the tie-lump diagnostic
    for arm, rq, fk in (("S_g_quantile", "req_pct_g", "realized_flag_g"),
                        ("S_LOTO_quantile", "req_pct_quant", "realized_flag_quant"),
                        ("S_oracle_pct", "req_pct_oracle", "realized_flag_oracle")):
        u = [r for r in cnt if r[rq] is not None and r[fk] is not None]
        if u:
            d = [abs((100 - r[rq]) / 100.0 - r[fk]) for r in u]
            p("  realized-vs-requested |flag - (1-pct)| for %-16s mean %.3f max %.3f"
              % (arm, statistics.mean(d), max(d)))
    g = [r for r in cnt if r["S_g_quantile"] is not None]
    verdict = None
    if g:
        ge = [r for r in g if r["S_g_quantile"] >= r["V"]]
        lo, hi = boot([1 if r["S_g_quantile"] >= r["V"] else 0 for r in g],
                      lambda v: sum(v) / len(v))
        p("  P-g2: S_g_quantile >= V in %d/%d (%.0f%%)%s  [needs >=80%%]"
          % (len(ge), len(g), 100 * len(ge) / len(g),
             ("  95%% CI [%.0f%%, %.0f%%]" % (100 * lo, 100 * hi)) if lo is not None else ""))
        gq = [r for r in g if r["S_LOTO_quantile"] is not None]
        beat = [r for r in gq if r["S_g_quantile"] >= r["S_LOTO_quantile"]]
        p("  P-g1: S_g_quantile >= S_LOTO_quantile in %d/%d (%.0f%%)"
          % (len(beat), len(gq), 100 * len(beat) / max(len(gq), 1)))
        u = [r for r in usable if r["S_g_quantile"] is not None]
        pooled = (sum(r["S_g_quantile"] - r["V"] for r in u)
                  / sum(r["S_fitted"] - r["V"] for r in u)) if u else None
        p_g2 = len(ge) / len(g)
        verdict = ("G2b1-R3 FAIL" if p_g2 < 0.80 else
                   ("G2b1-R1 PASS" if (pooled is not None and pooled >= 0.5)
                    else "G2b1-R2 PARTIAL"))
        p("  ==> %s" % verdict)
    gap = [r for r in cnt if r["S_mid_gap"] is not None and r["S_fitted"] is not None]
    if gap:
        near = [r for r in gap if abs(r["S_mid_gap"] - r["S_fitted"]) <= 0.01]
        p("  P-gap: |S_mid_gap - S_fitted| <= 0.01 in %d/%d (%.0f%%)"
          % (len(near), len(gap), 100 * len(near) / len(gap)))
    if cnt:
        ok = [r for r in cnt if r["mass_extremes"] > 0.5]
        w = sorted(r["gap_width"] for r in cnt)
        p("  P-shape: mass-at-extremes>50%% in %d/%d (%.0f%%); gap width min %.3f "
          "median %.3f max %.3f; width>0.05 in %d/%d"
          % (len(ok), len(cnt), 100 * len(ok) / len(cnt), w[0], w[len(w) // 2], w[-1],
             sum(1 for x in w if x > 0.05), len(w)))
    return verdict


def cross_dataset_probe(cells, out):
    """Apply each assessor's pooled raw cut from one dataset to its cells in the other."""
    p = lambda s: (print(s), out.append(s))
    p("\n===== CROSS-DATASET PROBE (secondary) =====")
    p("%-26s %-9s %-9s %8s %8s %8s" % ("assessor", "cut from", "applied to",
                                       "within", "across", "delta"))
    rows = []
    for asr in sorted({k[1] for k in cells}):
        for src_ds, dst_ds in (("alfworld", "hotpotqa"), ("hotpotqa", "alfworld")):
            src = [k for k in cells if k[1] == asr and k[0] == src_ds]
            dst = [k for k in cells if k[1] == asr and k[0] == dst_ds]
            if len(src) < 2 or not dst:
                continue
            pool = [(u, y) for k in src for u, y, _ in cells[k]["flat"]]
            cut = G.fit_cut(pool)
            if cut is None:
                continue
            wi, ac = [], []
            for k in dst:
                uy = [(u, y) for u, y, _ in cells[k]["flat"]]
                b = G.bal_acc_at(uy, cut)
                if b is not None:
                    ac.append(b)
            for k in src:
                uy = [(u, y) for u, y, _ in cells[k]["flat"]]
                b = G.bal_acc_at(uy, cut)
                if b is not None:
                    wi.append(b)
            if wi and ac:
                p("%-26s %-9s %-9s %8.3f %8.3f %+8.3f"
                  % (asr, src_ds, dst_ds, statistics.mean(wi), statistics.mean(ac),
                     statistics.mean(ac) - statistics.mean(wi)))
                rows.append((asr, src_ds, dst_ds, statistics.mean(wi), statistics.mean(ac)))
    return rows


def dump_curves(cells, figdir, scope):
    """Flatness curve (bal_acc vs cut percentile) + histogram, per capable cell."""
    os.makedirs(figdir, exist_ok=True)
    cpath = os.path.join(figdir, "flatness_curves_%s.csv" % scope)
    hpath = os.path.join(figdir, "score_histograms_%s.csv" % scope)
    with open(cpath, "w", newline="") as fc, open(hpath, "w", newline="") as fh:
        wc = csv.writer(fc); wc.writerow(
            ["dataset", "assessor", "target", "pct", "cut", "bal_acc", "realized_flag"])
        wh = csv.writer(fh); wh.writerow(
            ["dataset", "assessor", "target", "bin_lo", "bin_hi", "count", "frac"])
        for (ds, asr, tgt), C in sorted(cells.items()):
            if asr not in CAPABLE:
                continue
            flat = C["flat"]
            uy = [(u, y) for u, y, _ in flat]
            scores = [u for u, _, _ in flat]
            prep = G._prep(uy)
            for pct in range(1, 100):
                cut = G.quantile_cut(scores, pct)
                b = G.bal_acc_at(uy, cut, prep)
                if b is not None:
                    wc.writerow([ds, asr, tgt, pct, "%.6f" % cut, "%.4f" % b,
                                 "%.4f" % flag_rate(scores, cut)])
            for i in range(20):
                lo, hi = i / 20.0, (i + 1) / 20.0
                c = sum(1 for u in scores if (u >= lo and (u < hi or (i == 19 and u <= hi))))
                wh.writerow([ds, asr, tgt, "%.2f" % lo, "%.2f" % hi, c,
                             "%.4f" % (c / len(scores))])
    print("wrote %s and %s" % (cpath, hpath))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--scope", default="AGG-true")
    ap.add_argument("--outdir", default="tables_gate2b1")
    ap.add_argument("--figdir", default="figures_gate2b1")
    ap.add_argument("--min-n", type=int, default=200)
    ap.add_argument("--allow-unmatched", action="store_true",
                    help="override the blocking audit; recorded in the output if used")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    # ---------------- BLOCKING AUDIT ----------------
    cells_all = collect(a.pivot, a.scope, a.min_n, matched=False)
    prates = {k: c["parse_rate"] for k, c in cells_all.items()}
    worst = min(prates.values())
    n_bad = sum(1 for v in prates.values() if v < PARSE_MIN)
    print("AUDIT parse rate: min %.5f | cells below %.0f%%: %d / %d"
          % (worst, 100 * PARSE_MIN, n_bad, len(prates)))
    # tag: "full" when the audit clears (one pass, it IS the primary); "unmatched"
    # only when a matched pass exists alongside it and the distinction matters.
    full_tag = "unmatched" if n_bad else "full"
    passes = [(full_tag, cells_all)]
    primary = full_tag
    if n_bad:
        print("AUDIT TRIGGERED — recomputing every arm on the step-matched subset; "
              "matched is primary (spec: A28.1 Audit fix).")
        for k, v in sorted(prates.items()):
            if v < PARSE_MIN:
                print("   %-9s %-26s -> %-26s parse %.4f" % (k[0], k[1], k[2], v))
        cells_m = collect(a.pivot, a.scope, a.min_n, matched=True)
        passes.append(("matched", cells_m))
        primary = "matched"
        if not a.allow_unmatched and not cells_m:
            sys.exit("ABORT: step-matched recomputation produced no cells.")
    else:
        print("AUDIT CLEARS — V and the S arms already share identical step sets.")

    out_lines = []
    verdicts = {}
    for tag, cells in passes:
        rows = build_rows(cells)
        cols = ["dataset", "assessor", "target", "arm", "capable", "n", "n_ep",
                "n_pool_targets", "parse_rate", "g_degenerate", "base", "mean_u", "p_hat",
                "V", "S_LOTO_raw", "S_LOTO_quantile", "S_g_quantile", "S_oracle_pct",
                "S_mid_gap", "S_fitted", "req_pct_quant", "req_pct_g", "req_pct_oracle",
                "realized_flag_V", "realized_flag_raw", "realized_flag_quant",
                "realized_flag_g", "realized_flag_oracle", "realized_flag_gap",
                "gap_width", "gap_mid", "mass_extremes"]
        path = os.path.join(a.outdir, "gate2b1_cells_%s_%s.csv" % (a.scope, tag))
        with open(path, "w", newline="") as fo:
            w = csv.writer(fo); w.writerow(cols)
            for r in rows:
                w.writerow([r[c] if isinstance(r[c], (str, int)) else
                            ("" if r[c] is None else "%.4f" % r[c]) for c in cols])
        print("\n[%s pass] cells: %d -> %s" % (tag.upper(), len(rows), path))
        out_lines.append("[%s pass] cells: %d" % (tag.upper(), len(rows)))
        v_cap = report([r for r in rows if r["capable"] == "yes"],
                       "CAPABLE STRATUM (decisive) — %s" % tag, out_lines)
        report(rows, "ALL JUDGES (context) — %s" % tag, out_lines)
        verdicts[tag] = v_cap
        if tag == primary:
            cross_dataset_probe(cells, out_lines)
            dump_curves(cells, a.figdir, a.scope)

    print("\nPRIMARY PASS: %s | capable verdict: %s" % (primary, verdicts.get(primary)))
    with open(os.path.join(a.outdir, "gate2b1_console_%s.txt" % a.scope), "w") as fo:
        fo.write("\n".join(out_lines) + "\n")


if __name__ == "__main__":
    main()
