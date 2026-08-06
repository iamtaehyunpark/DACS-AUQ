# Report — Can the Label-Free Cut Run Online?
**2026-08-06 · Basis: gate-2b.1 cells (tables_gate2b1/gate2b1_cells_AGG-true_full.csv), flatness curves (figures_gate2b1/), gate-2 b1 tables · Labels L1 (3-judge ensemble, PREVIEW; L2 rerun owed) · Scope AGG-true**

## 1. Question and answer

The g-rule — estimate a new agent's error rate p̂ from the judge's own mean score via the
pool-fitted map g, cut at the top-p̂ quantile of the agent's own scores, zero labels — was
validated in **batch** form (A28.1): statistics computed over the target's full frozen
corpus (~140 episodes). Question: does the rule *require* the completed corpus, or can it
run online?

**Answer: online by construction; only convergence speed is unmeasured.** The rule
consumes three objects: g (fitted offline on reference targets, exists before step 1),
the running mean of scores seen so far, and the running quantile of scores seen so far.
All are streaming statistics over strictly past information. The step being gated is
scored before execution and compared against a cut computed from steps 1..t−1. No labels,
no completed episodes, no future information. The batch numbers below are what the online
statistics converge to; the open quantity is how fast.

## 2. Grounding A — batch validity of the rule (what the gates established)

Arm means, balanced accuracy, capable stratum (Llama-3.3-70B, Qwen3.6-35B as judges;
22 countable cells; 95% bootstrap CI over cells):

| arm | mean | 95% CI | labels from target |
|---|---|---|---|
| V (argmax verdict = fixed 0.5 cut) | 0.727 | [0.701, 0.755] | none |
| S-LOTO-raw (transferred raw cut) | 0.732 | [0.699, 0.764] | none |
| S-LOTO-quantile (transferred fixed percentile) | 0.752 | [0.733, 0.770] | none |
| **S-g-quantile (the online-capable rule)** | **0.753** | **[0.725, 0.780]** | **none** |
| S-oracle-pct (true-error-rate percentile) | 0.757 | [0.734, 0.780] | base rate only |
| S-fitted (per-target labeled cut, episode-split OOS) | 0.775 | [0.757, 0.792] | ~half the corpus |

Verdicts: fixed-percentile transfer **FAILED** its gate (A28, G2b-R3, capable stratum);
the indexed rule **PASSED** (A28.1, G2b1-R1: g ≥ V in 18/22 = 82% vs 80% bar; pooled
capture 0.555 vs 0.5 bar). Both deciding CIs straddle their thresholds — the pass is
real but marginal on L1; L2 is decisive.

## 3. Grounding B — the tier contrast the online rule must sustain

Qwen-35B (mid judge, score rules) vs Llama-70B (large judge, verdict), all 11 shared
targets, per cell:

| cell | L70B verdict | Q35 g-rule (label-free) | Q35 fitted (~labels) |
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

Label-free: **8/11** overall, **8/9 on cross-judging cells** (the design's regime; the
two losses are Qwen self-cells, §5, and the third is −0.001). With ~200 labels: 11/11.
Related single-cell anecdote: on deepseek's own trajectories, the external mid-size
g-rule (0.800) beats deepseek's self-reading at its own cut (~0.72–0.76) — one cell,
ALFWorld only, self-assessment not external judging; existence proof, not pattern.

## 4. Grounding C — the error budget the online estimate must meet

Flatness-curve anatomy per capable cell (optimal cut percentile; width of the region
within 0.01 of the optimum):

| cell (judge → target) | opt pct | opt bal_acc | flat region | width |
|---|---|---|---|---|
| alf L70B→L70B | 49 | 0.769 | 40–56 | 17 |
| alf L70B→Mistral | 39 | 0.766 | 24–43 | 20 |
| alf L70B→Phi | 30 | 0.736 | 21–40 | 20 |
| alf L70B→Qwen35 | 57 | 0.699 | 52–62 | 11 |
| alf L70B→deepseek | 58 | 0.748 | 49–64 | 14 |
| alf L70B→gemma | 18 | 0.797 | 14–32 | 19 |
| alf Q35→L70B | 53 | 0.818 | 46–56 | 11 |
| alf Q35→Mistral | 32 | 0.782 | 25–40 | 16 |
| alf Q35→Phi | 24 | 0.751 | 19–35 | 17 |
| alf Q35→Qwen35 | 45 | 0.654 | 32–52 | 20 |
| alf Q35→deepseek | 60 | 0.805 | 55–65 | 10 |
| alf Q35→gemma | 22 | 0.814 | 19–34 | 16 |
| hot L70B→L70B | 55 | 0.769 | 51–63 | 13 |
| hot L70B→Mistral | 41 | 0.774 | 35–56 | 22 |
| hot L70B→Phi | 51 | 0.834 | 40–54 | 15 |
| hot L70B→Qwen35 | 67 | 0.772 | 56–74 | 19 |
| hot L70B→gemma | 48 | 0.835 | 43–58 | 16 |
| hot Q35→L70B | 56 | 0.763 | 47–61 | 15 |
| hot Q35→Mistral | 38 | 0.773 | 33–48 | 16 |
| hot Q35→Phi | 42 | 0.838 | 36–46 | 11 |
| hot Q35→Qwen35 | 59 | 0.797 | 56–71 | 15 |
| hot Q35→gemma | 48 | 0.846 | 42–56 | 15 |

Median flat-region width: **16 percentile points** (min 10). Reading: a cut placed
within ~±8 points of the optimum loses ≤0.01 balanced accuracy. The competence estimate
therefore needs only |p̂ − p| ≲ 0.05–0.08 — ordinary, not heroic, accuracy.

## 5. Grounding D — where the batch rule missed, and what it implies online

The four capable cells where g < V, with the estimation diagnosis:

| cell | base p | p̂ | Δp | V | g | oracle-pct |
|---|---|---|---|---|---|---|
| alf Q35→Qwen35 *(self)* | 0.382 | 0.242 | −0.140 | 0.628 | 0.602 | 0.630 |
| hot Q35→Qwen35 *(self)* | 0.153 | 0.049 | −0.105 | 0.756 | 0.597 | 0.699 |
| hot Q35→L70B | 0.209 | 0.301 | +0.092 | 0.759 | 0.734 | 0.699 |
| hot L70B→gemma | 0.472 | 0.467 | −0.005 | 0.833 | 0.830 | 0.830 |

Two mechanisms, both relevant to online deployment:
1. **Self-leniency** (rows 1–2): the judge's mean score on its *own* steps sits below the
   cross-fitted relation → p̂ underestimated by 0.10–0.14, outside the §4 budget. Cross
   cells average |Δp| = 0.052 — inside budget. The online rule inherits the same scope
   condition the paper already imposes: **external judge only**.
2. **Indexing-identity error** (rows 3–4): the oracle percentile *also* loses to V, so
   perfect p̂ would not fix these — the assumption "optimal flag rate = error rate" is an
   approximation with structured residuals (optimal percentiles in §4 deviate from
   100·(1−base) by up to ~26 points). Pre-registered L2 secondary: fit the percentile
   directly (h: mean score → optimal percentile) instead of routing through the identity.

## 6. Convergence: the only open quantity, and its expected size

The online statistics are a running mean and running quantile. Standard-error scaling:
with per-step score sd ≈ 0.3–0.4 (bounded [0,1] scores), the running mean reaches
±0.05 accuracy — the §4 budget — within roughly n ≈ 40–70 steps; quantile estimates at
mid-percentiles behave comparably. Expected warm-up: **tens of steps to ~one–two
episodes** (ALFWorld episodes run ~20–50 steps), amortized once per deployment, not per
episode. During warm-up the gate falls back on the pool-transferred fixed-percentile
prior — the arm measured at 0.752 mean (capable) with known failure mode (base-rate
mismatch), which is precisely what convergence then repairs. Contrast for positioning:
trajectory-level methods emit nothing until an episode completes; this rule decides
every step from the first, at reduced accuracy that improves online.

These estimates are back-of-envelope. The measurement is free: **prequential replay** on
banked scores — stream each target's episodes, decide each step from past-only
statistics, plot cumulative balanced accuracy and p̂_t → p, ~10 episode orderings,
mean ± sd, warm-up-inclusive headline plus post-warm-up figure. Slots as §8.ix after the
L2 rerun. Pre-registered prediction: prequential performance reaches within 0.01 of the
batch g-rule by ≤100 steps on cross cells.

## 7. Caveats of record

1. All numbers are L1 (judge-ensemble labels); gate-1 environment-anchored rerun is the
   pass of record for every table above.
2. Batch-validated, sequential-unmeasured: §6's warm-up numbers are estimates until the
   replay runs.
3. Single scope (AGG-true), single evidence condition; the retrospective-stream variant
   (C5-grade re-scoring, v4.1 §6b) is untested and would only tighten the calibration
   side.
4. Frontier *external* judge (b3) remains the untested rung of the tier ladder; the
   deepseek cell in §3 is self-assessment, not an external frontier judge.
