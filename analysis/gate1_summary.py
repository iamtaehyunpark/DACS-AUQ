#!/usr/bin/env python3
"""Gate-1 GATE1_SUMMARY.md — the four pre-registered rules, each with its deciding number.

Reports against R1-R4 as written. It does not reinterpret them and it says nothing
evaluative beyond them.

  gate1_summary.py [--tables reports/gate1/tables_gate1] [--labels ...csv]
"""
import argparse
import collections
import csv
import json
import os

CAPABLE = ["Llama-3.3-70B-Instruct", "Qwen3.6-35B-A3B"]
ORDER = ["Llama-3.3-70B-Instruct", "Qwen3.6-35B-A3B", "Mistral-7B-Instruct-v0.3",
         "gemma-3-4b-it", "Phi-4-mini-instruct"]
F_FLOOR = 0.70
F_RANGE_MAX = 0.25
G_FLOOR = 0.85
CELL_DELTA = 0.05


def read_csv(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def load(p):
    return json.load(open(p)) if os.path.exists(p) else {}


def r1(fsep):
    """f >= 0.70 for the capable judges under y_env, and the ordering preserved."""
    env = fsep.get("env_restricted", {})
    got = {a: env.get(a) for a in ORDER}
    detail = []
    ok_floor = True
    for a in CAPABLE:
        d = got.get(a)
        if not d:
            ok_floor = False
            detail.append("%s: no cells under y_env" % a)
            continue
        detail.append("%s f=%.3f (range %.2f-%.2f, width %.2f, %d cells)"
                      % (a, d["mean"], d["min"], d["max"], d["range"], d["n_cells"]))
        if d["mean"] < F_FLOOR:
            ok_floor = False
    means = [(a, got[a]["mean"]) for a in ORDER if got.get(a)]
    ok_order = all(means[i][1] > means[i + 1][1] for i in range(len(means) - 1))
    deciding = min((got[a]["mean"] for a in CAPABLE if got.get(a)), default=None)
    return {
        "verdict": "PASS" if (ok_floor and ok_order) else "FAIL",
        "number": deciding,
        "number_label": "lowest capable-judge f under y_env",
        "floor_ok": ok_floor, "order_ok": ok_order,
        "observed_order": " > ".join("%s (%.3f)" % m for m in means),
        "detail": detail,
    }


def r2(gfit):
    """g's correlation below 0.85 for capable judges demotes g to a heuristic."""
    env = gfit.get("env_restricted", {})
    rows, worst = [], None
    for key, d in sorted(env.items()):
        scope, asr = key.split("/", 1)
        if asr not in CAPABLE or scope == "ALL":
            continue
        r = d.get("r")
        rows.append((key, r, d.get("n_targets")))
        if r is not None and (worst is None or abs(r) < abs(worst)):
            worst = r
    below = [k for k, r, _ in rows if r is None or abs(r) < G_FLOOR]
    return {
        "verdict": "FAIL" if below else "PASS",
        "number": worst,
        "number_label": "weakest capable-judge |r| for g (mean U vs error rate)",
        "below": below, "rows": rows,
    }


def r3(tables):
    """Any crossprobe AUROC cell moving more than 0.05 is flagged."""
    base = {(r["dataset"], r["target"], r["assessor"], r["scope"]): r
            for r in read_csv(os.path.join(tables, "ensemble", "crossprobe_matrix.csv"))}
    env = {(r["dataset"], r["target"], r["assessor"], r["scope"]): r
           for r in read_csv(os.path.join(tables, "env_restricted", "crossprobe_matrix.csv"))}
    moved, compared, biggest = [], 0, (0.0, None)
    for k, rb in base.items():
        re_ = env.get(k)
        if not re_ or not rb.get("auroc") or not re_.get("auroc"):
            continue
        compared += 1
        d = float(re_["auroc"]) - float(rb["auroc"])
        if abs(d) > abs(biggest[0]):
            biggest = (d, k)
        if abs(d) > CELL_DELTA:
            moved.append((k, float(rb["auroc"]), float(re_["auroc"]), d))
    moved.sort(key=lambda t: -abs(t[3]))
    return {
        "verdict": "FLAG" if moved else "PASS",
        "number": len(moved),
        "number_label": "cells moving more than %.2f AUROC (of %d compared)"
                        % (CELL_DELTA, compared),
        "compared": compared, "moved": moved, "biggest": biggest,
    }


def r4(labels_csv):
    """Ensemble error on Tier-A-settled steps, reported regardless of outcome."""
    n = c = 0
    soft = 0.0
    for r in read_csv(labels_csv):
        if r["in_matrix"] != "1" or r["y_tier_a"] != "1" or r["judge_present"] != "1":
            continue
        n += 1
        c += int(r["y_ensemble"] == "0")
        try:
            soft += float(r["judge_frac_correct"])
        except (ValueError, TypeError):
            pass
    return {
        "verdict": "REPORTED",
        "number": (c / n) if n else None,
        "number_label": "share of Tier-A-incorrect steps the ensemble called correct",
        "n": n, "correct": c, "soft": (soft / n) if n else None,
    }


def fmt(v, pat="%.3f"):
    return "—" if v is None else (pat % v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", default="reports/gate1/tables_gate1")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--out", default="reports/gate1/GATE1_SUMMARY.md")
    a = ap.parse_args()

    fsep = load(os.path.join(a.tables, "separation_f.json"))
    gfit = load(os.path.join(a.tables, "g_fit.json"))
    R = {"R1": r1(fsep), "R2": r2(gfit), "R3": r3(a.tables), "R4": r4(a.labels)}

    L = ["# GATE1_SUMMARY", "",
         "Each pre-registered rule with its verdict and the single number that decided "
         "it. Primary label `y_env`, restricted mode, scope SPLIT-action.", "",
         "| rule | verdict | deciding number | what it is |", "|---|---|---|---|"]
    L.append("| R1 | **%s** | %s | %s |" % (R["R1"]["verdict"], fmt(R["R1"]["number"]),
                                            R["R1"]["number_label"]))
    L.append("| R2 | **%s** | %s | %s |" % (R["R2"]["verdict"], fmt(R["R2"]["number"]),
                                            R["R2"]["number_label"]))
    L.append("| R3 | **%s** | %d | %s |" % (R["R3"]["verdict"], R["R3"]["number"],
                                            R["R3"]["number_label"]))
    L.append("| R4 | **%s** | %s | %s |" % (
        R["R4"]["verdict"],
        "—" if R["R4"]["number"] is None else "%.1f%%" % (100 * R["R4"]["number"]),
        R["R4"]["number_label"]))

    L += ["", "## R1 — qualification floors", "",
          "*If capable-judge f >= 0.70 under y_env and the assessor ordering is "
          "preserved, the qualification floors freeze.*", "",
          "- floor met: **%s**" % R["R1"]["floor_ok"],
          "- ordering preserved: **%s**" % R["R1"]["order_ok"],
          "- observed ordering: %s" % (R["R1"]["observed_order"] or "—")]
    L += ["- " + d for d in R["R1"]["detail"]]

    L += ["", "## R2 — the g fit", "",
          "*If g's correlation drops below 0.85 for capable judges, the deployment "
          "policy is reported quantile-only and g is demoted to heuristic.*", "",
          "| scope / assessor | r | targets |", "|---|---|---|"]
    for k, r, n in R["R2"]["rows"]:
        L.append("| %s | %s | %s |" % (k, fmt(r), n))
    if R["R2"]["below"]:
        L.append("")
        L.append("Below 0.85: %s" % ", ".join(R["R2"]["below"]))

    L += ["", "## R3 — crossprobe cell movement", "",
          "*If any cell moves by more than 0.05 AUROC, flag it; headline independence "
          "deltas must be restated from the env-labelled matrix.*", "",
          "%d of %d comparable cells move by more than 0.05. Largest move %s in %s."
          % (R["R3"]["number"], R["R3"]["compared"],
             fmt(R["R3"]["biggest"][0], "%+.3f"),
             " / ".join(R["R3"]["biggest"][1]) if R["R3"]["biggest"][1] else "—")]
    if R["R3"]["moved"]:
        L += ["", "| dataset | target | assessor | scope | ensemble | y_env | Δ |",
              "|---|---|---|---|---|---|---|"]
        for k, b, e, d in R["R3"]["moved"][:60]:
            L.append("| %s | %.3f | %.3f | %+.3f |" % (" | ".join(k), b, e, d))
        if len(R["R3"]["moved"]) > 60:
            L.append("")
            L.append("_%d further flagged cells in "
                     "`tables_gate1/crossprobe_side_by_side.md`._"
                     % (len(R["R3"]["moved"]) - 60))

    L += ["", "## R4 — ensemble error rate", "",
          "*Report regardless of outcome.*", "",
          "On the %d judged steps the environment labelled incorrect, the 3-judge "
          "ensemble called **%s** of them correct. Mean fraction of judges voting "
          "correct on those steps: %s."
          % (R["R4"]["n"],
             "—" if R["R4"]["number"] is None else "%.1f%%" % (100 * R["R4"]["number"]),
             fmt(R["R4"]["soft"]))]

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        f.write("\n".join(L) + "\n")
    with open(a.out.replace(".md", ".json"), "w") as f:
        json.dump(R, f, indent=2, default=str)
    print("\n".join(L[:12]))
    print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
