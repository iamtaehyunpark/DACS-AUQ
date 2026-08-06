# Cross-probe matrix — step-level AUROC (soft, 3-judge labels)

Positive class = judge-incorrect. **Labels are LLM-derived**: these are
not headline numbers until recomputed against environment-anchored
targets (gate 1). Diagonal = the arm's own probes (self-assessment).

## alfworld — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.800 *(self)* | 0.739 | 0.699 | — | — | 0.760 | 0.816 | 0.770 |
| **Mistral-7B-Instruct-v0.3** | 0.704 | 0.624 *(self)* | 0.615 | — | — | 0.576 | 0.564 | 0.654 |
| **Phi-4-mini-instruct** | 0.617 | 0.544 | 0.536 *(self)* | — | — | 0.508 | 0.531 | 0.610 |
| **Qwen3.5-4B** | — | — | — | 0.638 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.692 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.840 | 0.732 | 0.688 | — | — | 0.689 *(self)* | 0.826 | 0.772 |
| **deepseek-v4-flash** | — | — | — | — | — | — | 0.761 *(self)* | — |
| **gemma-3-4b-it** | 0.385 | 0.462 | 0.469 | — | — | 0.409 | 0.346 | 0.459 *(self)* |

## alfworld — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.885 *(self)* | 0.868 | 0.822 | — | — | 0.824 | 0.862 | 0.890 |
| **Mistral-7B-Instruct-v0.3** | 0.729 | 0.613 *(self)* | 0.603 | — | — | 0.632 | 0.640 | 0.710 |
| **Phi-4-mini-instruct** | 0.589 | 0.505 | 0.489 *(self)* | — | — | 0.574 | 0.551 | 0.617 |
| **Qwen3.5-4B** | — | — | — | 0.658 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.713 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.893 | 0.855 | 0.814 | — | — | 0.701 *(self)* | 0.849 | 0.908 |
| **deepseek-v4-flash** | — | — | — | — | — | — | 0.713 *(self)* | — |
| **gemma-3-4b-it** | 0.560 | 0.543 | 0.527 | — | — | 0.636 | 0.556 | 0.646 *(self)* |

## alfworld — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.874 *(self)* | 0.836 | 0.782 | — | — | 0.816 | 0.866 | 0.845 |
| **Mistral-7B-Instruct-v0.3** | 0.724 | 0.614 *(self)* | 0.596 | — | — | 0.626 | 0.623 | 0.668 |
| **Phi-4-mini-instruct** | 0.604 | 0.519 | 0.505 *(self)* | — | — | 0.539 | 0.539 | 0.613 |
| **Qwen3.5-4B** | — | — | — | 0.653 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.707 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.881 | 0.819 | 0.763 | — | — | 0.708 *(self)* | 0.852 | 0.856 |
| **deepseek-v4-flash** | — | — | — | — | — | — | 0.745 *(self)* | — |
| **gemma-3-4b-it** | 0.525 | 0.519 | 0.509 | — | — | 0.588 | 0.499 | 0.561 *(self)* |

## alfworld — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.845 *(self)* | 0.830 | 0.798 | — | — | 0.758 | 0.828 | 0.863 |
| **Mistral-7B-Instruct-v0.3** | 0.680 | 0.624 *(self)* | 0.590 | — | — | 0.579 | 0.585 | 0.705 |
| **Phi-4-mini-instruct** | 0.548 | 0.478 | 0.480 *(self)* | — | — | 0.448 | 0.487 | 0.527 |
| **Qwen3.5-4B** | — | — | — | 0.625 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.667 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.875 | 0.847 | 0.803 | — | — | 0.696 *(self)* | 0.852 | 0.886 |
| **deepseek-v4-flash** | — | — | — | — | — | — | 0.728 *(self)* | — |
| **gemma-3-4b-it** | 0.499 | 0.422 | 0.433 | — | — | 0.574 | 0.520 | 0.480 *(self)* |

## hotpotqa — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.682 *(self)* | 0.683 | 0.693 | — | — | 0.717 | 0.796 |
| **Mistral-7B-Instruct-v0.3** | 0.563 | 0.500 *(self)* | 0.530 | — | — | 0.605 | 0.601 |
| **Phi-4-mini-instruct** | 0.608 | 0.452 | 0.505 *(self)* | — | — | 0.632 | 0.602 |
| **Qwen3.5-4B** | — | — | — | 0.706 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.687 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.709 | 0.700 | 0.686 | — | — | 0.752 *(self)* | 0.808 |
| **gemma-3-4b-it** | 0.563 | 0.544 | 0.564 | — | — | 0.600 | 0.623 *(self)* |

## hotpotqa — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.798 *(self)* | 0.856 | 0.905 | — | — | 0.778 | 0.922 |
| **Mistral-7B-Instruct-v0.3** | 0.677 | 0.687 *(self)* | 0.706 | — | — | 0.744 | 0.749 |
| **Phi-4-mini-instruct** | 0.681 | 0.495 | 0.557 *(self)* | — | — | 0.631 | 0.600 |
| **Qwen3.5-4B** | — | — | — | 0.771 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.765 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.788 | 0.798 | 0.880 | — | — | 0.767 *(self)* | 0.905 |
| **gemma-3-4b-it** | 0.570 | 0.627 | 0.597 | — | — | 0.544 | 0.602 *(self)* |

## hotpotqa — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.776 *(self)* | 0.809 | 0.861 | — | — | 0.752 | 0.890 |
| **Mistral-7B-Instruct-v0.3** | 0.637 | 0.571 *(self)* | 0.603 | — | — | 0.674 | 0.671 |
| **Phi-4-mini-instruct** | 0.654 | 0.466 | 0.535 *(self)* | — | — | 0.627 | 0.602 |
| **Qwen3.5-4B** | — | — | — | 0.755 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.734 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.767 | 0.772 | 0.808 | — | — | 0.776 *(self)* | 0.880 |
| **gemma-3-4b-it** | 0.534 | 0.551 | 0.528 | — | — | 0.536 | 0.577 *(self)* |

## hotpotqa — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.801 *(self)* | 0.825 | 0.871 | — | — | 0.785 | 0.891 |
| **Mistral-7B-Instruct-v0.3** | 0.655 | 0.634 *(self)* | 0.664 | — | — | 0.730 | 0.722 |
| **Phi-4-mini-instruct** | 0.652 | 0.468 | 0.533 *(self)* | — | — | 0.617 | 0.583 |
| **Qwen3.5-4B** | — | — | — | 0.748 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.759 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.781 | 0.783 | 0.858 | — | — | 0.782 *(self)* | 0.895 |
| **gemma-3-4b-it** | 0.657 | 0.620 | 0.694 | — | — | 0.696 | 0.740 *(self)* |

## Winning scope per (assessor, target) — the invariance view

| dataset | assessor | winner per target |
|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:AGG-mean, gemma:SPLIT-action |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama:SPLIT-action, Mistral:SPLIT-thought, Phi:SPLIT-thought, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | Phi-4-mini-instruct | Llama:SPLIT-thought, Mistral:SPLIT-thought, Phi:SPLIT-thought, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | Qwen3.5-4B | Qwen3.5:SPLIT-action |
| alfworld | Qwen3.5-9B | Qwen3.5:SPLIT-action |
| alfworld | Qwen3.6-35B-A3B | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-mean, deepseek:AGG-mean, gemma:SPLIT-action |
| alfworld | deepseek-v4-flash | deepseek:SPLIT-thought |
| alfworld | gemma-3-4b-it | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Llama-3.3-70B-Instruct | Llama:AGG-true, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-true, gemma:SPLIT-action |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Phi-4-mini-instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-thought, gemma:SPLIT-thought |
| hotpotqa | Qwen3.5-4B | Qwen3.5:SPLIT-action |
| hotpotqa | Qwen3.5-9B | Qwen3.5:SPLIT-action |
| hotpotqa | Qwen3.6-35B-A3B | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-true, gemma:SPLIT-action |
| hotpotqa | gemma-3-4b-it | Llama:AGG-true, Mistral:SPLIT-action, Phi:AGG-true, Qwen3.6:AGG-true, gemma:AGG-true |

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
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | deepseek-v4-flash | 0.004 | [0.000, 0.012] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.011 | [0.003, 0.031] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Phi-4-mini-instruct | 0.012 | [0.000, 0.031] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.010] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | Qwen3.6-35B-A3B | 0.066 | [0.046, 0.088] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | deepseek-v4-flash | 0.020 | [0.000, 0.048] |
| alfworld | Phi-4-mini-instruct | SPLIT-thought | gemma-3-4b-it | 0.007 | [0.000, 0.033] |
| alfworld | Qwen3.5-4B | SPLIT-action | Qwen3.5-4B | 0.000 | [0.000, 0.005] |
| alfworld | Qwen3.5-9B | SPLIT-action | Qwen3.5-9B | 0.000 | [0.000, 0.005] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.007 | [0.000, 0.023] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | deepseek-v4-flash | 0.003 | [0.000, 0.021] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | deepseek-v4-flash | SPLIT-thought | deepseek-v4-flash | 0.000 | [0.000, 0.004] |
| alfworld | gemma-3-4b-it | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.003 | [0.000, 0.012] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.008 | [0.000, 0.020] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.001 | [0.000, 0.021] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | gemma-3-4b-it | 0.002 | [0.000, 0.024] |
| hotpotqa | Qwen3.5-4B | SPLIT-action | Qwen3.5-4B | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.5-9B | SPLIT-action | Qwen3.5-9B | 0.000 | [0.000, 0.005] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.003] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.014 | [0.003, 0.026] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | AGG-true | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | AGG-true | Mistral-7B-Instruct-v0.3 | 0.007 | [0.000, 0.028] |
| hotpotqa | gemma-3-4b-it | AGG-true | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | AGG-true | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | AGG-true | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
