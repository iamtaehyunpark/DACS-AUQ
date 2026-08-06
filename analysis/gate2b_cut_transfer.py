#!/usr/bin/env python3
"""GATE-2b (A28) — can the decision boundary move to a new target without labels?

Implements docs/GATE2B_SPEC_A28.md exactly. Pre-registered before running; the decision
rules G2b-R1/R2/R3 and the predictions P-raw / P-quantile are fixed in that document and
are not to be edited to fit the outcome.

Four arms per (assessor x target x dataset) cell. The held-out target is the cell's own
target; "other targets" always means other targets of the SAME assessor and dataset.

  V                 argmax verdict = the top-1 logprob answer. Black-box floor: no
                    logprobs, no labels, no transfer.
  S-LOTO-raw        cut fitted on the pooled labelled steps of the OTHER targets, applied
                    to the held-out target as a RAW score threshold. Predicted to fail.
  S-LOTO-quantile   the same other-target fit expressed as a PERCENTILE of the fitting
                    pool, then mapped through the held-out target's own UNLABELLED score
                    distribution to a raw cut. Labels from the target: zero.
  S-fitted          per-target labelled cut, episode-split out-of-sample. The calibrated
                    ceiling.

Honesty label carried from the spec: S-LOTO-quantile uses the held-out target's full
frozen score distribution, so it is the BATCH form of the online rule. The sequential
variant is out of scope here.

Cut criterion is balanced accuracy on the fitting pool (not Youden), per spec. Pooling is
per-step, weighted by n, with a per-target macro variant reported as sensitivity.

  gate2b_cut_transfer.py [--pivot result/pivot] [--scope AGG-true] [--outdir tables_gate2b]
"""
import argparse
import collections
import csv
import json
import os
import statistics

_YES = {"yes", "y", "yeah", "yep", "correct", "true"}
_NO = {"no", "n", "nope", "false", "incorrect"}
CAPABLE = {"Llama-3.3-70B-Instruct", "Qwen3.6-35B-A3B"}


def top1_verdict(ftt):
    """The temperature-0 black-box answer: highest-logprob first token."""
    if not ftt:
        return None
    best = max(ftt, key=lambda a: a["logprob"])
    t = (best.get("token") or "").strip().lower()
    return 0 if t in _YES else 1 if t in _NO else None


def load_labels(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        r = json.loads(line)
        v = [x.get("incorrect") for x in (r.get("votes") or {}).values()]
        v = [x for x in v if x is not None]
        if v:
            out[(r["task_id"], r["step_idx"])] = sum(1 for x in v if x == 0) / len(v)
    return out


def load_ptrue(paths):
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
            f = r.get("metric_field") or ""
            k = ("T" if f.startswith("U_T") else "A" if f.startswith("U_A")
                 else "R" if f.startswith("U_R") else None)
            if k is None:
                k = {"thought": "T", "action": "A", "response": "R"}.get(r.get("stage"))
            if not k:
                continue
            key = (r.get("task_id"), r.get("step_idx"))
            out[key][k] = float(u)
            v = top1_verdict(r.get("first_token_top"))
            if v is not None:
                out[key]["v" + k] = v
    return out


def scoped(v, scope):
    if scope == "SPLIT-thought":
        return v.get("T"), v.get("vT")
    if scope == "SPLIT-action":
        return v.get("A"), v.get("vA")
    if scope == "AGG-true":
        return v.get("R"), v.get("vR")
    if scope == "AGG-mean":
        t, a = v.get("T"), v.get("A")
        return (None if t is None or a is None else (t + a) / 2.0), None
    return None, None


def _prep(rows):
    """Sort once and precompute prefix counts, so a threshold sweep is O(n log n) rather
    than O(n^2). The naive version re-scanned every row per candidate cut, which on the
    ~25k-row LOTO pools was hundreds of millions of comparisons per cell."""
    srt = sorted(rows, key=lambda r: r[0])
    us = [r[0] for r in srt]
    # below_pos[i] / below_neg[i] = counts among the first i rows (u < us[i] boundary)
    below_pos = [0] * (len(srt) + 1)
    below_neg = [0] * (len(srt) + 1)
    for i, (_, y) in enumerate(srt):
        below_pos[i + 1] = below_pos[i] + (1 if y else 0)
        below_neg[i + 1] = below_neg[i] + (0 if y else 1)
    P, N = below_pos[-1], below_neg[-1]
    return us, below_pos, below_neg, P, N


def bal_acc_at(rows, thr, prep=None):
    """Predict incorrect iff u >= thr."""
    import bisect
    us, bp, bn, P, N = prep if prep else _prep(rows)
    if P == 0 or N == 0:
        return None
    i = bisect.bisect_left(us, thr)      # rows [0,i) have u < thr
    tp = P - bp[i]
    tn = bn[i]
    return 0.5 * (tp / P + tn / N)


def fit_cut(rows, prep=None):
    """Balanced-accuracy-optimal cut (spec: not Youden)."""
    us, bp, bn, P, N = prep if prep else _prep(rows)
    if P == 0 or N == 0:
        return None
    best = (-1.0, None)
    i = 0
    n = len(us)
    while i < n:
        j = i
        while j < n and us[j] == us[i]:
            j += 1
        b = 0.5 * ((P - bp[i]) / P + bn[i] / N)   # threshold == us[i]
        if b > best[0]:
            best = (b, us[i])
        i = j
    # also consider a cut above every score (predict all correct)
    b = 0.5 * (0.0 + N / N)
    if b > best[0]:
        best = (b, us[-1] + 1e-9)
    return best[1]


def pct_of(values, x):
    """Percentile rank of cut x within `values` (fraction strictly below)."""
    if not values:
        return None
    return 100.0 * sum(1 for v in values if v < x) / len(values)


def quantile_cut(values, pct):
    """The raw score at percentile `pct` of `values` (the target's unlabelled scores)."""
    if not values or pct is None:
        return None
    s = sorted(values)
    i = int(round(pct / 100.0 * (len(s) - 1)))
    return s[max(0, min(i, len(s) - 1))]


def assessors_in(xdir):
    seen = set()
    if not os.path.isdir(xdir):
        return seen
    for f in os.listdir(xdir):
        if not f.startswith("ptrue.") or not f.endswith(".jsonl"):
            continue
        stem = f[len("ptrue."):-len(".jsonl")]
        for suf in (".stages", ".response"):
            if stem.endswith(suf):
                seen.add(stem[:-len(suf)])
                break
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--scope", default="AGG-true")
    ap.add_argument("--outdir", default="tables_gate2b")
    ap.add_argument("--min-n", type=int, default=200)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    # ---- gather every cell's per-step (score, label, verdict), grouped by episode ----
    cells = {}
    xp = os.path.join(a.pivot, "crossprobe")
    for ds in sorted(d for d in os.listdir(a.pivot)
                     if os.path.isdir(os.path.join(a.pivot, d)) and d != "crossprobe"):
        for tgt in sorted(os.listdir(os.path.join(a.pivot, ds))):
            tdir = os.path.join(a.pivot, ds, tgt)
            if not os.path.isdir(tdir):
                continue
            labels = load_labels(os.path.join(tdir, "judge.jsonl"))
            if not labels:
                continue
            src = {tgt: [os.path.join(tdir, "probes.jsonl"),
                         os.path.join(tdir, "probes.aggtrue.jsonl")]}
            for asr in assessors_in(os.path.join(xp, ds, tgt)):
                src[asr] = [os.path.join(xp, ds, tgt, "ptrue.%s.%s.jsonl" % (asr, p))
                            for p in ("stages", "response")]
            for asr, paths in src.items():
                probes = load_ptrue(paths)
                by_ep = collections.defaultdict(list)
                for key, v in probes.items():
                    if key not in labels:
                        continue
                    u, said = scoped(v, a.scope)
                    if u is None:
                        continue
                    by_ep[key[0]].append((u, labels[key] < 0.5, said))
                flat = [r for rs in by_ep.values() for r in rs]
                if len(flat) < a.min_n:
                    continue
                if not (0 < sum(1 for r in flat if r[1]) < len(flat)):
                    continue
                cells[(ds, asr, tgt)] = {"by_ep": by_ep, "flat": flat}

    rows = []
    for (ds, asr, tgt), C in sorted(cells.items()):
        flat = C["flat"]
        uy = [(u, y) for u, y, _ in flat]
        scores = [u for u, _, _ in flat]

        # --- V: black-box argmax verdict -------------------------------------------
        vr = [(sd, y) for _, y, sd in flat if sd is not None]
        P = sum(1 for _, y in vr if y)
        N = len(vr) - P
        if P == 0 or N == 0:
            continue
        V = 0.5 * (sum(1 for sd, y in vr if y and sd == 1) / P
                   + sum(1 for sd, y in vr if not y and sd == 0) / N)

        # --- S-fitted: per-target cut, episode-split OOS ----------------------------
        eps = sorted(C["by_ep"])
        S_fitted = None
        if len(eps) >= 4:
            half = len(eps) // 2
            outs = []
            for fit_e, sc_e in ((eps[:half], eps[half:]), (eps[half:], eps[:half])):
                fr = [(u, y) for e in fit_e for u, y, _ in C["by_ep"][e]]
                sr = [(u, y) for e in sc_e for u, y, _ in C["by_ep"][e]]
                t = fit_cut(fr)
                if t is None:
                    continue
                b = bal_acc_at(sr, t)
                if b is not None:
                    outs.append(b)
            if outs:
                S_fitted = statistics.mean(outs)

        # --- LOTO pool: other targets of the same assessor x dataset ---------------
        others = [k for k in cells if k[0] == ds and k[1] == asr and k[2] != tgt]
        pool_step, pool_macro_cuts = [], []
        for k in others:
            o = [(u, y) for u, y, _ in cells[k]["flat"]]
            pool_step.extend(o)
            c = fit_cut(o)
            if c is not None:
                pool_macro_cuts.append((c, cells[k]["flat"]))
        n_pool = len(others)

        S_raw = S_quant = S_raw_macro = S_quant_macro = None
        cut_pool = pct_pool = None
        if n_pool >= 1 and pool_step:
            cut_pool = fit_cut(pool_step)
            if cut_pool is not None:
                # raw transfer: apply the pooled cut directly
                S_raw = bal_acc_at(uy, cut_pool)
                # quantile transfer: where did that cut sit in the POOL's own scores,
                # and what raw score sits at the same percentile of the TARGET's scores?
                pct_pool = pct_of([u for u, _ in pool_step], cut_pool)
                q = quantile_cut(scores, pct_pool)
                if q is not None:
                    S_quant = bal_acc_at(uy, q)
            # macro sensitivity: average the per-target cuts / percentiles instead
            if pool_macro_cuts:
                mc = statistics.mean([c for c, _ in pool_macro_cuts])
                S_raw_macro = bal_acc_at(uy, mc)
                mp = statistics.mean([pct_of([u for u, _, _ in fl], c)
                                      for c, fl in pool_macro_cuts])
                qm = quantile_cut(scores, mp)
                if qm is not None:
                    S_quant_macro = bal_acc_at(uy, qm)

        rows.append(dict(
            dataset=ds, assessor=asr, target=tgt,
            arm="self" if asr == tgt else "cross",
            capable="yes" if asr in CAPABLE else "no",
            n=len(flat), n_ep=len(eps), n_pool_targets=n_pool,
            base=sum(1 for _, y, _ in flat if y) / len(flat),
            V=V, S_LOTO_raw=S_raw, S_LOTO_quantile=S_quant, S_fitted=S_fitted,
            S_LOTO_raw_macro=S_raw_macro, S_LOTO_quantile_macro=S_quant_macro,
            cut_pool=cut_pool, pct_pool=pct_pool))

    # ---- write per-cell table --------------------------------------------------
    cols = ["dataset", "assessor", "target", "arm", "capable", "n", "n_ep",
            "n_pool_targets", "base", "V", "S_LOTO_raw", "S_LOTO_quantile", "S_fitted",
            "S_LOTO_raw_macro", "S_LOTO_quantile_macro", "cut_pool", "pct_pool"]
    path = os.path.join(a.outdir, "gate2b_cells_%s.csv" % a.scope)
    with open(path, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] if isinstance(r[c], (str, int)) else
                        ("" if r[c] is None else "%.4f" % r[c]) for c in cols])
    print("cells: %d -> %s" % (len(rows), path))

    # ---- decision rules --------------------------------------------------------
    # spec: a cell whose fitting pool has < 3 targets is reported but excluded from the
    # pass/fail count
    def boot_ci(vals, stat, n_boot=2000, seed=13):
        """Percentile bootstrap over CELLS. The unit of resampling is the cell, because
        the pass rate and the capture ratio are both statistics over cells, and the
        pre-registered thresholds (80%, 0.5) are read against them."""
        import random
        if len(vals) < 3:
            return None, None
        rng = random.Random(seed)
        draws = []
        for _ in range(n_boot):
            samp = [vals[rng.randrange(len(vals))] for _ in range(len(vals))]
            d = stat(samp)
            if d is not None:
                draws.append(d)
        if not draws:
            return None, None
        draws.sort()
        return (draws[int(0.025 * len(draws))],
                draws[min(len(draws) - 1, int(0.975 * len(draws)))])

    def evaluate(sub, label):
        countable = [r for r in sub if r["n_pool_targets"] >= 3
                     and r["S_LOTO_quantile"] is not None and r["V"] is not None]
        if not countable:
            print("\n[%s] no countable cells" % label)
            return
        q_ge_v = [r for r in countable if r["S_LOTO_quantile"] >= r["V"]]
        p_quant = len(q_ge_v) / len(countable)
        raw_lt_v = [r for r in countable
                    if r["S_LOTO_raw"] is not None and r["S_LOTO_raw"] < r["V"]]
        # capture ratio, excluding saturated cells (S_fitted - V <= 0.01)
        usable = [r for r in countable if r["S_fitted"] is not None
                  and (r["S_fitted"] - r["V"]) > 0.01]
        sat = len(countable) - len(usable)
        caps = [(r["S_LOTO_quantile"] - r["V"]) / (r["S_fitted"] - r["V"]) for r in usable]
        cap = statistics.mean(caps) if caps else None
        print("\n===== %s =====" % label)
        print("countable cells: %d (excluded for pool<3: %d, saturated: %d)"
              % (len(countable), len(sub) - len(countable), sat))
        for arm in ("V", "S_LOTO_raw", "S_LOTO_quantile", "S_fitted"):
            vals = [r[arm] for r in countable if r[arm] is not None]
            if vals:
                alo, ahi = boot_ci(vals, lambda v: sum(v) / len(v))
                print("  %-18s mean %.3f   sd %.3f%s"
                      % (arm, statistics.mean(vals),
                         statistics.pstdev(vals) if len(vals) > 1 else 0.0,
                         ("   95%% CI [%.3f, %.3f]" % (alo, ahi)) if alo is not None else ""))
        print("  P-raw    : S-LOTO-raw < V in %d/%d cells (%.0f%%)"
              % (len(raw_lt_v), len(countable), 100 * len(raw_lt_v) / len(countable)))
        flags = [1 if r["S_LOTO_quantile"] >= r["V"] else 0 for r in countable]
        qlo, qhi = boot_ci(flags, lambda v: sum(v) / len(v))
        print("  P-quantile: S-LOTO-quantile >= V in %d/%d cells (%.0f%%)  [needs >=80%%]"
              % (len(q_ge_v), len(countable), 100 * p_quant)
              + ("   95%% CI [%.0f%%, %.0f%%]" % (100 * qlo, 100 * qhi)
                 if qlo is not None else ""))
        if cap is not None:
            clo, chi = boot_ci(caps, lambda v: sum(v) / len(v))
            print("  capture ratio (mean over %d unsaturated): %.3f  [R1 needs >=0.5]"
                  % (len(caps), cap)
                  + ("   95%% CI [%.3f, %.3f]" % (clo, chi) if clo is not None else ""))
            # does the pre-registered verdict itself survive resampling?
            if qlo is not None:
                print("  rule stability: P-quantile CI %s 80%% threshold; capture CI %s 0.50"
                      % ("STRADDLES" if qlo < 0.80 <= qhi else
                         ("entirely ABOVE" if qlo >= 0.80 else "entirely BELOW"),
                         "STRADDLES" if clo < 0.50 <= chi else
                         ("entirely ABOVE" if clo >= 0.50 else "entirely BELOW")))
        verdict = ("G2b-R3 FAIL" if p_quant < 0.80 else
                   "G2b-R1 PASS" if (cap is not None and cap >= 0.5) else
                   "G2b-R2 PARTIAL")
        print("  ==> %s" % verdict)
        return verdict

    evaluate(rows, "ALL JUDGES")
    evaluate([r for r in rows if r["capable"] == "yes"], "CAPABLE STRATUM (Llama-70B, Qwen-35B)")


if __name__ == "__main__":
    main()
