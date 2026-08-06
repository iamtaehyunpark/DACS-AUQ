#!/usr/bin/env python3
"""Decision packages for the STOP-gated stages: S4, S5, S6.

EXECUTION_HANDOVER.md §5/§6/§7.  These stages HALT for the author.  The execution
agent's job is to size them exactly and stop -- never to launch them.  Everything
here is arithmetic over runs/manifest.json and the label coverage; no inference.

Throughput is taken from the manifest and is flagged UNVERIFIED there: §1 requires a
500-step probe before any GPU stage sizes itself.  Every hour figure below is
therefore a RANGE with the unverified constant named, not a point estimate.
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s1_labels as SL          # noqa: E402

CAPABLE = ["Llama-3.3-70B-Instruct", "Qwen3.6-35B-A3B"]


def load_manifest(p):
    if not os.path.exists(p):
        raise SystemExit("manifest absent: %s (run S0)" % p)
    return json.load(open(p))


def matrix_arms(labels_csv):
    """(dataset, model) -> labelled step count, in-matrix only."""
    out = {}
    for r in SL.coverage(labels_csv, in_matrix_only=True):
        if r["construct"] != "y_env":
            continue
        out[(r["dataset"], r["model"])] = r["n"]
    return out


def cell_steps(man):
    """(ds, assessor, target) -> scored line count for the AGG-true file."""
    out = {}
    for c in man.get("cells", []):
        f = c["files"].get("AGG-true")
        if f:
            out[(c["dataset"], c["assessor"], c["target"])] = f["lines"]
    return out


def hours(n_assess, rate_per_5min, n_gpu=1):
    """Convert assessments to A100-hours at the inherited rate."""
    per_hour = rate_per_5min * 12.0
    return n_assess / per_hour / max(n_gpu, 1)


def fmt_h(h):
    return "%.1f" % h


def s4(man, arms, out):
    """Hindsight-ceiling pass: capable judges x all matrix arms, hindsight condition
    only (online is banked and reused)."""
    rate = man["throughput"]["assessments"]
    n_steps = sum(arms.values())
    n_assess = n_steps * len(CAPABLE)
    fast, slow = hours(n_assess, rate * 1.5), hours(n_assess, rate * 0.5)
    L = ["# S4_COST — hindsight-ceiling pass (STOP gate)\n",
         "**This branch is HALTED pending author budget acknowledgement "
         "(EXECUTION_HANDOVER.md §5).** Nothing has been launched.\n",
         "## Exact assessment count\n",
         "| judge | arms | steps per pass | assessments |", "|---|---|---|---|"]
    for j in CAPABLE:
        L.append("| %s | %d | %s | %s |" % (j, len(arms), "{:,}".format(n_steps),
                                            "{:,}".format(n_steps)))
    L.append("| **total** | %d | | **%s** |" % (len(arms), "{:,}".format(n_assess)))
    L.append("")
    L.append("Only the **hindsight** condition is new inference; the online (C3-grade "
             "prefix) condition is banked and reused, so this is one matrix pass, not "
             "two.\n")
    L.append("## Hours\n")
    L.append("At the inherited %d assessments / 5 min / A100 — flagged **unverified** "
             "in the manifest — one A100 gives %s A100-hours. Bracketing the rate at "
             "±50%% because §1 requires a 500-step probe before any GPU stage sizes "
             "itself: **%s – %s A100-hours**.\n"
             % (rate, fmt_h(hours(n_assess, rate)), fmt_h(fast), fmt_h(slow)))
    L.append("With all 5 A100s free (S0 capacity check), wall clock is roughly "
             "**%s – %s hours**.\n"
             % (fmt_h(fast / 5), fmt_h(slow / 5)))
    L.append("> **This sizing disagrees with the handover.** §5 estimates 6–10 "
             "A100-hours; the arithmetic here gives %s–%s. The handover figure is "
             "%.1fx the upper bound of this bracket. Either the inherited throughput "
             "constant is optimistic (likely — hindsight prompts are longer), or §5's "
             "estimate assumed both evidence conditions rather than the hindsight one "
             "alone. **The 500-step probe resolves which, and should be run before the "
             "author is asked to approve anything.** Until then treat 10 A100-hours as "
             "the number to budget against, not %s.\n"
             % (fmt_h(fast), fmt_h(slow), 10.0 / max(slow, 0.1), fmt_h(slow)))
    L.append("Hindsight prompts carry the full trajectory plus episode outcome, so "
             "they are LONGER than the banked online prompts and the true rate will "
             "be below the inherited constant. Treat the upper bound as the planning "
             "number.\n")
    L.append("## Per-arm breakdown\n")
    L.append("| dataset | arm | labelled steps | x2 judges |")
    L.append("|---|---|---|---|")
    for (ds, m), n in sorted(arms.items()):
        L.append("| %s | %s | %s | %s |" % (ds, m, "{:,}".format(n),
                                            "{:,}".format(n * 2)))
    L.append("")
    L.append("## What the author is being asked\n")
    L.append("Approve up to **10 A100-hours** (the handover's own §5 ceiling) "
             "for the hindsight condition; this document's arithmetic says %s–%s but "
             "the throughput constant behind it is unverified.\n\n"
             "A30 calls this the keystone: it converts the construct taxonomy from "
             "argument into measurement, and decomposes the R3 movements into "
             "information-gap vs construct-gap. S1d raises the stakes — the "
             "construct choice now decides a gate verdict, not just a framing.\n"
             % (fmt_h(fast), fmt_h(slow)))
    open(out, "w").write("\n".join(L) + "\n")
    return n_assess


def s5(man, arms, out):
    """b3 frontier API judge on a stratified subsample."""
    n_sub = 2500          # A27: 2-3k stratified
    arms_n = len(arms)
    per_arm = n_sub // arms_n
    # two framings x (verdict + logprob in one call) x 1 frontier model
    calls = n_sub * 2
    L = ["# S5_BUDGET — frontier external judge b3 (STOP gate)\n",
         "**This branch is HALTED pending author budget acknowledgement "
         "(EXECUTION_HANDOVER.md §6).** No API key is used and no call is made "
         "until then.\n",
         "## Sample\n",
         "Stratified per A27: target x dataset x error-tercile x TierA-flag. "
         "Target **%s steps** across %d in-matrix arms (~%d per arm), frozen before "
         "sampling, seed logged.\n" % ("{:,}".format(n_sub), arms_n, per_arm),
         "## Calls\n",
         "| arm | framing | calls |", "|---|---|---|",
         "| frontier verdict | decision-framed | %s |" % "{:,}".format(n_sub),
         "| frontier verdict | trust-framed | %s |" % "{:,}".format(n_sub),
         "| **total** | | **%s** |" % "{:,}".format(calls), "",
         "P(True) comes from the same calls via `top_logprobs` where the provider "
         "exposes it (OpenAI: yes; deepseek: **verify before sizing** — if not "
         "exposed, text verdict only and the logprob arm is dropped, not faked).\n",
         "## Cost\n",
         "Cost per call depends on prompt length, which is the banked AGG-true "
         "evidence context. The manifest pins those files; a 500-call pilot on one "
         "arm gives the token-per-call figure. **A dollar estimate without that "
         "pilot would be a guess, and this document does not make one.**\n",
         "The comparison column the handover requires is $/1k steps for the frontier "
         "arm against measured self-hosted throughput for the best open-tier arm from "
         "S1d.\n",
         "## What the author is being asked\n",
         "1. Approve a ~500-call pilot to fix the per-call cost (small, bounded).\n"
         "2. Then approve or decline the full %s calls at the measured rate.\n"
         "3. Confirm the provider list, and whether deepseek exposes top_logprobs.\n"
         % "{:,}".format(calls),
         "G2-R4 resolves here.\n"]
    open(out, "w").write("\n".join(L) + "\n")
    return calls


def s6(man, arms, out, s1_verdict_note):
    """A25 kill-or-keep decision package."""
    rate = man["throughput"]["assessments"]
    n_steps = sum(arms.values())
    n_assess = n_steps * len(CAPABLE)
    fast, slow = hours(n_assess, rate * 1.5), hours(n_assess, rate * 0.5)
    L = ["# S6_DECISION — A25 kill-or-keep (STOP gate)\n",
         "**HALTED for author decision (EXECUTION_HANDOVER.md §7).** Silent drop is "
         "prohibited; the wording is committed in v4.1.\n",
         "## The decision\n",
         "KEEP → run the C5 retrospective-stream corpus pass, then P1/P2 per v4.1 "
         "§6d. DROP → commit A31 demotion plus the thesis-sentence retreat wording.\n",
         "## Cost if KEEP\n",
         "C5 is a capable-judge pass over the same matrix arms: **%s assessments**, "
         "**%s – %s A100-hours** at the unverified inherited rate (same bracketing as "
         "S4).\n" % ("{:,}".format(n_assess), fmt_h(fast), fmt_h(slow)),
         "## What P1/P2 would test\n",
         "- **P1**: retrospective-stream p̂ convergence against the forward stream.\n"
         "- **P2**: two-phase vs forward-only gating at equal budget.\n",
         "## Evidence now bearing on the decision\n",
         s1_verdict_note,
         "\n## Prepared text for the DROP branch\n",
         "A31 demotion: the retrospective-stream mechanism is removed from the "
         "claim set and recorded as untested, not as tested-and-failed. The v4.1 "
         "thesis sentence retreats to the forward-stream form. Both texts are drafted "
         "when the author picks DROP — per ground rule 5 the execution agent does not "
         "write paper text unprompted.\n"]
    open(out, "w").write("\n".join(L) + "\n")
    return n_assess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="runs/manifest.json")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    man = load_manifest(a.manifest)
    arms = matrix_arms(a.labels)

    note = ("S1d put the batch g-rule at **G2b1-R3 FAIL** on the A30-primary construct "
            "`violation+judgment` (P-g2 77% vs an 80% bar; capture 0.455 vs 0.5), and "
            "S2 had already flagged both statistics as `soften` at L1. The label-free "
            "cut is therefore not an established result that A25 would extend — it is "
            "an unestablished one. That bears directly on whether the retrospective "
            "stream is worth GPU hours, and is stated here rather than left for the "
            "author to reconstruct.")

    n4 = s4(man, arms, os.path.join(a.outdir, "S4_COST.md"))
    n5 = s5(man, arms, os.path.join(a.outdir, "S5_BUDGET.md"))
    n6 = s6(man, arms, os.path.join(a.outdir, "S6_DECISION.md"), note)
    print("S4_COST.md      %s assessments" % "{:,}".format(n4))
    print("S5_BUDGET.md    %s calls" % "{:,}".format(n5))
    print("S6_DECISION.md  %s assessments if KEEP" % "{:,}".format(n6))
    print("all three are STOP gates: halted, nothing launched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
