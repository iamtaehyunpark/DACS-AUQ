#!/usr/bin/env python3
"""S1e — assemble S1_SUMMARY.md from the S1 tables.

Spec: docs/specs/S1_SPEC.md §6.  Numbers first, verdicts against pre-registered
rules only, no prose evaluation (ground rule 5: the execution agent writes tables
and summaries, never paper text).

Also runs the spec §7 reproduction check: the L1 pass through this harness must
match the banked A28.1 table to 0.001.  A failure emits DISCREPANCY_S1.md and is
reported as a halt, because if the harness cannot reproduce L1 then no L2 number
it produced means anything.
"""
import argparse
import csv
import json
import os

TOL = 0.001          # spec §7
ARMS = ["V", "S_LOTO_raw", "S_LOTO_quantile", "S_g_quantile", "S_oracle_pct",
        "S_mid_gap", "S_fitted"]


def read(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return list(csv.DictReader(f))


def fnum(r, k):
    v = r.get(k, "")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def repro_check(banked, l1, out_md):
    """Compare the harness's L1 pass to the banked table cell-by-cell, arm-by-arm."""
    if banked is None or l1 is None:
        return {"status": "absent",
                "detail": "banked=%s l1=%s" % (banked is not None, l1 is not None)}
    key = lambda r: (r["dataset"], r["assessor"], r["target"])
    B = {key(r): r for r in banked}
    L = {key(r): r for r in l1}
    only_b = sorted(set(B) - set(L))
    only_l = sorted(set(L) - set(B))
    diffs = []
    for k in sorted(set(B) & set(L)):
        for arm in ARMS:
            b, v = fnum(B[k], arm), fnum(L[k], arm)
            if b is None and v is None:
                continue
            if b is None or v is None or abs(b - v) > TOL:
                diffs.append((k, arm, b, v))
    status = "PASS" if not diffs and not only_b and not only_l else "FAIL"
    if status == "FAIL":
        lines = ["# DISCREPANCY — S1 L1 reproduction check\n",
                 "Spec: docs/specs/S1_SPEC.md §7. Tolerance %.3f.\n" % TOL,
                 "The L1 pass through the S1 harness must reproduce the banked A28.1 "
                 "table exactly: nothing but the code path changed. It did not.\n",
                 "**This branch halts.** L2 numbers from this harness are not "
                 "reportable until the difference is explained.\n",
                 "## Cells\n",
                 "- only in banked: %d" % len(only_b),
                 "- only in L1 pass: %d" % len(only_l),
                 "- arm values beyond tolerance: %d\n" % len(diffs)]
        if only_b:
            lines.append("Banked-only: %s\n" % ", ".join("%s|%s->%s" % k for k in only_b[:20]))
        if only_l:
            lines.append("L1-only: %s\n" % ", ".join("%s|%s->%s" % k for k in only_l[:20]))
        if diffs:
            lines.append("| dataset | assessor | target | arm | banked | L1 pass | diff |")
            lines.append("|---|---|---|---|---|---|---|")
            for (ds, a, t), arm, b, v in diffs[:60]:
                lines.append("| %s | %s | %s | %s | %s | %s | %s |"
                             % (ds, a, t, arm,
                                "n/a" if b is None else "%.4f" % b,
                                "n/a" if v is None else "%.4f" % v,
                                "n/a" if (b is None or v is None) else "%+.4f" % (v - b)))
        with open(out_md, "w") as f:
            f.write("\n".join(lines) + "\n")
    return {"status": status, "only_banked": len(only_b), "only_l1": len(only_l),
            "beyond_tol": len(diffs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", default="tables_S1")
    ap.add_argument("--banked",
                    default="figures/tables_gate2b1/gate2b1_cells_AGG-true_full.csv")
    ap.add_argument("--out", default="S1_SUMMARY.md")
    ap.add_argument("--discrepancy", default="DISCREPANCY_S1.md")
    a = ap.parse_args()

    js = os.path.join(a.tables, "S1abc_L2.json")
    abc = json.load(open(js)) if os.path.exists(js) else {}

    rep = repro_check(read(a.banked),
                      read(os.path.join(a.tables, "L1_L1",
                                        "gate2b1_cells_AGG-true_full.csv")),
                      a.discrepancy)

    L = []
    L.append("# S1 SUMMARY — stratified recompute + gate-2 L2 pass of record\n")
    L.append("Spec: `docs/specs/S1_SPEC.md`. Scope %s, seed %s, %s bootstrap draws.\n"
             % (abc.get("scope", "?"), abc.get("seed", "?"), abc.get("nboot", "?")))
    L.append("Labels: **L2 (gate-1) is the pass of record**; L1 reported beside it.\n")

    L.append("## Reproduction check (spec §7)\n")
    L.append("The L1 pass through this harness vs the banked A28.1 table, "
             "tolerance %.3f: **%s**" % (TOL, rep["status"]))
    if rep["status"] == "FAIL":
        L.append("\n%d cells only in banked, %d only in the L1 pass, %d arm values "
                 "beyond tolerance. See `%s`. **This branch halts.**\n"
                 % (rep["only_banked"], rep["only_l1"], rep["beyond_tol"],
                    a.discrepancy))
    elif rep["status"] == "absent":
        L.append("\nNot run: %s\n" % rep["detail"])
    else:
        L.append("\nEvery cell and every arm reproduces. Nothing but the label input "
                 "differs between this harness and the banked gates.\n")

    L.append("## S1a — crossprobe matrix per construct (L2)\n")
    L.append("| construct | cells | countable | underpowered | mean AUROC |")
    L.append("|---|---|---|---|---|")
    for c, v in (abc.get("constructs") or {}).items():
        L.append("| %s | %d | %d | %d | %s |"
                 % (c, v["cells"], v["countable"], v["underpowered"],
                    "n/a" if v["mean_auroc"] is None else "%.4f" % v["mean_auroc"]))
    L.append("")

    for tag, key, txt in (
            ("(i)", "A30_pred_i",
             "capable external superiority intact on violation+judgment"),
            ("(ii)", "A30_pred_ii",
             "self-probe inflation confined to outcome strata")):
        d = abc.get(key)
        if not d:
            continue
        L.append("## A30 §4 prediction %s — %s\n" % (tag, txt))
        if key == "A30_pred_i":
            L.append("**%s** — capable wins in %d/%d countable external cells; "
                     "pooled Δ %.4f, 95%% CI [%.4f, %.4f].\n"
                     % (d["verdict"], d["wins"], d["total"], d["pooled_delta"],
                        d["pooled_ci"][0], d["pooled_ci"][1]))
        else:
            L.append("**%s** — the self-minus-external gap is larger under `outcome` "
                     "than under `violation+judgment` in %d/%d arms; mean "
                     "difference-of-differences %.4f, 95%% CI [%.4f, %.4f].\n"
                     % (d["verdict"], d["larger"], d["arms"], d["mean_dd"],
                        d["ci"][0], d["ci"][1]))

    # independence, per construct
    L.append("## S1b — independence restatement (R3 obligation)\n")
    L.append("Best-self vs best-external per arm, paired episode-clustered CI on the "
             "difference. Negative Δ means the external judge reads the target better "
             "than the target reads itself.\n")
    for c in ["violation", "outcome", "judgment", "y_env", "violation+judgment"]:
        rows = read(os.path.join(a.tables, "S1b_independence_L2_%s.csv"
                                 % c.replace("+", "-")))
        if not rows:
            continue
        ok = [r for r in rows if fnum(r, "delta") is not None]
        if not ok:
            continue
        neg = sum(1 for r in ok if fnum(r, "delta") < 0)
        excl = sum(1 for r in ok
                   if fnum(r, "ci_lo") is not None and fnum(r, "ci_hi") is not None
                   and not (fnum(r, "ci_lo") <= 0 <= fnum(r, "ci_hi")))
        L.append("- **%s**: %d arms; external beats self in %d; %d have a CI "
                 "excluding 0." % (c, len(ok), neg, excl))
    L.append("")
    L.append("## Tables\n")
    for f in sorted(os.listdir(a.tables)):
        if f.endswith(".csv"):
            L.append("- `%s/%s`" % (a.tables, f))
    L.append("")
    with open(a.out, "w") as f:
        f.write("\n".join(L) + "\n")
    print("repro=%s -> %s" % (rep["status"], a.out))
    return 0 if rep["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
