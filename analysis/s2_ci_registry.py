#!/usr/bin/env python3
"""S2 — CI sweep and the claim->interval registry.

Spec: docs/specs/S2_SPEC.md.  One row per paper claim-sentence: estimate, interval,
the null it is tested against, and a status.  The only decision rule S2 has is
`soften`: a claim whose 95% interval includes its null is pre-committed to soften in
the rewrite pass.  S2 never changes a point estimate and never re-decides a gate.

Claims whose source table is missing are emitted with status=absent rather than
skipped, so the registry cannot quietly under-report.
"""
import argparse
import csv
import json
import os

import numpy as np

SPEC = "docs/specs/S2_SPEC.md"
SEED = 13
NBOOT = 2000


def read(path):
    if not path or not os.path.exists(path):
        return None
    with open(path) as f:
        return list(csv.DictReader(f))


def fnum(r, k):
    try:
        return float(r.get(k, ""))
    except (TypeError, ValueError):
        return None


def boot_mean(v, rng, nboot=NBOOT):
    v = np.asarray([x for x in v if x is not None], dtype=np.float64)
    if v.size == 0:
        return None, None, None
    b = np.array([v[rng.integers(0, v.size, v.size)].mean() for _ in range(nboot)])
    return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975))


def boot_prop(flags, rng, nboot=NBOOT):
    """Bootstrap a proportion over CELLS (spec: resample cells, not steps)."""
    v = np.asarray([1.0 if f else 0.0 for f in flags], dtype=np.float64)
    if v.size == 0:
        return None, None, None
    b = np.array([v[rng.integers(0, v.size, v.size)].mean() for _ in range(nboot)])
    return float(v.mean()), float(np.quantile(b, .025)), float(np.quantile(b, .975))


def row(cid, claim, est, lo, hi, null, method, n, src, note=""):
    if est is None:
        status = "absent"
    elif lo is None or hi is None:
        status = "underpowered"
    elif lo <= null <= hi:
        status = "soften"
    else:
        status = "ok"
    return {"claim_id": cid, "claim": claim, "estimate": est, "ci_lo": lo,
            "ci_hi": hi, "null_value": null, "method": method, "n": n,
            "source_table": src, "status": status, "note": note}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate2b1",
                    default="figures/tables_gate2b1/gate2b1_cells_AGG-true_full.csv")
    ap.add_argument("--vv", default="reports/tables/verdict_vs_value.csv")
    ap.add_argument("--s1", default="tables_S1")
    ap.add_argument("--outdir", default="tables_S2")
    ap.add_argument("--summary", default="S2_SUMMARY.md")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows = []

    # ---- A28.1 derived claims -----------------------------------------
    g = read(a.gate2b1)
    if g is None:
        rows.append(row("C-g2", "the indexed cut beats the verdict", None, None, None,
                        0.80, "bootstrap over cells", 0, a.gate2b1))
        rows.append(row("C-cap", "pooled capture of the g-rule", None, None, None,
                        0.5, "bootstrap over cells", 0, a.gate2b1))
    else:
        cap = [r for r in g if r.get("capable") == "yes"]
        # P-g2: S_g_quantile >= V, over countable capable cells
        flags, gains, denoms = [], [], []
        for r in cap:
            V, S, F = fnum(r, "V"), fnum(r, "S_g_quantile"), fnum(r, "S_fitted")
            if V is None or S is None:
                continue
            flags.append(S >= V)
            if F is not None and (F - V) > 0.01:      # unsaturated, per A28 rule
                gains.append(S - V)
                denoms.append(F - V)
        est, lo, hi = boot_prop(flags, rng)
        rows.append(row("C-g2", "S-g-quantile >= V on capable cells (P-g2)",
                        est, lo, hi, 0.80, "cell bootstrap, 2000", len(flags),
                        a.gate2b1,
                        "null is the registered 0.80 threshold, not 0.5"))
        # pooled capture = sum(gain)/sum(denom); bootstrap the RATIO over cells
        if gains:
            gv, dv = np.array(gains), np.array(denoms)
            b = []
            for _ in range(NBOOT):
                i = rng.integers(0, gv.size, gv.size)
                d = dv[i].sum()
                if d != 0:
                    b.append(gv[i].sum() / d)
            b = np.array(b)
            rows.append(row("C-cap", "pooled capture ratio of the g-rule (capable)",
                            float(gv.sum() / dv.sum()), float(np.quantile(b, .025)),
                            float(np.quantile(b, .975)), 0.5,
                            "cell bootstrap of the ratio, 2000", len(gains),
                            a.gate2b1, "null is the registered 0.5 threshold"))

    # ---- b1: value vs verdict ------------------------------------------
    vv = read(a.vv)
    if vv is None:
        rows.append(row("C-chan", "reading the value beats reading the verdict",
                        None, None, None, 0.0, "cell bootstrap", 0, a.vv))
    else:
        gains = [fnum(r, "value_out") - fnum(r, "verdict")
                 for r in vv
                 if fnum(r, "value_out") is not None and fnum(r, "verdict") is not None]
        est, lo, hi = boot_mean(gains, rng)
        rows.append(row("C-chan", "mean OOS gain of value over verdict", est, lo, hi,
                        0.0, "cell bootstrap, 2000", len(gains), a.vv))
        est, lo, hi = boot_prop([x > 0 for x in gains], rng)
        rows.append(row("C-chan-frac", "fraction of cells where value beats verdict",
                        est, lo, hi, 0.5, "cell bootstrap, 2000", len(gains), a.vv))

    # ---- S1 / A30 claims -----------------------------------------------
    js = os.path.join(a.s1, "S1abc_L2.json")
    abc = json.load(open(js)) if os.path.exists(js) else {}
    d = abc.get("A30_pred_i")
    rows.append(row("C-a30i", "capable external superiority (violation+judgment)",
                    d and d.get("pooled_delta"),
                    d and d["pooled_ci"][0], d and d["pooled_ci"][1], 0.0,
                    "paired episode bootstrap then cell bootstrap", d and d.get("total"),
                    js) if d else
                row("C-a30i", "capable external superiority (violation+judgment)",
                    None, None, None, 0.0, "-", 0, js))
    d = abc.get("A30_pred_ii")
    rows.append(row("C-a30ii", "self-inflation larger under outcome than "
                    "violation+judgment",
                    d and d.get("mean_dd"), d and d["ci"][0], d and d["ci"][1], 0.0,
                    "cell bootstrap of difference-of-differences", d and d.get("arms"),
                    js) if d else
                row("C-a30ii", "self-inflation larger under outcome", None, None, None,
                    0.0, "-", 0, js))

    # ---- crossprobe per-cell AUROC claims (tier contrast, ties) ---------
    for cid, cons, claim in (
            ("C-tier", "violation+judgment",
             "capable-tier assessors beat the tier below"),):
        p = os.path.join(a.s1, "S1a_crossprobe_L2_%s.csv" % cons.replace("+", "-"))
        t = read(p)
        if not t:
            rows.append(row(cid, claim, None, None, None, 0.0, "-", 0, p))
            continue
        cap = [fnum(r, "auroc") for r in t
               if r.get("capable") == "1" and r.get("self") == "0"
               and r.get("underpowered") == "0"]
        non = [fnum(r, "auroc") for r in t
               if r.get("capable") == "0" and r.get("self") == "0"
               and r.get("underpowered") == "0"]
        ce, clo, chi = boot_mean(cap, rng)
        ne, nlo, nhi = boot_mean(non, rng)
        if ce is not None and ne is not None:
            cv, nv = np.array(cap), np.array(non)
            b = np.array([cv[rng.integers(0, cv.size, cv.size)].mean()
                          - nv[rng.integers(0, nv.size, nv.size)].mean()
                          for _ in range(NBOOT)])
            rows.append(row(cid, claim, ce - ne, float(np.quantile(b, .025)),
                            float(np.quantile(b, .975)), 0.0,
                            "unpaired cell bootstrap (different cell sets)",
                            len(cap) + len(non), p,
                            "capable mean %.4f (n=%d), non-capable %.4f (n=%d)"
                            % (ce, len(cap), ne, len(non))))

    cols = ["claim_id", "claim", "estimate", "ci_lo", "ci_hi", "null_value",
            "method", "n", "source_table", "status", "note"]
    out = os.path.join(a.outdir, "ci_registry.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r[c] is None else
                        (r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c])
                        for c in cols])

    soften = [r for r in rows if r["status"] == "soften"]
    absent = [r for r in rows if r["status"] == "absent"]
    L = ["# S2 SUMMARY — CI registry\n",
         "Spec: `%s`. Seed %d, %d bootstrap draws.\n" % (SPEC, SEED, NBOOT),
         "| claim | estimate | 95% CI | null | status | n |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %s — %s | %s | %s | %s | **%s** | %s |"
                 % (r["claim_id"], r["claim"],
                    "n/a" if r["estimate"] is None else "%.4f" % r["estimate"],
                    "n/a" if r["ci_lo"] is None else "[%.4f, %.4f]" % (r["ci_lo"], r["ci_hi"]),
                    "%.2f" % r["null_value"], r["status"],
                    r["n"] if r["n"] is not None else "?"))
    L.append("")
    L.append("## Sentences committed to soften\n")
    if soften:
        L.append("These intervals include their null. The commitment to soften was "
                 "registered in the spec before the intervals were computed.\n")
        for r in soften:
            L.append("- **%s** — %s: %.4f, CI [%.4f, %.4f] includes %.2f"
                     % (r["claim_id"], r["claim"], r["estimate"], r["ci_lo"],
                        r["ci_hi"], r["null_value"]))
    else:
        L.append("None.")
    if absent:
        L.append("\n## Absent sources\n")
        for r in absent:
            L.append("- %s — `%s` not found" % (r["claim_id"], r["source_table"]))
    L.append("")
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")
    print("S2: %d claims, %d soften, %d absent -> %s, %s"
          % (len(rows), len(soften), len(absent), out, a.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
