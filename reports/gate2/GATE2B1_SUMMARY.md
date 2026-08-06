# GATE-2b.1 (A28.1) — Error-Rate-Indexed Cut: Results

Spec: `docs/GATE2B1_SPEC_A28_1.md` (pre-registered, committed `7df1f66`).
Scope AGG-true. Labels L1 (3-judge ensemble) — PREVIEW pass; L2 rerun owed.
Tables: `figures/tables_gate2b1/gate2b1_cells_AGG-true_full.csv`,
`figures/tables_gate2b1/gate2b1_console_AGG-true.txt`.
Curves: `figures/figures_gate2b1/flatness_curves_AGG-true.csv`,
`figures/figures_gate2b1/score_histograms_AGG-true.csv`.

Table tag is `_full` because the audit cleared: a `_unmatched` table is emitted
only when a step-matched pass exists beside it.

60 cells collected. Capable stratum (Llama-3.3-70B, Qwen3.6-35B assessors):
22 countable, 16 unsaturated, 0 g-degenerate. All judges: 55 countable
(5 excluded for pool < 3), 46 unsaturated, 0 g-degenerate.

## Blocking audit

Parse rate min **1.00000** across all 60 cells; cells below 99%: **0**.
V and the S arms share identical step sets. The step-matched recomputation
path did not fire; a single full pass is primary.

## Arm means (balanced accuracy, 95% percentile bootstrap over cells, 2000 draws)

| arm | CAPABLE (n=22) | ALL JUDGES (n=55) |
|---|---|---|
| V (argmax verdict) | 0.727 [0.701, 0.755] | 0.590 [0.558, 0.622] |
| S-LOTO-raw | 0.732 [0.699, 0.764] | 0.639 [0.612, 0.666] |
| S-LOTO-quantile | 0.752 [0.733, 0.770] | 0.644 [0.617, 0.671] |
| **S-g-quantile** | **0.753 [0.725, 0.780]** | **0.639 [0.610, 0.668]** |
| S-oracle-pct | 0.757 [0.734, 0.780] | 0.641 [0.612, 0.669] |
| S-mid-gap | 0.719 [0.692, 0.749] | 0.586 [0.556, 0.618] |
| S-fitted (labeled ceiling) | 0.775 [0.757, 0.792] | 0.657 [0.628, 0.685] |

## Capture ratio (pooled primary; mean-of-ratios secondary)

| arm | CAPABLE pooled | 95% CI | mean-of-ratios | ALL pooled | 95% CI |
|---|---|---|---|---|---|
| S-LOTO-quantile | 0.654 | [0.481, 0.779] | 0.552 | 0.843 | [0.770, 0.902] |
| **S-g-quantile** | **0.555** | **[0.084, 0.844]** | 0.340 | 0.738 | [0.588, 0.857] |
| S-oracle-pct | 0.671 | [0.448, 0.831] | 0.590 | 0.777 | [0.686, 0.853] |
| S-mid-gap | −0.161 | [−0.332, −0.027] | −0.148 | −0.057 | [−0.124, −0.015] |

## Realized vs requested flag rate

|realized_flag − (1 − requested percentile)|, over all cut-percentile arms:

| arm | mean | max |
|---|---|---|
| S-g-quantile | 0.000 | 0.001 |
| S-LOTO-quantile | 0.000 | 0.000 |
| S-oracle-pct | 0.000 | 0.000 |

Requested percentiles are realized to within 0.001. No tie-lumping.

## Pre-registered predictions

**P-g1** — S-g-quantile ≥ S-LOTO-quantile in a majority of capable cells:
**15/22 (68%)** capable; 30/55 (55%) all judges. **HOLDS** on the capable stratum.

Named test case `alfworld / Qwen3.6-35B-A3B → deepseek-v4-flash` (A28's only
large loss): V 0.797, S-LOTO-quantile 0.711 (−0.086 vs V), **S-g-quantile 0.800
(+0.003 vs V)**, S-fitted 0.772. The cell flips from loss to win, and the
indexed cut exceeds the per-target labeled fit.

Eight cells where the indexed cut converts a fixed-percentile loss into a
win (quantile < V ≤ g):

| dataset | assessor | target | V | quantile | g |
|---|---|---|---|---|---|
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | 0.797 | 0.711 | 0.800 |
| alfworld | Llama-3.3-70B | deepseek-v4-flash | 0.715 | 0.704 | 0.742 |
| alfworld | Llama-3.3-70B | Llama-3.3-70B | 0.762 | 0.743 | 0.767 |
| hotpotqa | Llama-3.3-70B | Phi-4-mini | 0.826 | 0.806 | 0.828 |
| hotpotqa | Llama-3.3-70B | Mistral-7B-v0.3 | 0.769 | 0.753 | 0.772 |
| alfworld | Phi-4-mini | gemma-3-4b-it | 0.509 | 0.504 | 0.522 |
| alfworld | Phi-4-mini | Phi-4-mini | 0.480 | 0.477 | 0.483 |
| alfworld | Phi-4-mini | Mistral-7B-v0.3 | 0.478 | 0.476 | 0.481 |

**P-g2** — S-g-quantile ≥ V in ≥ 80% of capable countable cells:
**18/22 (82%)**, 95% CI [64%, 95%]. **HOLDS** at the point estimate; the CI
spans the 80% threshold. All judges: 49/55 (89%), CI [80%, 96%].

Six cells where S-g-quantile < V:

| dataset | assessor | target | V | g | Δ | stratum |
|---|---|---|---|---|---|---|
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | 0.756 | 0.597 | −0.159 | capable |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | 0.628 | 0.602 | −0.026 | capable |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B | 0.759 | 0.734 | −0.026 | capable |
| alfworld | Phi-4-mini | Llama-3.3-70B | 0.527 | 0.520 | −0.007 | |
| hotpotqa | Llama-3.3-70B | gemma-3-4b-it | 0.833 | 0.830 | −0.003 | capable |
| alfworld | Phi-4-mini | Qwen3.6-35B-A3B | 0.496 | 0.494 | −0.002 | |

Both self-cells of Qwen3.6-35B-A3B are among the failures, and supply the
single largest loss (−0.159).

**P-gap** — S-mid-gap within 0.01 of S-fitted in a majority of capable cells:
**5/22 (23%)** capable; 8/55 (15%) all judges. **FAILS.**

Median |S-mid-gap − S-fitted| = 0.049 capable, 0.061 all judges (max 0.199).
Median |S-mid-gap − V| = **0.001**; |S-mid-gap − V| ≤ 0.01 in **53/60 cells**.
Median gap midpoint = 0.475 capable, 0.515 all judges. The widest empty
interval sits at the renormalized 0.5 boundary, so the mid-gap cut reproduces
the verdict cut rather than the fitted cut. Capture ratio for S-mid-gap is
negative in both strata.

**P-shape** — mass-at-extremes > 50% and a nonzero-width gap in every capable
cell: mass criterion met in **17/22 (77%)** capable, 45/55 (82%) all judges.
Not every cell. Gap widths: capable min 0.016, median 0.062, max 0.062;
all judges min 0.016, median 0.062, max 0.381; width > 0.05 in 11/22 capable
and 40/55 all judges. Median mass-at-extremes 0.822 capable, 0.897 all judges.

## Decision rule

P-g2 holds (18/22 = 82% ≥ 80%) AND pooled capture(S-g-quantile) = 0.555 ≥ 0.5
on the capable stratum.

**==> G2b1-R1 PASS.**

Both deciding quantities sit near their thresholds and their CIs straddle
them: P-g2 CI [64%, 95%] spans 80%; capture CI [0.084, 0.844] spans 0.5.

## A28 verdict restated beside A28.1

| gate | rule tested | capable stratum | all judges |
|---|---|---|---|
| **A28** (GATE-2b) | fixed-percentile transfer (S-LOTO-quantile) | P-quantile 15/22 (68%) < 80% → **G2b-R3 FAIL** | P-quantile 44/55 (80%), capture 0.775 → **G2b-R1 PASS** |
| **A28.1** (GATE-2b.1) | error-rate-indexed transfer (S-g-quantile) | P-g2 18/22 (82%), pooled capture 0.555 → **G2b1-R1 PASS** | P-g2 49/55 (89%), pooled capture 0.738 → **G2b1-R1 PASS** |

The A28 FAIL on fixed-percentile transfer stands in the record as a verdict on
fixed-percentile transfer.

## Cross-dataset probe (secondary)

Each assessor's pooled raw cut from one dataset applied to its cells in the
other.

| assessor | cut from | applied to | within | across | Δ |
|---|---|---|---|---|---|
| Llama-3.3-70B | alfworld | hotpotqa | 0.707 | 0.726 | +0.019 |
| Llama-3.3-70B | hotpotqa | alfworld | 0.759 | 0.695 | −0.065 |
| Qwen3.6-35B-A3B | alfworld | hotpotqa | 0.738 | 0.748 | +0.010 |
| Qwen3.6-35B-A3B | hotpotqa | alfworld | 0.769 | 0.734 | −0.035 |
| Mistral-7B-v0.3 | alfworld | hotpotqa | 0.589 | 0.542 | −0.047 |
| Mistral-7B-v0.3 | hotpotqa | alfworld | 0.657 | 0.554 | −0.103 |
| Phi-4-mini | alfworld | hotpotqa | 0.503 | 0.530 | +0.027 |
| Phi-4-mini | hotpotqa | alfworld | 0.568 | 0.498 | −0.070 |
| gemma-3-4b-it | alfworld | hotpotqa | 0.553 | 0.575 | +0.023 |
| gemma-3-4b-it | hotpotqa | alfworld | 0.641 | 0.553 | −0.087 |

Direction is asymmetric: hotpotqa → alfworld is negative for all 5 assessors
(−0.035 to −0.103); alfworld → hotpotqa is positive for 4 of 5 (+0.010 to
+0.027) and negative for Mistral (−0.047).

## Provenance

Labels L1 (3-judge ensemble). No inference run. Analysis:
`analysis/gate2b1_indexed_cut.py`. Cell counting per A28: fitting pool ≥ 3
targets, saturated = S-fitted − V ≤ 0.01. CIs are percentile bootstrap over
cells, 2000 draws.
