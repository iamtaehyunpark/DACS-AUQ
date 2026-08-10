#!/usr/bin/env python3
"""Item 4 — registry and bundle hygiene.

1. Fix the CI-registry A28.1 row to the L2 pass of record (77% / 0.455). The banked
   row carried the L1 preview numbers (81.8% / 0.555), which is the wrong pass: L2 is
   the pass of record and L1 was explicitly a preview. One row changed, logged.
2. Apply "PASS (marginal)" wherever a pass-rate CI straddles its bar.
3. Re-title the bootstrap ladder as the label-source menu, with the
   violation-calibrated outcome collapse and the day-one/h ordering stated as-is.
"""
import argparse
import csv
import os
import sys

# L2 pass of record, capable stratum, primary construct violation+judgment
# (tables_S1/L2_violation-judgment/S1d_A28_1_console.txt).
A28_1_L2 = {"pass_rate": 17.0 / 22.0, "pass_n": "17/22", "capture": 0.455}
A28_1_L1 = {"pass_rate": 18.0 / 22.0, "capture": 0.5552}


def load(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def fnum(r, k):
    try:
        return float(r.get(k, ""))
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="tables_S2/ci_registry.csv")
    ap.add_argument("--topup", default="tables_P3/S2_ci_registry_topup.csv")
    ap.add_argument("--ladder", default="tables_P3/bootstrap_ladder.csv")
    ap.add_argument("--outdir", default="tables_bundle")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    changelog = []

    # ---- 1 + 2: unified registry --------------------------------------
    rows = []
    for r in load(a.registry):
        cid = r.get("claim_id", "")
        if cid == "C-g2":
            changelog.append(
                "C-g2: estimate %.4f -> %.4f, n 22 (L1 preview -> L2 pass of record). "
                "The banked row reported the L1 preview pass-rate 18/22; the pass of "
                "record is L2 at 17/22 on the primary construct."
                % (fnum(r, "estimate") or A28_1_L1["pass_rate"], A28_1_L2["pass_rate"]))
            r["estimate"] = "%.4f" % A28_1_L2["pass_rate"]
            r["note"] = ("L2 pass of record, primary construct violation+judgment "
                         "(%s). CI is the L1-era interval; the point estimate is L2."
                         % A28_1_L2["pass_n"])
        elif cid == "C-cap":
            changelog.append(
                "C-cap: estimate %.4f -> %.4f (L1 preview -> L2 pass of record)."
                % (fnum(r, "estimate") or A28_1_L1["capture"], A28_1_L2["capture"]))
            r["estimate"] = "%.4f" % A28_1_L2["capture"]
            r["note"] = ("L2 pass of record, primary construct violation+judgment. "
                         "CI is the L1-era interval; the point estimate is L2.")
        # the banked registry names the text column "claim"; the top-up names it
        # "quantity". Normalise so neither set of rows loses its description.
        if not r.get("quantity"):
            r["quantity"] = r.get("claim", "")
        rows.append(r)
    for r in load(a.topup):
        rows.append({"claim_id": r["claim_id"], "quantity": r["quantity"],
                     "estimate": r["estimate"], "ci_lo": r["ci_lo"],
                     "ci_hi": r["ci_hi"], "null_value": r["null_value"],
                     "method": "cell bootstrap, 2000", "n": r["n"],
                     "source_table": r["source"], "status": r["status"],
                     "note": ""})

    # marginal labelling
    for r in rows:
        lo, hi, nv = fnum(r, "ci_lo"), fnum(r, "ci_hi"), fnum(r, "null_value")
        est = fnum(r, "estimate")
        if lo is None or hi is None or nv is None or est is None:
            continue
        straddles = lo <= nv <= hi
        if straddles and est >= nv:
            r["verdict_label"] = "PASS (marginal)"
        elif straddles:
            # below the bar with a CI that spans it: the verdict is FAIL and the
            # interval cannot separate it from the bar. Both facts belong in the label.
            r["verdict_label"] = "FAIL (CI spans bar)"
        else:
            r["verdict_label"] = "clear"
    # Part D is explicitly no-claim
    for r in rows:
        if r.get("claim_id") == "C-crossenv-h":
            r["verdict_label"] = "no-claim"
            r["note"] = ("Part D carries NO success criterion. CI includes 0, so the "
                         "cross-environment result is reported as consistent with no "
                         "degradation and is not claimed as transfer.")

    cols = ["claim_id", "quantity", "estimate", "ci_lo", "ci_hi", "null_value",
            "verdict_label", "method", "n", "source_table", "status", "note"]
    out = os.path.join(a.outdir, "ci_registry_final.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---- 3: label-source menu -----------------------------------------
    lad = load(a.ladder)
    NAMES = {"day1_violation_calibrated": "day one — violation-calibrated",
             "label_200_fitted": "~200 labels — fitted cut",
             "steady_state_h": "steady state — h-rule"}
    menu = []
    for r in lad:
        menu.append({"construct": r["construct"],
                     "route": NAMES.get(r["tier"], r["tier"]),
                     "human_labels_required": ("0" if "violation" in r["tier"] or
                                               "steady" in r["tier"] else "~200"),
                     "label_source": r["label_source"],
                     "time_to_deploy": r["time_to_deploy"],
                     "mean_ba": r["mean_ba"], "ci_lo": r["ci_lo"],
                     "ci_hi": r["ci_hi"]})
    lout = os.path.join(a.outdir, "label_source_menu.csv")
    with open(lout, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["construct", "route",
                                          "human_labels_required", "label_source",
                                          "time_to_deploy", "mean_ba", "ci_lo",
                                          "ci_hi"])
        w.writeheader()
        for r in menu:
            w.writerow(r)

    with open(os.path.join(a.outdir, "REGISTRY_CHANGELOG.md"), "w") as f:
        f.write("# CI registry changelog\n\n**2026-08-08 · item 4**\n\n")
        for c in changelog:
            f.write("- %s\n" % c)
        f.write("\nNo other estimate, interval or status was altered. "
                "Rows from the GATE-3/4 top-up were appended, not merged over "
                "existing rows.\n")
    print("registry -> %s (%d rows, %d corrected)" % (out, len(rows), len(changelog)))
    print("menu     -> %s (%d rows)" % (lout, len(menu)))
    for c in changelog:
        print("  " + c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
