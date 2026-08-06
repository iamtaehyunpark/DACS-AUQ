# GATE-3 SPEC (A33) — Final Label-Free Attempt, With Closure
## Mixture cut · violation-calibrated cut · h-rule check

**2026-08-07 · Pre-registered before any arm is computed. Commit before running.**
**This is label-free attempt #3 (after A28 fixed-percentile FAIL and A28.1 g-rule
FAIL-on-record). The closure clause in §6 is the point of this spec: whatever happens,
the label-free line ends here for this paper.**

## 0. Standing context

The prize is bounded: fitted ceiling − verdict ≈ +0.048 balanced accuracy on capable
cells; the g-rule captured ~half and failed its pass of record on the primary construct
(P-g2 77% vs 80; capture 0.455 vs 0.5). The documented failure mode was the indexing
identity (optimal flag-rate ≠ error-rate; the oracle percentile itself lost on half the
failing cells, oracle capture ceiling 0.67). New arms must therefore escape the
percentile-indexing family, not refine it.

## 1. Data, labels, evaluation frame

Banked per-step P(True) scores, same cells and counting rules as A28/A28.1 (pool ≥ 3,
saturated = fitted − V ≤ 0.01). Labels: **L2, all constructs reported, primary =
violation+judgment** (A30 §5.3; unchanged by A32). Decisive stratum: capable
(Llama-70B, Qwen-35B). Seed 13, 2000-draw cell bootstrap. Anchors reported in every
table: V, S-LOTO-quantile, S-g-quantile, S-oracle-pct, S-fitted.

## 2. Arm 0 (read before computing anything) — the h-rule from S1 secondaries

The direct percentile map (pct* ~ mean-U, pool-fitted) was pre-registered as an S1
secondary. First action: read those tables. If computed, record its capable-stratum
pass-rate and capture per construct in this gate's summary as an anchor; if it already
clears §5's bars, arms 1–2 still run (they are registered), but the summary says so
plainly. If not computed, compute it here exactly as the S1 spec defined it.

## 3. Arm 1 (primary) — mixture cut

Motivation from banked shape findings: scores are strongly bimodal (mass-at-extremes
0.82–0.90 median). Procedure, fixed now:
1. Logit-transform the held-out target's unlabeled scores (clip to [1e-4, 1−1e-4]).
2. Fit a 1-D two-component Gaussian mixture by EM (k-means init, 200 iters, tol 1e-6,
   3 restarts, best likelihood).
3. Cut at the equal-posterior boundary between components, mapped back to score space.
4. Degenerate guards (pre-registered): if EM collapses (component weight < 0.05 or
   |μ1−μ2| < 0.25 logits), the arm ABSTAINS on that cell and the cell counts as a loss.
   No fallback to other rules — fallbacks are how a third attempt becomes a fourth.
Uses: target's unlabeled scores only. Zero labels, zero transfer from the pool.

## 4. Arm 2 (secondary claim, different wording) — violation-calibrated cut

Procedure: fit the balanced-accuracy-optimal cut on the held-out target's OWN steps
using violation labels as the positive class and all non-violation steps as (noisy)
negatives; evaluate on the full primary construct. Uses: labels the environment emits
automatically in any deployment log (inadmissible / repeat / no-op) — zero human
labels, but not zero labels. If it passes, its claim wording is **"human-annotation-
free, environment-self-calibrating"**, never "label-free". Pre-registered risk, to be
reported either way: violation steps are gross failures, so the fitted cut may sit
wrong for subtle errors (measured as its recall on judgment-only-incorrect steps vs
the fitted anchor's).

## 5. Decision rules (identical bars to A28.1; no bar shopping)

Per arm, capable stratum, primary construct:
- **PASS**: arm ≥ V in ≥ 80% of countable cells AND pooled capture ≥ 0.5.
- **PARTIAL**: pass-rate ≥ 80% only.
- **FAIL**: otherwise.
CIs reported on both statistics; a PASS whose CIs straddle both bars is reported as
"PASS (marginal)" — the same honesty label A28.1 carried.

## 6. Closure clause (binding)

If NO arm reaches PASS on the primary construct: **the label-free line is closed for
this paper.** §6d leads with the ~200-label calibrated tier (which passed under every
construct), the label-free attempts ship as a documented negative result with the
mechanism analysis (indexing-identity failure, construct-dependence, self-consistency
of judge-derived cuts), and no further label-free rule is proposed, computed, or
discussed in this paper regardless of ideas that arise during writing. If an arm
PASSES: §6d recovers a label-free (or human-free, per §4 wording) deployment story
with this gate as its provenance, and the A28/A28.1 verdicts remain beside it in the
record. Either way, the floors decision (S8) proceeds on this gate's outcome.

## 7. Deliverables

`tables_gate3/` per-cell all-arms table (all constructs, both label passes where
applicable); `GATE3_SUMMARY.md` — one page: arm 0 anchor, arms 1–2 verdicts with the
deciding numbers, closure-clause status (INVOKED / NOT INVOKED), and the single
sentence §6d will lead with as a result.
