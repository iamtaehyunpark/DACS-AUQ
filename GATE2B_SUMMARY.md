# GATE-2b (A28) — Cut Transfer: Results

**2026-08-06 · scope AGG-true · label pass L1 (3-judge ensemble, PREVIEW) · no conclusion
freezes on L1 · spec: `docs/GATE2B_SPEC_A28.md`, pre-registered at commit `c443bca`**

Per-cell table: `tables_gate2b/gate2b_cells_AGG-true.csv`.
95% CIs are percentile bootstrap over cells, 2000 draws.

---

## Arms

60 cells computed. 55 countable (5 excluded: fitting pool < 3 targets).

| excluded cell | reason |
|---|---|
| alfworld / Qwen3.5-4B / Qwen3.5-4B | self-only, no cross cells → pool = 0 |
| alfworld / Qwen3.5-9B / Qwen3.5-9B | self-only → pool = 0 |
| alfworld / deepseek-v4-flash / deepseek-v4-flash | self-only → pool = 0 |
| hotpotqa / Qwen3.5-4B / Qwen3.5-4B | self-only → pool = 0 |
| hotpotqa / Qwen3.5-9B / Qwen3.5-9B | self-only → pool = 0 |

## ALL JUDGES (55 countable, 9 saturated)

| arm | mean | sd across cells | 95% CI |
|---|---|---|---|
| V | 0.590 | 0.121 | [0.558, 0.622] |
| S-LOTO-raw | 0.639 | 0.102 | [0.612, 0.666] |
| S-LOTO-quantile | 0.644 | 0.103 | [0.617, 0.671] |
| S-fitted | 0.657 | 0.110 | [0.628, 0.685] |

- **P-raw**: S-LOTO-raw < V in **12/55 cells (22%)**
- **P-quantile**: S-LOTO-quantile ≥ V in **44/55 cells (80%)**, 95% CI **[69%, 89%]**
- **Capture ratio**: **0.775** over 46 unsaturated cells, 95% CI **[0.636, 0.904]**
- Rule stability: P-quantile CI **straddles** the 80% threshold; capture CI **entirely above** 0.50

**Verdict: G2b-R1 PASS**

## CAPABLE STRATUM — Llama-3.3-70B, Qwen3.6-35B (22 countable, 6 saturated)

| arm | mean | sd across cells | 95% CI |
|---|---|---|---|
| V | 0.727 | 0.063 | [0.701, 0.755] |
| S-LOTO-raw | 0.732 | 0.076 | [0.699, 0.764] |
| S-LOTO-quantile | 0.752 | 0.045 | [0.733, 0.770] |
| S-fitted | 0.775 | 0.042 | [0.757, 0.792] |

- **P-raw**: S-LOTO-raw < V in **10/22 cells (45%)**
- **P-quantile**: S-LOTO-quantile ≥ V in **15/22 cells (68%)**, 95% CI **[50%, 86%]**
- **Capture ratio**: **0.552** over 16 unsaturated cells, 95% CI **[0.364, 0.718]**
- Rule stability: P-quantile CI **straddles** 80%; capture CI **straddles** 0.50

**Verdict: G2b-R3 FAIL**

## Per-assessor arm means (countable cells only)

| assessor | n | V | S-LOTO-raw | S-LOTO-quantile | S-fitted |
|---|---|---|---|---|---|
| Qwen3.6-35B-A3B | 11 | 0.730 | 0.743 | 0.754 | 0.782 |
| Llama-3.3-70B-Instruct | 11 | 0.724 | 0.721 | 0.749 | 0.768 |
| Mistral-7B-Instruct-v0.3 | 11 | 0.504 | 0.619 | 0.608 | 0.614 |
| gemma-3-4b-it | 11 | 0.483 | 0.590 | 0.581 | 0.589 |
| Phi-4-mini-instruct | 11 | 0.508 | 0.523 | 0.527 | 0.531 |

---

## Pre-registered predictions: outcome

**P-raw — NOT BORNE OUT.** The spec predicted S-LOTO-raw would fall short of S-fitted by a
wide margin and fall below V in a substantial minority of cells. Across all judges,
S-LOTO-raw is below V in 22% of cells, and its mean (0.639) is within 0.018 of S-fitted
(0.657). On the capable stratum S-LOTO-raw falls below V in 45% of cells and its mean
(0.732) is 0.043 below S-fitted (0.775).

The spec states: *"If S-LOTO-raw ≈ S-fitted instead, §7.1's practical-bite framing must be
softened — write that down too."* Recorded here.

**P-quantile — holds on ALL JUDGES (80%, at the threshold), fails on the CAPABLE STRATUM
(68%).**

## Cross-arm ordering

- ALL JUDGES: V (0.590) < S-LOTO-raw (0.639) < S-LOTO-quantile (0.644) < S-fitted (0.657)
- CAPABLE: V (0.727) < S-LOTO-raw (0.732) < S-LOTO-quantile (0.752) < S-fitted (0.775)

Cross-cell sd (transfer stability), capable stratum: S-fitted 0.042 < S-LOTO-quantile
0.045 < V 0.063 < S-LOTO-raw 0.076.

## Status of these numbers

- Label pass **L1** (3-judge ensemble). Per the spec, this is a preview; the pass of
  record requires rerun under **L2** (gate-1 environment-anchored labels).
- Scope AGG-true only. Other scopes not computed.
- S-LOTO-quantile uses the held-out target's full frozen score distribution — the batch
  form of the online rule, as labelled in the spec §Arms.
- Both P-quantile rates have bootstrap CIs spanning the 80% decision threshold, so the
  R1/R3 assignment is not separated from its alternative at 95% confidence in either
  stratum.
