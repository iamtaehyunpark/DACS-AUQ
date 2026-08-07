#!/usr/bin/env python3
"""S5 analysis — frontier (gpt-4o) vs mid-tier open judges. Resolves G2-R4.

Spec: EXECUTION_HANDOVER v2 §4.  gpt-4o is disjoint from the label ensemble, so no
column is marked contaminated.

The comparison is PAIRED on the frozen b3 sample: every open judge is re-scored on
exactly the steps gpt-4o saw, so a difference is judge quality and not sample.
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
import s1_labels as SL                   # noqa: E402
import s1_matrix as SM                   # noqa: E402

SEED = 13
NBOOT = 2000
CONSTRUCTS = ["violation+judgment", "judgment", "violation", "outcome", "y_env"]
CAPABLE = {"Llama-3.3-70B-Instruct", "Qwen3.6-35B-A3B"}


def load_b3(path):
    out = {}
    for line in open(path):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("U") is None:
            continue
        out[(r["dataset"], r["target"], r["task_id"], r["step_idx"])] = \
            (float(r["U"]), r.get("verdict"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b3", default="result/b3/b3.gpt-4o.jsonl")
    ap.add_argument("--cache", default="runs/score_cache_AGG-true.pkl")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--outdir", default="tables_S5")
    ap.add_argument("--summary", default="S5_SUMMARY.md")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    b3 = load_b3(a.b3)
    online = pickle.load(open(a.cache, "rb"))
    rng = np.random.default_rng(SEED)
    print("b3 records with U: %d" % len(b3), flush=True)

    rows = []
    for construct in CONSTRUCTS:
        lab = SL.load(a.labels, construct, in_matrix_only=True)
        # group the frozen sample by arm
        by_arm = collections.defaultdict(list)
        for (ds, tgt, task, sidx), (u, v) in b3.items():
            by_arm[(ds, tgt)].append((task, sidx, u, v))
        for (ds, tgt), items in sorted(by_arm.items()):
            L = lab.get((ds, tgt))
            if not L:
                continue
            keys = {(t, s) for t, s, _u, _v in items if (t, s) in L}
            if len(keys) < 40:
                continue
            # frontier cell
            fr = [(u, L[(t, s)][0], L[(t, s)][1], t)
                  for t, s, u, _v in items if (t, s) in L]
            if len({r[1] for r in fr}) < 2:
                continue
            c_fr = SM.Cell([(u, y, w, ep) for u, y, w, ep in fr])
            # each open judge, restricted to the SAME steps
            for assessor in sorted({k[1] for k in online if k[0] == ds and k[2] == tgt}):
                d = online.get((ds, assessor, tgt))
                if not d:
                    continue
                rs = [(d[k], L[k][0], L[k][1], k[0]) for k in keys if k in d]
                if len(rs) < 40 or len({r[1] for r in rs}) < 2:
                    continue
                c_op = SM.Cell(rs)
                delta, lo, hi = SM.boot_paired(c_fr, c_op, rng)
                rows.append({"construct": construct, "dataset": ds, "target": tgt,
                             "open_judge": assessor,
                             "capable": int(assessor in CAPABLE),
                             "n": c_op.n, "auroc_gpt4o": c_fr.auroc(),
                             "auroc_open": c_op.auroc(), "delta": delta,
                             "ci_lo": lo, "ci_hi": hi})
    SM.write_csv(os.path.join(a.outdir, "S5_frontier_vs_open.csv"), rows,
                 ["construct", "dataset", "target", "open_judge", "capable", "n",
                  "auroc_gpt4o", "auroc_open", "delta", "ci_lo", "ci_hi"])

    def summarise(construct, capable_only):
        rs = [r for r in rows if r["construct"] == construct
              and r["delta"] is not None
              and (r["capable"] == 1 if capable_only else True)]
        if not rs:
            return None
        d = [r["delta"] for r in rs]
        m, lo, hi = SM.boot_mean(d, rng) if hasattr(SM, "boot_mean") else (
            float(np.mean(d)), None, None)
        return {"n": len(rs), "mean": float(np.mean(d)),
                "wins": sum(1 for x in d if x > 0),
                "ci_excl": sum(1 for r in rs if r["ci_lo"] is not None
                               and r["ci_lo"] > 0),
                "lo": lo, "hi": hi}

    L = ["# S5 SUMMARY — frontier judge (gpt-4o) vs mid-tier open judges\n",
         "Resolves **G2-R4**. gpt-4o via Azure, disjoint from the label ensemble "
         "(`grok-4.3` / `DeepSeek-V4-Pro` / `gpt-5.6-sol`), so **no column is marked "
         "contaminated** and all three constructs are answerable.\n",
         "Sample: 1,188 steps, 11 in-matrix arms, 110/arm, stratified per A27, "
         "seed 13, frozen before the first call. 100%% top-1 Yes/No, 0 errors, "
         "~$2.85. One framing (the banked trust wording), one scope (AGG-true) — "
         "only the model differs.\n",
         "Δ = AUROC(gpt-4o) − AUROC(open judge), paired on identical steps, "
         "episode-clustered bootstrap.\n",
         "## Against the CAPABLE open judges (the decisive contrast)\n",
         "| construct | cells | mean Δ | gpt-4o wins | CI excludes 0 |",
         "|---|---|---|---|---|"]
    for c in CONSTRUCTS:
        s = summarise(c, True)
        if s:
            L.append("| %s | %d | %+.4f | %d/%d | %d |"
                     % (c, s["n"], s["mean"], s["wins"], s["n"], s["ci_excl"]))
    L.append("")
    L.append("## Against ALL open judges\n")
    L.append("| construct | cells | mean Δ | gpt-4o wins | CI excludes 0 |")
    L.append("|---|---|---|---|---|")
    for c in CONSTRUCTS:
        s = summarise(c, False)
        if s:
            L.append("| %s | %d | %+.4f | %d/%d | %d |"
                     % (c, s["n"], s["mean"], s["wins"], s["n"], s["ci_excl"]))
    L.append("")
    prim = summarise("violation+judgment", True)
    if prim:
        verdict = ("the frontier judge BEATS the capable open judges"
                   if prim["mean"] > 0 and prim["ci_excl"] * 2 >= prim["n"]
                   else "the frontier judge does NOT clearly beat the capable open "
                        "judges")
        L.append("## G2-R4\n")
        L.append("On the primary construct, against the capable stratum: mean Δ "
                 "**%+.4f** over %d cells, gpt-4o ahead in %d, CI excluding 0 in %d. "
                 "**%s.**\n"
                 % (prim["mean"], prim["n"], prim["wins"], prim["ci_excl"], verdict))
        L.append("Read with the cost column: gpt-4o cost ~$2.85 for 1,188 steps "
                 "(~$2.40/1k). The open judges are self-hosted; their marginal cost "
                 "is GPU time already owned.\n")
    L.append("## Tables\n- `%s/S5_frontier_vs_open.csv`\n" % a.outdir)
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")
    print("-> %s, %s" % (a.outdir, a.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
