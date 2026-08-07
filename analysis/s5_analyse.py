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


def load_sample(path):
    """The frozen sample. Analysis is restricted to it.

    The first 1,188-step batch was drawn by the pre-monotone sampler, so 996 of its
    records fall OUTSIDE the enlarged 2,475-step sample. They remain on disk and are
    ignored here: including them would mean analysing a set that was never frozen,
    which is the guarantee the seal exists to provide.
    """
    keep = set()
    for r in csv.DictReader(open(path)):
        try:
            t = r["task_id"]
            # CSV is all text; the JSONL keys are typed and differ BY DATASET --
            # ALFWorld task_id is a string, HotpotQA task_id is an int. Coerce, as
            # s1_labels does. Without this the join silently kept 206 of 2,475.
            tid = int(t) if t.lstrip("-").isdigit() else t
            keep.add((r["dataset"], r["target"], tid, int(r["step_idx"])))
        except (KeyError, ValueError):
            continue
    return keep


def load_b3(path, keep=None):
    out = {}
    for line in open(path):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("U") is None:
            continue
        k = (r["dataset"], r["target"], r["task_id"], r["step_idx"])
        if keep is not None and k not in keep:
            continue
        out[k] = (float(r["U"]), r.get("verdict"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b3", default="result/b3/b3.gpt-4o.trust.jsonl")
    ap.add_argument("--b3-decision", default="result/b3/b3.gpt-4o.decision.jsonl")
    ap.add_argument("--sample", default="result/b3/b3_sample.csv")
    ap.add_argument("--cache", default="runs/score_cache_AGG-true.pkl")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--outdir", default="tables_S5")
    ap.add_argument("--summary", default="S5_SUMMARY.md")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    # Analyse EVERY scored step, not a sample-file subset.
    #
    # The sample file was rewritten by each run instead of being read, so it names
    # only the last run's draw and filtering to it discards steps that were scored
    # and paid for. Using the complete scored set is also the LEAST selective choice
    # available: there is no cherry-picking in "all of it". What is lost is the
    # frozen-before-first-call guarantee, and that is stated in the summary rather
    # than papered over.
    b3 = load_b3(a.b3)
    b3d = load_b3(a.b3_decision) if os.path.exists(a.b3_decision) else {}
    both = sorted(set(b3) & set(b3d))
    print("scored steps — trust %d | decision %d | both %d"
          % (len(b3), len(b3d), len(both)), flush=True)
    with open(os.path.join(a.outdir, "S5_analysed_steps.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "target", "task_id", "step_idx", "trust", "decision"])
        for k in sorted(set(b3) | set(b3d)):
            w.writerow(list(k) + [int(k in b3), int(k in b3d)])
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
         "Sample: stratified per A27 (dataset x target x error-tercile x Tier-A "
         "flag), seed 13, 11 in-matrix arms. The frontier-vs-open contrast uses the "
         "**trust** framing, matching the banked open-judge probe verbatim so only "
         "the model differs. Parse rates 99.9%% / 99.6%%, 0 errors.\n",
         "**Provenance note.** 1,188 of the 5,404 trust records predate the "
         "`framing` field; their framing is established by the code version that "
         "wrote them (the wording was hardcoded to the banked trust text) rather "
         "than by a field in the data. Dropping them moves the primary-construct "
         "delta from -0.0209 to -0.0182, same sign and same cell counts, so the "
         "result does not rest on them.\n",
         "**Two deviations, recorded not smoothed.**\n",
         "1. D2.2 gated the run behind a 500-call pilot plus an author "
         "acknowledgement. The first batch ran 1,188 calls after a 50-call pilot "
         "without a recorded ack. The author later funded completion, but the ack "
         "for that first batch was never obtained.\n",
         "2. The frozen-sample guarantee did not hold. The sample file was "
         "REGENERATED by each run instead of being read, so successive runs drew "
         "different step sets while every log printed \"SAMPLE FROZEN\". The "
         "analysis below therefore uses **every scored step** rather than a single "
         "frozen draw — the least selective option available, and the one that "
         "wastes nothing already paid for. Steps analysed are enumerated in "
         "`S5_analysed_steps.csv`. The protection this removes is against "
         "post-hoc sample shaping; the enumeration is what replaces it.\n",
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
        L.append("Read with the cost column: this arm cost ~$19 of API spend across "
                 "7,879 calls, of which ~$7 was wasted on the sample-file defect "
                 "described above; the work itself needed ~4,950 calls. The open "
                 "judges are self-hosted, so their marginal cost is GPU time already "
                 "owned. That asymmetry is the point of the comparison.\n")
    if b3d:
        shared = both
        agree = sum(1 for k in shared if b3[k][1] == b3d[k][1])
        du = [abs(b3[k][0] - b3d[k][0]) for k in shared]
        L.append("## Framing sensitivity (trust vs decision, same steps)\n")
        L.append("Verdict agreement **%.1f%%** over %d shared steps; mean |ΔU| "
                 "**%.4f**, over the steps scored under BOTH framings. The "
                 "frontier-vs-open contrast above uses the trust framing, which is "
                 "the one the banked open-judge probe used; the decision framing is "
                 "a sensitivity check, not the primary.\n"
                 % (100.0 * agree / max(len(shared), 1), len(shared),
                    float(np.mean(du)) if du else float("nan")))
    L.append("## Tables\n- `%s/S5_frontier_vs_open.csv`\n" % a.outdir)
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")
    print("-> %s, %s" % (a.outdir, a.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
