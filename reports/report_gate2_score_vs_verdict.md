# GATE-2 Report — The Score Beats the Verdict, a Tier Down
## Mid-size P(True) + operating-point machinery vs the large model's binary decision

**2026-08-06 · Basis: gate-2 b1 (verdict_vs_value, ptrue_binary_consensus), GATE-2b (A28), GATE-2b.1 (A28.1) · Labels L1 (3-judge ensemble, PREVIEW; L2 rerun owed) · Scope AGG-true**

## 0. The challenge under test

Advisor position: for online step-wise decision-making a binary LLM-judge verdict
("execute / don't") suffices — same prefill, same one-token cost — so the paper stands
only if a mid-size model's P(True) discriminates at least as well as a larger judge's
binary decision. This report is the answer on banked data. Identity making it testable
for free: the greedy binary verdict IS the P(True) value cut at 0.5 — so verdict-vs-value
is one channel compared at two operating points, and the machinery's job is to place the
operating point better than the model's own semantic boundary does.

## 1. Channel result: reading the probability beats reading the answer

Value (cut fitted out-of-sample by episode) vs verdict, per judge, balanced accuracy,
60 cells:

| judge | n | mean gain (value − verdict) | cells value < verdict |
|---|---|---|---|
| Llama-3.3-70B | 11 | +0.044 | 2 |
| Qwen3.6-35B | 11 | +0.048 | 1 |
| Mistral-7B | 11 | +0.110 | 0 |
| gemma-3-4b | 11 | +0.107 | 0 |
| Phi-4-mini | 11 | +0.024 | 2 |
| deepseek (self, 1 cell) + Qwen3.5-4B/9B (2 each) | 5 | +0.011…+0.098 | 0 |
| **ALL** | **60** | **+0.065** | **5** |

Value ≥ verdict in **55/60 cells (92%)**; in-sample optimism of the fitted cut is +0.009
(the win is not overfitting). The verdict side needs no logprob access; only the value
side does — the gain is the price of one logit read.

## 2. The verdict is adaptive — and still mis-placed (the advisor's mechanism, measured)

From the consensus table (verdict behavior per judge, AGG-true):

| judge | corr(flag rate, target error rate) | mean(flag − error rate) | verdict mean bal_acc | cells ≤ majority-class |
|---|---|---|---|---|
| Llama-3.3-70B | +0.978 | −0.013 | 0.723 | 0/11 |
| Qwen3.6-35B | +0.956 | +0.121 | 0.734 | 2/11 |
| Mistral-7B | +0.834 | −0.489 | 0.503 | 11/11 |
| Phi-4-mini | +0.706 | −0.321 | 0.507 | 9/11 |
| gemma-3-4b | +0.690 | −0.332 | 0.483 | 10/11 |

Capable judges' implicit threshold tracks target difficulty almost perfectly (r ≈ 0.97) —
the advisor's hypothesis is confirmed — yet placement is biased per judge (Llama
under-flags in low-error regimes: worst cell flags 7% at a 15% error rate, bal_acc 0.614;
Qwen over-flags everywhere, +0.12). Adaptation is not optimization; a bit cannot be
re-thresholded, a score can. Weak judges' verdicts collapse to majority-class or below in
9–11/11 cells while their *scores* remain recoverable (+0.02…+0.11 via a cut) — the
binary channel is more capability-gated than the score channel.

## 3. Tier result: the mid judge's score vs the large judge's verdict, per cell

Qwen3.6-35B (score rules) vs Llama-3.3-70B (verdict), all 11 shared targets:

| cell | L70B verdict | Q35 g-rule (zero target labels) | Q35 fitted (~200 labels) |
|---|---|---|---|
| alfworld / Llama-70B | 0.762 | 0.790 | 0.823 |
| alfworld / Mistral-7B | 0.727 | 0.776 | 0.780 |
| alfworld / Phi-4-mini | 0.665 | 0.739 | 0.748 |
| alfworld / Qwen-35B *(self)* | 0.649 | 0.602 | 0.664 |
| alfworld / deepseek-v4-flash | 0.715 | **0.800** | 0.772 |
| alfworld / gemma-3-4b | 0.707 | 0.811 | 0.811 |
| hotpotqa / Llama-70B | 0.691 | 0.734 | 0.761 |
| hotpotqa / Mistral-7B | 0.769 | 0.771 | 0.771 |
| hotpotqa / Phi-4-mini | 0.826 | 0.825 | 0.836 |
| hotpotqa / Qwen-35B *(self)* | 0.619 | 0.597 | 0.790 |
| hotpotqa / gemma-3-4b | 0.833 | 0.834 | 0.843 |

- **With ~200 target labels: 11/11** — the mid score sweeps the large verdict.
- **Fully label-free (g-rule): 8/11 overall; 8/9 in cross-judging cells**, the design's
  regime — the two real losses are Qwen judging *itself* (self-leniency, §5 below), the
  third is −0.001.
- Anecdote (one cell, self-assessment, ALFWorld only): the mid-size external g-rule reads
  deepseek's trajectories at 0.800 vs deepseek's own self-reading at its own cut
  (~0.72–0.76) — the API-class model grading its own homework loses to a hosted 35B.

## 4. How the label-free cut earned its place (the two transfer gates)

| gate | rule tested | capable stratum (decisive) | all judges |
|---|---|---|---|
| A28 | fixed-percentile transfer | 15/22 (68%) < 80% → **FAIL** | 44/55 (80%), capture 0.775 → PASS |
| A28.1 | error-rate-indexed transfer (g-rule) | 18/22 (82%), pooled capture 0.555 → **PASS** | 49/55 (89%), capture 0.738 → PASS |

The FAIL stands in the record as a verdict on fixed percentiles; the indexed rule fixed
its named failure case (Qwen→deepseek: fixed-percentile 0.711 vs V 0.797 → indexed
0.800). Both A28.1 deciders sit at their thresholds with CIs straddling (82% CI [64, 95];
capture CI [0.08, 0.84]) — pass, marginal, L2 decisive.

## 5. Boundary of the claim, measured

Capable cells where the label-free rule loses to the verdict, with the diagnosis:

| cell | true p | p̂ | Δp | V | g |
|---|---|---|---|---|---|
| alf Qwen→Qwen *(self)* | 0.382 | 0.242 | −0.140 | 0.628 | 0.602 |
| hot Qwen→Qwen *(self)* | 0.153 | 0.049 | −0.105 | 0.756 | 0.597 |
| hot Qwen→Llama | 0.209 | 0.301 | +0.092 | 0.759 | 0.734 |
| hot Llama→gemma | 0.472 | 0.467 | −0.005 | 0.833 | 0.830 |

Self-cells break the characterization (the judge scores its own steps leniently; p̂
underestimated by 0.10–0.14) — a measured argument that the **external**-judge design is
necessary, not stylistic. Cross-cell p̂ error averages 0.052, inside the ±0.08 tolerance
the flatness curves establish. On two cells the oracle percentile also loses — the
flag-rate=error-rate identity is an approximation; a direct percentile map is
pre-registered as an L2 secondary.

## 6. Decision-rule status (A27)

- **G2-R1 (channel):** value ≥ verdict in 92% of cells (bar: 80%) → provisional PASS.
- **G2-R2 (tier — the advisor's stated feasibility bar):** mid score ≥ large verdict
  11/11 with labels, 8/9 label-free in-regime → provisional PASS.
- **G2-R3 (adverse):** not fired.
- **G2-R4 (frontier split):** UNTESTED — the frontier *external* judge arm (b3:
  ChatGPT/deepseek API, decision-framed verdict + logprob P(True), ~2–3k-step stratified
  subsample) is the one rung of the ladder not yet run; the decision-framed prompt (b2)
  for open judges is also owed.

## 7. Caveats of record

1. All numbers are L1 (judge-ensemble labels); the gate-1 environment-anchored rerun is
   the pass of record for every table here.
2. The verdict tested is the trust-framed argmax; a decision-framed prompt may carry a
   better-placed implicit boundary (b2, unrun).
3. The g-rule is batch-validated; its online form is identical in information
   requirements, with convergence (warm-up ≈ tens of steps, estimated) measured by the
   prequential replay after L2 — see companion report
   `report_online_labelfree_rule.md`.
4. Single scope (AGG-true); self-cells excluded from the deployment claim by design, not
   post-hoc (the rule was always specified for external judging).

**One-line summary for the advisor:** the judge's yes/no is as adaptive as you predicted
— we measured it at r ≈ 0.97 — and it still loses to its own probability read: +0.065
same-judge, and a 35B score beats a 70B verdict in 11/11 cells with ~200 labels, 8/9
label-free; the remaining untested opponent is the frontier external judge, which is one
cheap API pass away.
