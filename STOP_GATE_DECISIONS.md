# STOP GATE DECISIONS — Author Acknowledgements
**2026-08-07 · Authoritative responses to S4_COST, S5_BUDGET, S6_DECISION, and the
spot-check package. Commit to repo; the harness may unhalt the named branches.**

## D1 — S4 hindsight-ceiling pass: **APPROVED**

Budget ceiling: **10 A100-hours** (the handover's own ceiling; the cheaper arithmetic is
noted but its throughput constant is unverified). Conditions:
1. Run the 500-step probe first; record the measured rate in the S4 log.
2. If probe-projected cost ≤ ceiling → proceed without further ack. If > ceiling →
   re-halt with the measured number.
3. Analyses as specced: per-cell hindsight−online Δ; hindsight-judge vs outcome-label
   agreement; R3 decomposition into information-gap vs construct-gap. All constructs.

## D2 — S5 frontier judge (b3): **PILOT APPROVED, full run held**

1. ~500-call pilot approved. Before any call: (a) verify whether deepseek exposes
   top_logprobs — if not, drop the logprob arm for that provider, never approximate it;
   (b) verify the chosen frontier model(s) are disjoint from the 3-model label-ensemble
   trio — if not disjoint, that provider's judgment-column comparison is marked
   contaminated in every table it appears in.
2. Report measured $/1k steps and projected full-run cost, then re-halt for the
   full 5,000-call ack.
3. Grading: pass of record = L2, all constructs, primary violation+judgment; the
   predicted construct asymmetry (frontier judge relatively stronger on the judgment
   column than the violation column) is pre-registered here as an observation to
   report, not a rule.

## D3 — S6 A25 kill-or-keep: **DROP**

1. Commit A31: retrospective-stream mechanism removed from the claim set, recorded as
   **untested** (not tested-and-failed); v4.1 thesis sentence retreats to the
   forward-stream form. Use the prepared texts.
2. Add migration note to A31: the mechanism is reserved for the author's follow-up MAS
   attribution work, where post-hoc scoring with realized observations is the native
   operating regime. No C5 corpus pass is run for this paper.

## D4 — Spot check (150-step human annotation): **DEFERRED by author**

1. Deferral is an author decision: annotation happens after the paper's safety
   milestone, not this week. The package stays ready; the item stays in
   OPEN_DECISIONS.md and weekly status until annotated.
2. **A32 (working assumption, disclosed):** until the spot check runs, judgment
   (3-judge ensemble) labels are treated as a proxy for human annotation. This is
   recorded as an assumption with its validation status split: **validated at ~2%
   error on the environment-certain band (gate-1 audit); untested on the contested
   band (pending spot check).** The paper's limitations section must state exactly
   this. A32 does not change the registered primary construct (violation+judgment,
   per A30 §5.3), and no shipped verdict is restated under it.

## New work item — A33 (final label-free attempt): **APPROVED as a free stage**

Spec in `GATE3_SPEC_A33.md`. Runs after S1 tables are re-read (the h-rule secondary may
already answer part of it). Floors decision (S8) is now sequenced AFTER A33 resolves,
since the qualification criteria depend on whether any label-free rule survives.

## Standing human items (unchanged, restated for the record)

Rewrite pass (after A33 + hindsight land) · floors freeze (after A33) · spot check
(deferred, above) · **Changdae conversation** — remains open, remains non-automatable,
now relevant to both papers.
