# GATE-2b.1 SPEC (A28.1) — The Error-Rate-Indexed Cut
## Testing the arm A28 should have specified

**2026-08-06 · Pre-registered before any arm is computed. Commit before running.**
**Status of A28: G2b-R3 FAIL on the capable stratum stands in the record — it is a valid
verdict on FIXED-percentile transfer. A28.1 is a new gate on the error-rate-INDEXED rule
(the §6d rule as actually written), not a re-roll of A28. This distinction is the point
of pre-registration and is not negotiable after results exist.**

## Plain statement of the question

A cut transferred as a fixed percentile ("flag the top 40% everywhere") failed on
capable judges, losing precisely where the target's error rate differed from the fitting
pool's. The deployment rule was never a fixed percentile: it flags the top p̂%, where p̂
is the target's error rate, estimated label-free from the judge's own mean score. Does
the indexed rule beat the verdict where the fixed rule could not?

## Arms (added; A28 arms V / S-LOTO-raw / S-LOTO-quantile / S-fitted retained as anchors)

- **S-g-quantile** — the §6d rule, LOTO-disciplined:
  1. On the other targets of the same assessor × dataset, fit g: linear regression of
     true error rate on mean judge score (one point per target; macro, not per-step).
  2. For the held-out target: p̂ = g(mean of its UNLABELED scores), clipped to [0.02, 0.98].
  3. Cut at percentile 100·(1 − p̂) of the target's unlabeled score distribution.
  Target labels used: zero. Target data used: raw scores only.
- **S-oracle-pct** — cut at percentile 100·(1 − true base rate). Uses one number of label
  information (the base rate). Upper bound for percentile-indexed placement; not a method.
- **S-mid-gap** (diagnostic, free): cut at the midpoint of the widest empty interval in
  the target's score distribution. If the bimodality story is right, this label-free,
  transfer-free arm should approach S-fitted; if it does, the "any cut in the gap works"
  mechanism is confirmed from a third direction.

## Distribution-shape deliverable (confirmatory, was exploratory)

Per capable cell: (a) balanced accuracy as a function of cut percentile (the flatness
curve); (b) score histogram with mass-at-extremes (share of scores < 0.1 and > 0.9) and
widest-gap location/width. One figure per assessor × dataset; summary table of gap
widths. This is the mechanism exhibit for why verdicts are strong, why raw cuts
transfer, and why fixed percentiles misfire.

## Audit fix (blocking, runs first)

A28's V was computed on the subset of steps whose verdict token parsed; S arms used all
steps. Report parse rate per cell. If any cell < 99%: recompute ALL arms on the
step-matched (parsed) subset and report both; step-matched is primary.

## Metrics & primacy (fixed now, learning from A28's ambiguity)

- Decisive stratum: **CAPABLE (Llama-3.3-70B, Qwen3.6-35B)**. Declared here, before
  results; the all-judges stratum is reported as context. (Folds in the A29 declaration.)
- Capture ratio primary form: **pooled** Σ(arm − V) / Σ(S-fitted − V) over unsaturated
  countable cells. Mean-of-ratios reported as secondary (A28 showed it is dominated by
  single near-zero-denominator cells). This primacy choice is made before computing
  S-g-quantile and applies to it.
- Cell counting rules unchanged from A28 (pool ≥ 3, saturated = fitted − V ≤ 0.01).
- CIs: percentile bootstrap over cells, 2000 draws, as in A28.

## Pre-registered predictions

- P-g1: S-g-quantile ≥ S-LOTO-quantile (fixed) in a majority of capable cells, with the
  largest gains in cells where |pct_pool − 100(1−base)| was largest (incl. the
  alfworld/Qwen→deepseek cell, A28's only large loss).
- P-g2: S-g-quantile ≥ V in ≥ 80% of capable countable cells.
- P-gap: S-mid-gap within 0.01 of S-fitted in a majority of capable cells (bimodality
  mechanism).
- P-shape: mass-at-extremes > 50% and a nonzero-width gap in every capable cell.

## Decision rules

- **G2b1-R1 (PASS):** P-g2 holds AND pooled capture(S-g-quantile) ≥ 0.5 on the capable
  stratum → the §6d deployment rule survives at decision level (batch form; sequential
  variant remains paper work). §6d wording keeps "label-free," annotated
  "error-rate-indexed, not fixed-percentile."
- **G2b1-R2 (PARTIAL):** P-g2 holds, capture < 0.5 → label-free indexed transfer works
  but thinly; §6d leads with the ~200-label calibrated tier, indexed transfer as
  fallback.
- **G2b1-R3 (FAIL):** P-g2 fails → the label-free deployment claim is dropped on capable
  judges; the paper's §6d is rewritten around: (i) verdict-strength finding, (ii)
  bimodality/flat-gap mechanism, (iii) labeled calibration, (iv) controllability. Written
  down now so it cannot be argued away later.
- Whatever fires: the A28 FAIL of fixed-percentile transfer is reported alongside, not
  replaced.

## Cross-dataset probe (secondary, cheap, informs the §7.1 rewrite)

Apply each assessor's alfworld pooled raw cut to its hotpotqa cells and vice versa.
Prediction: raw transfer degrades across datasets (the gap moves) — locating §7.1's
threshold-non-transfer claim at the cross-environment boundary, where it belongs, rather
than cross-target within an environment, where A28 falsified it.

## Labels, sequencing, cost

L1 (ensemble) preview now; L2 (gate-1 environment-anchored) pass of record. Extension of
gate2b_cut_transfer.py (~80 lines: g fit, three arms, histogram/curve dump). Zero
inference. Audit fix → arms → curves → summary.

## Deliverables

`tables_gate2b1/` per-cell table (all seven arms + parse rate + gap stats, both label
passes); `figures_gate2b1/` flatness curves + histograms per assessor × dataset;
`GATE2B1_SUMMARY.md` — one page: P-g1/P-g2/P-gap/P-shape and G2b1-R1..R3 with the
deciding numbers; the A28 verdict restated beside the A28.1 verdict.
