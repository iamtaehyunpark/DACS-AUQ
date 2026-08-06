# Cross-probe matrix — step-level AUROC (soft, 3-judge labels)

Positive class = judge-incorrect. **Labels are LLM-derived**: these are
not headline numbers until recomputed against environment-anchored
targets (gate 1). Diagonal = the arm's own probes (self-assessment).

## alfworld — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.672 *(self)* | 0.662 | 0.511 | — | — | — | 0.671 | 0.649 | 0.591 |
| **Mistral-7B-Instruct-v0.3** | 0.683 | 0.593 *(self)* | 0.538 | — | — | — | 0.637 | 0.621 | 0.657 |
| **Phi-4-mini-instruct** | 0.701 | 0.583 | 0.572 *(self)* | — | — | — | 0.659 | 0.713 | 0.638 |
| **Qwen3.5-27B** | — | — | — | 0.773 *(self)* | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.689 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.669 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.689 | 0.683 | 0.545 | — | — | — | 0.709 *(self)* | 0.699 | 0.644 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.703 *(self)* | — |
| **gemma-3-4b-it** | 0.544 | 0.456 | 0.493 | — | — | — | 0.480 | 0.424 | 0.465 *(self)* |

## alfworld — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.720 *(self)* | 0.793 | 0.642 | — | — | — | 0.698 | 0.728 | 0.697 |
| **Mistral-7B-Instruct-v0.3** | 0.687 | 0.670 *(self)* | 0.597 | — | — | — | 0.683 | 0.688 | 0.659 |
| **Phi-4-mini-instruct** | 0.692 | 0.659 | 0.617 *(self)* | — | — | — | 0.719 | 0.761 | 0.635 |
| **Qwen3.5-27B** | — | — | — | 0.791 *(self)* | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.680 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.695 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.747 | 0.818 | 0.659 | — | — | — | 0.728 *(self)* | 0.778 | 0.780 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.730 *(self)* | — |
| **gemma-3-4b-it** | 0.632 | 0.595 | 0.538 | — | — | — | 0.599 | 0.626 | 0.612 *(self)* |

## alfworld — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.705 *(self)* | 0.747 | 0.574 | — | — | — | 0.682 | 0.692 | 0.652 |
| **Mistral-7B-Instruct-v0.3** | 0.683 | 0.637 *(self)* | 0.554 | — | — | — | 0.665 | 0.666 | 0.628 |
| **Phi-4-mini-instruct** | 0.699 | 0.633 | 0.608 *(self)* | — | — | — | 0.681 | 0.736 | 0.640 |
| **Qwen3.5-27B** | — | — | — | 0.768 *(self)* | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.664 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.658 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.723 | 0.779 | 0.603 | — | — | — | 0.718 *(self)* | 0.745 | 0.719 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.718 *(self)* | — |
| **gemma-3-4b-it** | 0.613 | 0.541 | 0.525 | — | — | — | 0.560 | 0.551 | 0.522 *(self)* |

## alfworld — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.706 *(self)* | 0.754 | 0.638 | — | — | — | 0.687 | 0.708 | 0.679 |
| **Mistral-7B-Instruct-v0.3** | 0.723 | 0.677 *(self)* | 0.642 | — | — | — | 0.680 | 0.722 | 0.733 |
| **Phi-4-mini-instruct** | 0.662 | 0.601 | 0.558 *(self)* | — | — | — | 0.608 | 0.685 | 0.538 |
| **Qwen3.5-27B** | — | — | — | — | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.656 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.657 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.719 | 0.783 | 0.619 | — | — | — | 0.692 *(self)* | 0.726 | 0.724 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.713 *(self)* | — |
| **gemma-3-4b-it** | 0.605 | 0.548 | 0.506 | — | — | — | 0.538 | 0.512 | 0.440 *(self)* |

## hotpotqa — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.736 *(self)* | 0.819 | 0.671 | — | — | 0.784 | 0.749 |
| **Mistral-7B-Instruct-v0.3** | 0.828 | 0.887 *(self)* | 0.810 | — | — | 0.873 | 0.848 |
| **Phi-4-mini-instruct** | 0.892 | 0.934 | 0.884 *(self)* | — | — | 0.924 | 0.946 |
| **Qwen3.5-4B** | — | — | — | 0.883 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.894 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.754 | 0.849 | 0.695 | — | — | 0.843 *(self)* | 0.856 |
| **gemma-3-4b-it** | 0.715 | 0.808 | 0.727 | — | — | 0.853 | 0.841 *(self)* |

## hotpotqa — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.756 *(self)* | 0.951 | 0.843 | — | — | 0.789 | 0.832 |
| **Mistral-7B-Instruct-v0.3** | 0.793 | 0.888 *(self)* | 0.692 | — | — | 0.862 | 0.863 |
| **Phi-4-mini-instruct** | 0.839 | 0.889 | 0.760 *(self)* | — | — | 0.894 | 0.881 |
| **Qwen3.5-4B** | — | — | — | 0.831 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.832 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.854 | 0.967 | 0.911 | — | — | 0.863 *(self)* | 0.922 |
| **gemma-3-4b-it** | 0.242 | 0.251 | 0.245 | — | — | 0.187 | 0.328 *(self)* |

## hotpotqa — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.764 *(self)* | 0.925 | 0.803 | — | — | 0.800 | 0.818 |
| **Mistral-7B-Instruct-v0.3** | 0.818 | 0.904 *(self)* | 0.724 | — | — | 0.892 | 0.878 |
| **Phi-4-mini-instruct** | 0.871 | 0.923 | 0.835 *(self)* | — | — | 0.914 | 0.925 |
| **Qwen3.5-4B** | — | — | — | 0.873 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.888 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.824 | 0.944 | 0.832 | — | — | 0.865 *(self)* | 0.910 |
| **gemma-3-4b-it** | 0.428 | 0.553 | 0.407 | — | — | 0.556 | 0.634 *(self)* |

## hotpotqa — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.804 *(self)* | 0.962 | 0.816 | — | — | 0.860 | 0.825 |
| **Mistral-7B-Instruct-v0.3** | 0.871 | 0.932 *(self)* | 0.840 | — | — | 0.899 | 0.907 |
| **Phi-4-mini-instruct** | 0.884 | 0.924 | 0.863 *(self)* | — | — | 0.915 | 0.942 |
| **Qwen3.5-4B** | — | — | — | 0.857 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.860 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.869 | 0.965 | 0.883 | — | — | 0.883 *(self)* | 0.911 |
| **gemma-3-4b-it** | 0.683 | 0.667 | 0.635 | — | — | 0.754 | 0.798 *(self)* |

## Winning scope per (assessor, target) — the invariance view

| dataset | assessor | winner per target |
|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama:AGG-true, Mistral:AGG-true, Phi:AGG-true, Qwen3.6:SPLIT-action, deepseek:AGG-true, gemma:AGG-true |
| alfworld | Phi-4-mini-instruct | Llama:SPLIT-thought, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:AGG-mean |
| alfworld | Qwen3.5-27B | Qwen3.5:SPLIT-action |
| alfworld | Qwen3.5-4B | Qwen3.5:SPLIT-thought |
| alfworld | Qwen3.5-9B | Qwen3.5:SPLIT-action |
| alfworld | Qwen3.6-35B-A3B | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | deepseek-v4-flash | deepseek:SPLIT-action |
| alfworld | gemma-3-4b-it | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Llama-3.3-70B-Instruct | Llama:AGG-true, Mistral:AGG-true, Phi:SPLIT-action, Qwen3.6:AGG-true, gemma:SPLIT-action |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama:AGG-true, Mistral:AGG-true, Phi:AGG-true, Qwen3.6:AGG-true, gemma:AGG-true |
| hotpotqa | Phi-4-mini-instruct | Llama:SPLIT-thought, Mistral:SPLIT-thought, Phi:SPLIT-thought, Qwen3.6:SPLIT-thought, gemma:SPLIT-thought |
| hotpotqa | Qwen3.5-4B | Qwen3.5:SPLIT-thought |
| hotpotqa | Qwen3.5-9B | Qwen3.5:SPLIT-thought |
| hotpotqa | Qwen3.6-35B-A3B | Llama:AGG-true, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:AGG-true, gemma:SPLIT-action |
| hotpotqa | gemma-3-4b-it | Llama:SPLIT-thought, Mistral:SPLIT-thought, Phi:SPLIT-thought, Qwen3.6:SPLIT-thought, gemma:SPLIT-thought |

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
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.008] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.003] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.011] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Qwen3.6-35B-A3B | 0.002 | [0.000, 0.016] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.009 | [0.001, 0.024] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.007] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | gemma-3-4b-it | 0.004 | [0.000, 0.044] |
| alfworld | Qwen3.5-27B | SPLIT-action | Qwen3.5-27B | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.5-4B | SPLIT-thought | Qwen3.5-4B | 0.000 | [0.000, 0.008] |
| alfworld | Qwen3.5-9B | SPLIT-action | Qwen3.5-9B | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | deepseek-v4-flash | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.008] |
| alfworld | gemma-3-4b-it | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.004] |
| alfworld | gemma-3-4b-it | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | AGG-true | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | AGG-true | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | AGG-true | Phi-4-mini-instruct | 0.027 | [0.003, 0.054] |
| hotpotqa | Llama-3.3-70B-Instruct | AGG-true | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | AGG-true | gemma-3-4b-it | 0.007 | [0.000, 0.023] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | AGG-true | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | AGG-true | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.007] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | AGG-true | Phi-4-mini-instruct | 0.000 | [0.000, 0.022] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | AGG-true | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.006] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | AGG-true | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-thought | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.005] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-thought | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.010] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-thought | Phi-4-mini-instruct | 0.000 | [0.000, 0.020] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-thought | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.001] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-thought | gemma-3-4b-it | 0.000 | [0.000, 0.012] |
| hotpotqa | Qwen3.5-4B | SPLIT-thought | Qwen3.5-4B | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.5-9B | SPLIT-thought | Qwen3.5-9B | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.015 | [0.005, 0.025] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.003] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.020 | [0.008, 0.031] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.002] |
| hotpotqa | gemma-3-4b-it | SPLIT-thought | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.005] |
| hotpotqa | gemma-3-4b-it | SPLIT-thought | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-thought | Phi-4-mini-instruct | 0.000 | [0.000, 0.031] |
| hotpotqa | gemma-3-4b-it | SPLIT-thought | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-thought | gemma-3-4b-it | 0.000 | [0.000, 0.004] |
