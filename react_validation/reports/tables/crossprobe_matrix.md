# Cross-probe matrix — step-level AUROC (soft, 3-judge labels)

Positive class = judge-incorrect. **Labels are LLM-derived**: these are
not headline numbers until recomputed against environment-anchored
targets (gate 1). Diagonal = the arm's own probes (self-assessment).

## alfworld — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.796 *(self)* | 0.738 | 0.699 | 0.759 | 0.812 | 0.772 |
| **Mistral-7B-Instruct-v0.3** | 0.696 | 0.623 *(self)* | 0.614 | 0.572 | 0.561 | 0.653 |
| **Phi-4-mini-instruct** | 0.617 | 0.553 | 0.534 *(self)* | 0.509 | 0.532 | 0.608 |
| **Qwen3.6-35B-A3B** | 0.844 | 0.735 | 0.690 | 0.690 *(self)* | 0.830 | 0.774 |
| **deepseek-v4-flash** | — | — | — | — | 0.760 *(self)* | — |
| **gemma-3-4b-it** | 0.391 | 0.471 | 0.474 | 0.411 | 0.359 | 0.460 *(self)* |

## alfworld — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.883 *(self)* | 0.868 | 0.823 | 0.823 | 0.859 | 0.891 |
| **Mistral-7B-Instruct-v0.3** | 0.723 | 0.608 *(self)* | 0.599 | 0.627 | 0.632 | 0.706 |
| **Phi-4-mini-instruct** | 0.584 | 0.504 | 0.483 *(self)* | 0.573 | 0.545 | 0.615 |
| **Qwen3.6-35B-A3B** | 0.893 | 0.856 | 0.815 | 0.702 *(self)* | 0.849 | 0.909 |
| **deepseek-v4-flash** | — | — | — | — | 0.709 *(self)* | — |
| **gemma-3-4b-it** | 0.555 | 0.541 | 0.524 | 0.632 | 0.543 | 0.642 *(self)* |

## alfworld — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.872 *(self)* | 0.836 | 0.783 | 0.815 | 0.863 | 0.847 |
| **Mistral-7B-Instruct-v0.3** | 0.718 | 0.611 *(self)* | 0.594 | 0.622 | 0.617 | 0.666 |
| **Phi-4-mini-instruct** | 0.601 | 0.522 | 0.501 *(self)* | 0.540 | 0.538 | 0.611 |
| **Qwen3.6-35B-A3B** | 0.883 | 0.821 | 0.765 | 0.708 *(self)* | 0.854 | 0.857 |
| **deepseek-v4-flash** | — | — | — | — | 0.743 *(self)* | — |
| **gemma-3-4b-it** | 0.524 | 0.520 | 0.507 | 0.585 | 0.495 | 0.559 *(self)* |

## alfworld — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.839 *(self)* | 0.831 | 0.797 | 0.757 | 0.823 | 0.865 |
| **Mistral-7B-Instruct-v0.3** | 0.671 | 0.616 *(self)* | 0.583 | 0.574 | 0.573 | 0.700 |
| **Phi-4-mini-instruct** | 0.548 | 0.478 | 0.475 *(self)* | 0.448 | 0.483 | 0.524 |
| **Qwen3.6-35B-A3B** | 0.877 | 0.848 | 0.805 | 0.697 *(self)* | 0.853 | 0.887 |
| **deepseek-v4-flash** | — | — | — | — | 0.720 *(self)* | — |
| **gemma-3-4b-it** | 0.498 | 0.421 | 0.431 | 0.571 | 0.522 | 0.477 *(self)* |

## hotpotqa — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.714 *(self)* | 0.719 | 0.727 | 0.764 | 0.828 |
| **Mistral-7B-Instruct-v0.3** | 0.531 | 0.528 *(self)* | 0.531 | 0.547 | 0.570 |
| **Phi-4-mini-instruct** | 0.626 | 0.502 | 0.525 *(self)* | 0.607 | 0.594 |
| **Qwen3.6-35B-A3B** | 0.748 | 0.737 | 0.733 | 0.810 *(self)* | 0.836 |
| **gemma-3-4b-it** | 0.551 | 0.564 | 0.567 | 0.522 | 0.603 *(self)* |

## hotpotqa — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.820 *(self)* | 0.881 | 0.928 | 0.814 | 0.931 |
| **Mistral-7B-Instruct-v0.3** | 0.714 | 0.723 *(self)* | 0.741 | 0.769 | 0.749 |
| **Phi-4-mini-instruct** | 0.719 | 0.586 | 0.616 *(self)* | 0.651 | 0.644 |
| **Qwen3.6-35B-A3B** | 0.829 | 0.850 | 0.922 | 0.836 *(self)* | 0.927 |
| **gemma-3-4b-it** | 0.691 | 0.696 | 0.717 | 0.663 | 0.714 *(self)* |

## hotpotqa — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.790 *(self)* | 0.839 | 0.889 | 0.792 | 0.910 |
| **Mistral-7B-Instruct-v0.3** | 0.652 | 0.602 *(self)* | 0.620 | 0.658 | 0.651 |
| **Phi-4-mini-instruct** | 0.693 | 0.541 | 0.576 *(self)* | 0.625 | 0.624 |
| **Qwen3.6-35B-A3B** | 0.810 | 0.822 | 0.867 | 0.838 *(self)* | 0.906 |
| **gemma-3-4b-it** | 0.603 | 0.590 | 0.600 | 0.530 | 0.616 *(self)* |

## hotpotqa — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.820 *(self)* | 0.858 | 0.904 | 0.816 | 0.910 |
| **Mistral-7B-Instruct-v0.3** | 0.668 | 0.668 *(self)* | 0.676 | 0.736 | 0.704 |
| **Phi-4-mini-instruct** | 0.677 | 0.530 | 0.550 *(self)* | 0.592 | 0.586 |
| **Qwen3.6-35B-A3B** | 0.822 | 0.836 | 0.904 | 0.842 *(self)* | 0.916 |
| **gemma-3-4b-it** | 0.646 | 0.643 | 0.705 | 0.676 | 0.725 *(self)* |

## Winning scope per (assessor, target) — the invariance view

| dataset | assessor | winner per target |
|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:AGG-mean, gemma:SPLIT-action |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama:SPLIT-action, Mistral:SPLIT-thought, Phi:SPLIT-thought, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | Phi-4-mini-instruct | Llama:SPLIT-thought, Mistral:SPLIT-thought, Phi:SPLIT-thought, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | Qwen3.6-35B-A3B | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-mean, deepseek:AGG-mean, gemma:SPLIT-action |
| alfworld | deepseek-v4-flash | deepseek:SPLIT-thought |
| alfworld | gemma-3-4b-it | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Llama-3.3-70B-Instruct | Llama:AGG-true, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-true, gemma:SPLIT-action |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Phi-4-mini-instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Qwen3.6-35B-A3B | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-true, gemma:SPLIT-action |
| hotpotqa | gemma-3-4b-it | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-true, gemma:AGG-true |

## Invariance: cost of a single fixed scope vs the per-target best

For each assessor the fixed scope is the one with the best MEAN AUROC
across its targets. delta = (per-target best) - (fixed), so delta >= 0 and
SMALL means fixing the recipe is cheap. CI is a 95% episode-clustered
bootstrap on the delta itself - an argmax alone manufactures 'the recipe
flipped' wherever AUROC sits near chance.

| dataset | assessor | fixed scope | target | delta | 95% CI |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | deepseek-v4-flash | 0.005 | [0.000, 0.012] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.015 | [0.004, 0.032] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Phi-4-mini-instruct | 0.016 | [0.000, 0.034] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.008] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Qwen3.6-35B-A3B | 0.064 | [0.041, 0.085] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | deepseek-v4-flash | 0.013 | [0.000, 0.042] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | gemma-3-4b-it | 0.008 | [0.000, 0.031] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.007 | [0.000, 0.022] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | deepseek-v4-flash | 0.005 | [0.000, 0.021] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | deepseek-v4-flash | SPLIT-thought | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.018] |
| alfworld | gemma-3-4b-it | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.001 | [0.000, 0.006] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.003 | [0.000, 0.012] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.007 | [0.000, 0.014] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.006] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Qwen3.6-35B-A3B | 0.013 | [0.000, 0.040] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | gemma-3-4b-it | 0.011 | [0.000, 0.027] |
