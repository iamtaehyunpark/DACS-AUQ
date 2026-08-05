# Can a judge's operating point be characterised once?

**2026-08-05 · pivot corpus, 56 (assessor × target) cells · scope SPLIT-action**

All numbers below are against the 3-judge ensemble label, so they are **provisional until
gate-1 recomputation** against environment-anchored targets. They are reported here to
settle a design question, not as headline results.

---

## The question

Recipe invariance holds: fixing one scope costs ≤0.02 AUROC in 52 of 54 columns
(`crossprobe_matrix.md`). But a deployed gate needs a *decision*, not a ranking. If the
threshold has to be re-fitted for every new agent, the methodology loses its deployment
claim — it would be no cheaper than searching for the best self-assessment metric per
model, which §2 already says fails.

So: is the operating point a property of the judge?

---

## 1. Absolute thresholds do not transfer — not even within one dataset

Per assessor, across its targets (`uncertainty_levels.csv`):

| assessor (ALFWorld) | mu_inc range | mu_cor range | gap range |
|---|---|---|---|
| Llama-3.3-70B | 0.177 – 0.920 | 0.011 – 0.348 | +0.161 … +0.655 |
| Qwen3.6-35B | 0.489 – 0.938 | 0.281 – 0.644 | +0.208 … +0.439 |
| Mistral-7B | 0.019 – 0.107 | 0.005 – 0.086 | +0.010 … +0.068 |
| Phi-4-mini | 0.123 – 0.434 | 0.084 – 0.394 | **−0.032** … +0.086 |
| gemma-3-4b | 0.033 – 0.263 | 0.023 – 0.337 | **−0.073** … +0.043 |

`mu_inc` and `mu_cor` are the mean U on judge-incorrect and judge-correct steps. They are
base-rate free by construction — pooling by group removes the error-rate confound — and
they still move by 5× and 30×.

Worse, the ranges **overlap across targets**: Llama's mean U on *correct* steps reaches
0.348 on one target while its mean on *incorrect* steps is 0.177 on another. A cut point
that separates correctly on one target actively misclassifies on another, same judge,
same environment.

**A threshold cannot be settled per (estimator, dataset).** Two assessors show *negative*
mean gaps on ALFWorld — Phi-4-mini and gemma-3-4b rate correct steps as more uncertain
than incorrect ones on at least one target.

## 2. Percentile rules are better behaved but not uniform

`lift@10%` = precision in the top decile ÷ base rate. 1.0 = no better than random.

| assessor | ALFWorld mean (range) | HotpotQA mean (range) |
|---|---|---|
| Llama-70B | 1.74 (1.12–2.75) | 2.46 (1.77–3.52) |
| Qwen-35B | 1.72 (1.13–2.80) | 2.40 (1.70–3.40) |
| Mistral-7B | 1.34 (1.04–1.69) | 1.80 (1.38–2.65) |
| Phi-4-mini | 1.12 (0.98–1.36) | 1.43 (1.12–1.98) |
| gemma-3-4b | 1.03 (0.82–1.48) | 1.38 (1.25–1.70) |

Direction is stable — the top slice beats random almost everywhere — and the assessor
ordering is identical in both environments. But the enrichment factor still moves ~2.5×
within one assessor, so a fixed yield cannot be promised.

Note the ceiling this exposes: at a 10% budget the best judges recall only **18–25%** of
incorrect steps. Errors are common here (base rates 0.15–0.89), not rare, so a strong
ranking still surfaces a minority of them in the top decile.

## 3. The optimal cut is determined by the target's error rate

Correlation between target error rate and the optimal cut expressed as a percentile:

| assessor | r |
|---|---|
| Llama-70B | +0.958 |
| Qwen-35B | +0.944 |
| gemma-3-4b | +0.839 |
| Mistral-7B | +0.532 |
| Phi-4-mini | +0.400 |

The cut is not drifting arbitrarily: for capable judges it is almost entirely set by how
error-prone the target is. Flag ~33% when a third of steps are bad, ~89% when nearly all
are — correct behaviour, not instability.

**And the error rate is estimable without labels.** Mean U tracks the target error rate at
r = +0.990 (Llama, ALFWorld), +0.998 (Llama, HotpotQA), +0.960/+0.972 (Qwen). The judge
can estimate an unknown agent's competence before any labels exist for it.

## 4. Correcting an artifact: raw percentile correlations are mostly arithmetic

The median percentile position of the incorrect pool correlates strongly and negatively
with the error rate (Llama −0.983, Qwen −0.942, all cells −0.681). **This is not a
finding.** A perfect ranker shows the same thing: if a fraction *p* of steps are incorrect
and ranking is flawless, the incorrect pool occupies the top *p*, so its median percentile
is `100·(1 − p/2)` — 83.5 at p=0.33, 55.5 at p=0.89. The negative correlation is forced.

The informative quantity is how far the observed position sits between chance (50) and
that perfect-ranking bound.

## 5. Normalised separation IS uniform — for capable judges only

`frac = (observed median percentile − 50) / (perfect-ranking bound − 50)`.
0 = chance, 1 = perfect separation. Base-rate free.

| assessor | mean | range over 11 cells |
|---|---|---|
| **Llama-3.3-70B** | **0.876** | 0.78 – 0.98 |
| **Qwen3.6-35B** | **0.842** | 0.54 – 0.97 |
| Mistral-7B | 0.484 | 0.27 – 0.71 |
| gemma-3-4b | 0.323 | 0.05 – 0.52 |
| Phi-4-mini | 0.259 | **−0.08** – 0.57 |

Llama achieves ~88% of achievable separation across six generators and two environments,
varying only 0.78–0.98. Qwen is close behind. The weak judges are not merely worse, they
are **erratic**: Phi-4-mini spans −0.08 to 0.57, i.e. it inverts on some targets.

Uniformity of the operating point is therefore **capability-gated**. It is a real property
of a capable instrument and absent from a weak one.

---

## What this means for the methodology

**Supported:** the recipe (scope + evidence) transfers; the normalised separation is
uniform for capable judges; a budget-gated policy always beats random inspection; and the
quantity that sets the cut — the target's error rate — is itself estimable from the
judge's own scores without labels.

**Not supported:** "characterise the threshold once and deploy blind." The operating point
is a function of the target's competence, and §4's "local calibration saturates at ~200
labelled steps" should be stated as a per-deployment requirement, not a footnote.

**Why this is still not per-model metric search.** What must be fitted is a single scalar,
not a search over metric × scope; the labels for it are environment-derived and free
(loop flags, cap events, outcomes); and none of it needs access to the agent's internals,
so it works on closed models where self-assessment cannot run at all.

**Honest one-line summary:** *the instrument's ranking and recipe amortise; its operating
point is a function of the target's competence, which the instrument can itself estimate.*

---

## Artifacts

| file | contents |
|---|---|
| `reports/tables/uncertainty_levels.{md,csv}` | mu_inc / mu_cor / gap / level / Youden threshold, 56 cells |
| `reports/tables/percentile_consistency.{md,csv}` | lift / precision / recall at k = 5/10/20/30%, 236 rows |
| `reports/tables/percentile_consistency_ranks.csv` | percentile position of the incorrect pool per cell |
| `reports/tables/crossprobe_matrix.{md,csv,json}` | the 56-cell AUROC matrix and invariance table |
| `figures/pivot/incorrect_pool_percentile_vs_errorrate.png` | mean and median percentile vs error rate, per assessor |

Reproduce:

```bash
python analysis/uncertainty_levels.py --scope SPLIT-action
python analysis/percentile_consistency.py --scope SPLIT-action
```

## Caveats

1. **Judge-anchored labels.** Everything here uses the 3-judge ensemble. Gate-1
   recomputation against environment-anchored targets is outstanding.
2. **One scope.** All of this is SPLIT-action. The other three scopes are not analysed.
3. **Small n per assessor.** 11 cells each; correlations are indicative, and the stable
   thing is the ordering, which is consistent across both environments.
4. **deepseek-v4-flash** appears as a target only — it is API-only and was not run as an
   assessor, so it has a self cell and no row.
