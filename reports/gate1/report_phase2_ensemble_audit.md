# Gate-1 Phase 2 — ensemble circularity audit

Every step below is **Tier-A incorrect**: the environment rejected the action, returned nothing, repeated a state, or the action was not a legal call at all. Ground truth on these steps is certain and needs no judgment. The question is how often the 3-judge ensemble — the label all current results are scored against — called them **correct**.

Two readings are given. *Discrete* uses the ensemble's own majority label (`ensemble_incorrect == 0`). *Soft* is the mean fraction of the 3 judges voting correct, which is the weighting `crossprobe_matrix_auroc.py` actually uses.


## All arms

| dataset | model | Tier-A-incorrect steps | judged | ensemble said CORRECT (discrete) | mean judge frac. correct (soft) |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 1714 | 1714 | 80 (4.7%) | 0.082 |
| alfworld | Mistral-7B-Instruct-v0.3 | 4616 | 4616 | 97 (2.1%) | 0.053 |
| alfworld | Phi-4-mini-instruct | 4109 | 4102 | 40 (1.0%) | 0.043 |
| alfworld | Qwen3.5-27B | 967 | 0 | 0 (—) | — |
| alfworld | Qwen3.5-4B | 2464 | 1975 | 92 (4.7%) | 0.107 |
| alfworld | Qwen3.5-9B | 1840 | 1515 | 65 (4.3%) | 0.099 |
| alfworld | Qwen3.6-35B-A3B | 1157 | 1015 | 110 (10.8%) | 0.178 |
| alfworld | deepseek-v4-flash | 779 | 770 | 42 (5.5%) | 0.105 |
| alfworld | gemma-3-4b-it | 5538 | 5538 | 32 (0.6%) | 0.016 |
| hotpotqa | Llama-3.3-70B-Instruct | 841 | 841 | 318 (37.8%) | 0.575 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 2277 | 2277 | 492 (21.6%) | 0.313 |
| hotpotqa | Phi-4-mini-instruct | 1620 | 1620 | 307 (19.0%) | 0.256 |
| hotpotqa | Qwen3.5-4B | 1174 | 1066 | 495 (46.4%) | 0.596 |
| hotpotqa | Qwen3.5-9B | 1057 | 811 | 289 (35.6%) | 0.614 |
| hotpotqa | Qwen3.6-35B-A3B | 794 | 752 | 385 (51.2%) | 0.670 |
| hotpotqa | gemma-3-4b-it | 1386 | 1386 | 330 (23.8%) | 0.286 |
| **ALL** | | **32333** | **29998** | **3174 (10.6%)** | **0.164** |

## Matrix arms only (the 56 cells)

| dataset | model | Tier-A-incorrect steps | judged | ensemble said CORRECT (discrete) | mean judge frac. correct (soft) |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 1714 | 1714 | 80 (4.7%) | 0.082 |
| alfworld | Mistral-7B-Instruct-v0.3 | 4616 | 4616 | 97 (2.1%) | 0.053 |
| alfworld | Phi-4-mini-instruct | 4109 | 4102 | 40 (1.0%) | 0.043 |
| alfworld | Qwen3.6-35B-A3B | 1157 | 1015 | 110 (10.8%) | 0.178 |
| alfworld | deepseek-v4-flash | 779 | 770 | 42 (5.5%) | 0.105 |
| alfworld | gemma-3-4b-it | 5538 | 5538 | 32 (0.6%) | 0.016 |
| hotpotqa | Llama-3.3-70B-Instruct | 841 | 841 | 318 (37.8%) | 0.575 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 2277 | 2277 | 492 (21.6%) | 0.313 |
| hotpotqa | Phi-4-mini-instruct | 1620 | 1620 | 307 (19.0%) | 0.256 |
| hotpotqa | Qwen3.6-35B-A3B | 794 | 752 | 385 (51.2%) | 0.670 |
| hotpotqa | gemma-3-4b-it | 1386 | 1386 | 330 (23.8%) | 0.286 |
| **ALL** | | **24831** | **24631** | **2233 (9.1%)** | **0.139** |

## By firing sub-rule (matrix arms)

| rule | steps | judged | ensemble said CORRECT | mean judge frac. correct |
|---|---|---|---|---|
| `A1_inadmissible` | 9768 | 9610 | 126 (1.3%) | 0.037 |
| `A1_malformed_toolcall` | 89 | 47 | 0 (0.0%) | 0.028 |
| `A2_nothing_happens` | 6062 | 6000 | 49 (0.8%) | 0.020 |
| `A3_exact_repeat` | 14788 | 14682 | 276 (1.9%) | 0.040 |
| `A3_repeat_query` | 2734 | 2724 | 9 (0.3%) | 0.012 |
| `A4_zero_result` | 5785 | 5785 | 1823 (31.5%) | 0.429 |

## Unanimity on settled steps (matrix arms)

How the 3 judges split on steps the environment had already decided.

| judges voting CORRECT | steps | share |
|---|---|---|
| 0 of 3 | 19944 | 81.0% |
| 1 of 3 | 1437 | 5.8% |
| 2 of 3 | 1017 | 4.1% |
| 3 of 3 | 2233 | 9.1% |

## R4 — the number

**10.6% of judged Tier-A-incorrect steps were labelled CORRECT by the 3-judge ensemble** (3174 of 29998, all arms). Soft weighting: mean fraction of judges voting correct on those steps = **0.164**.

This is a floor on ensemble label error, not an estimate of it: it is measured only where the environment supplies certain ground truth, which is the subset of steps where errors are most blatant.

**A4 sensitivity.** A4 is the only sub-rule where the environment's verdict and a step-quality verdict can legitimately diverge: a well-formed query that happened to retrieve nothing is a failed step by the pre-registered rule, but a judge may reasonably call the *action* sound. The rule is not reinterpreted here — both numbers are simply reported. Matrix arms, judged Tier-A-incorrect steps: **9.1% said correct** (2233 of 24631) as pre-registered; **2.0%** (410 of 20521) after dropping the 4110 steps whose only firing rule is A4.

