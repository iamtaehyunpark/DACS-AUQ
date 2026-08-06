# Cross-probe matrix — step-level AUROC (soft, 3-judge labels)

Positive class = judge-incorrect. **Labels are LLM-derived**: these are
not headline numbers until recomputed against environment-anchored
targets (gate 1). Diagonal = the arm's own probes (self-assessment).

## alfworld — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.636 *(self)* | 0.656 | 0.535 | — | — | — | 0.664 | 0.617 | 0.624 |
| **Mistral-7B-Instruct-v0.3** | 0.627 | 0.571 *(self)* | 0.514 | — | — | — | 0.619 | 0.582 | 0.625 |
| **Phi-4-mini-instruct** | 0.649 | 0.594 | 0.542 *(self)* | — | — | — | 0.648 | 0.647 | 0.591 |
| **Qwen3.5-27B** | — | — | — | 0.752 *(self)* | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.677 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.666 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.686 | 0.676 | 0.559 | — | — | — | 0.699 *(self)* | 0.675 | 0.644 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.663 *(self)* | — |
| **gemma-3-4b-it** | 0.535 | 0.521 | 0.530 | — | — | — | 0.490 | 0.480 | 0.481 *(self)* |

## alfworld — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.691 *(self)* | 0.776 | 0.641 | — | — | — | 0.689 | 0.673 | 0.713 |
| **Mistral-7B-Instruct-v0.3** | 0.637 | 0.598 *(self)* | 0.542 | — | — | — | 0.658 | 0.619 | 0.624 |
| **Phi-4-mini-instruct** | 0.628 | 0.597 | 0.559 *(self)* | — | — | — | 0.702 | 0.666 | 0.609 |
| **Qwen3.5-27B** | — | — | — | 0.759 *(self)* | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.660 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.667 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.719 | 0.777 | 0.647 | — | — | — | 0.714 *(self)* | 0.716 | 0.763 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.671 *(self)* | — |
| **gemma-3-4b-it** | 0.591 | 0.567 | 0.514 | — | — | — | 0.596 | 0.568 | 0.584 *(self)* |

## alfworld — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.680 *(self)* | 0.736 | 0.590 | — | — | — | 0.674 | 0.651 | 0.675 |
| **Mistral-7B-Instruct-v0.3** | 0.632 | 0.585 *(self)* | 0.517 | — | — | — | 0.642 | 0.609 | 0.602 |
| **Phi-4-mini-instruct** | 0.639 | 0.604 | 0.553 *(self)* | — | — | — | 0.667 | 0.656 | 0.599 |
| **Qwen3.5-27B** | — | — | — | 0.744 *(self)* | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.648 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.647 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.707 | 0.749 | 0.604 | — | — | — | 0.705 *(self)* | 0.701 | 0.706 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.670 *(self)* | — |
| **gemma-3-4b-it** | 0.584 | 0.545 | 0.514 | — | — | — | 0.562 | 0.537 | 0.519 *(self)* |

## alfworld — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-27B | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | deepseek-v4-flash | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.667 *(self)* | 0.741 | 0.626 | — | — | — | 0.678 | 0.659 | 0.697 |
| **Mistral-7B-Instruct-v0.3** | 0.638 | 0.588 *(self)* | 0.555 | — | — | — | 0.653 | 0.620 | 0.674 |
| **Phi-4-mini-instruct** | 0.612 | 0.558 | 0.519 *(self)* | — | — | — | 0.600 | 0.621 | 0.518 |
| **Qwen3.5-27B** | — | — | — | — | — | — | — | — | — |
| **Qwen3.5-4B** | — | — | — | — | 0.641 *(self)* | — | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | — | 0.640 *(self)* | — | — | — |
| **Qwen3.6-35B-A3B** | 0.702 | 0.757 | 0.621 | — | — | — | 0.680 *(self)* | 0.682 | 0.718 |
| **deepseek-v4-flash** | — | — | — | — | — | — | — | 0.619 *(self)* | — |
| **gemma-3-4b-it** | 0.573 | 0.516 | 0.485 | — | — | — | 0.534 | 0.513 | 0.434 *(self)* |

## hotpotqa — SPLIT-thought

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.662 *(self)* | 0.667 | 0.646 | — | — | 0.718 | 0.758 |
| **Mistral-7B-Instruct-v0.3** | 0.532 | 0.552 *(self)* | 0.530 | — | — | 0.554 | 0.552 |
| **Phi-4-mini-instruct** | 0.641 | 0.557 | 0.550 *(self)* | — | — | 0.616 | 0.619 |
| **Qwen3.5-4B** | — | — | — | 0.732 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.746 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.682 | 0.679 | 0.652 | — | — | 0.754 *(self)* | 0.757 |
| **gemma-3-4b-it** | 0.523 | 0.553 | 0.529 | — | — | 0.522 | 0.579 *(self)* |

## hotpotqa — SPLIT-action

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.745 *(self)* | 0.828 | 0.851 | — | — | 0.755 | 0.848 |
| **Mistral-7B-Instruct-v0.3** | 0.636 | 0.673 *(self)* | 0.669 | — | — | 0.677 | 0.673 |
| **Phi-4-mini-instruct** | 0.670 | 0.646 | 0.631 *(self)* | — | — | 0.678 | 0.661 |
| **Qwen3.5-4B** | — | — | — | 0.798 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.816 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.743 | 0.812 | 0.834 | — | — | 0.805 *(self)* | 0.837 |
| **gemma-3-4b-it** | 0.627 | 0.662 | 0.730 | — | — | 0.617 | 0.682 *(self)* |

## hotpotqa — AGG-mean

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.710 *(self)* | 0.771 | 0.785 | — | — | 0.734 | 0.820 |
| **Mistral-7B-Instruct-v0.3** | 0.594 | 0.592 *(self)* | 0.583 | — | — | 0.606 | 0.603 |
| **Phi-4-mini-instruct** | 0.666 | 0.602 | 0.599 *(self)* | — | — | 0.649 | 0.645 |
| **Qwen3.5-4B** | — | — | — | 0.757 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.772 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.726 | 0.771 | 0.772 | — | — | 0.782 *(self)* | 0.815 |
| **gemma-3-4b-it** | 0.574 | 0.576 | 0.614 | — | — | 0.524 | 0.603 *(self)* |

## hotpotqa — AGG-true

| assessor \ target | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | Qwen3.5-4B | Qwen3.5-9B | Qwen3.6-35B-A3B | gemma-3-4b-it |
|---|---|---|---|---|---|---|---|
| **Llama-3.3-70B-Instruct** | 0.726 *(self)* | 0.796 | 0.804 | — | — | 0.741 | 0.816 |
| **Mistral-7B-Instruct-v0.3** | 0.614 | 0.643 *(self)* | 0.611 | — | — | 0.643 | 0.639 |
| **Phi-4-mini-instruct** | 0.640 | 0.573 | 0.554 *(self)* | — | — | 0.617 | 0.601 |
| **Qwen3.5-4B** | — | — | — | 0.754 *(self)* | — | — | — |
| **Qwen3.5-9B** | — | — | — | — | 0.782 *(self)* | — | — |
| **Qwen3.6-35B-A3B** | 0.726 | 0.784 | 0.804 | — | — | 0.781 *(self)* | 0.810 |
| **gemma-3-4b-it** | 0.577 | 0.596 | 0.631 | — | — | 0.583 | 0.651 *(self)* |

## Winning scope per (assessor, target) — the invariance view

| dataset | assessor | winner per target |
|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama:AGG-true, Mistral:SPLIT-action, Phi:AGG-true, Qwen3.6:SPLIT-action, deepseek:AGG-true, gemma:AGG-true |
| alfworld | Phi-4-mini-instruct | Llama:SPLIT-thought, Mistral:AGG-mean, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | Qwen3.5-27B | Qwen3.5:SPLIT-action |
| alfworld | Qwen3.5-4B | Qwen3.5:SPLIT-thought |
| alfworld | Qwen3.5-9B | Qwen3.5:SPLIT-action |
| alfworld | Qwen3.6-35B-A3B | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| alfworld | deepseek-v4-flash | deepseek:SPLIT-action |
| alfworld | gemma-3-4b-it | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-thought, Qwen3.6:SPLIT-action, deepseek:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Llama-3.3-70B-Instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Phi-4-mini-instruct | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | Qwen3.5-4B | Qwen3.5:SPLIT-action |
| hotpotqa | Qwen3.5-9B | Qwen3.5:SPLIT-action |
| hotpotqa | Qwen3.6-35B-A3B | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |
| hotpotqa | gemma-3-4b-it | Llama:SPLIT-action, Mistral:SPLIT-action, Phi:SPLIT-action, Qwen3.6:SPLIT-action, gemma:SPLIT-action |

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
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.003] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Llama-3.3-70B-Instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.018] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Mistral-7B-Instruct-v0.3 | 0.010 | [0.000, 0.027] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Phi-4-mini-instruct | 0.000 | [0.000, 0.011] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | Qwen3.6-35B-A3B | 0.005 | [0.000, 0.020] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | deepseek-v4-flash | 0.000 | [0.000, 0.016] |
| alfworld | Mistral-7B-Instruct-v0.3 | AGG-true | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.021 | [0.004, 0.039] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.007 | [0.000, 0.042] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.009] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.004] |
| alfworld | Phi-4-mini-instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.024] |
| alfworld | Qwen3.5-27B | SPLIT-action | Qwen3.5-27B | 0.000 | [0.000, 0.008] |
| alfworld | Qwen3.5-4B | SPLIT-thought | Qwen3.5-4B | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.5-9B | SPLIT-action | Qwen3.5-9B | 0.000 | [0.000, 0.014] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| alfworld | deepseek-v4-flash | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.010] |
| alfworld | gemma-3-4b-it | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.003] |
| alfworld | gemma-3-4b-it | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | Phi-4-mini-instruct | 0.015 | [0.000, 0.057] |
| alfworld | gemma-3-4b-it | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | deepseek-v4-flash | 0.000 | [0.000, 0.000] |
| alfworld | gemma-3-4b-it | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Llama-3.3-70B-Instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Mistral-7B-Instruct-v0.3 | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.004] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Phi-4-mini-instruct | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.5-4B | SPLIT-action | Qwen3.5-4B | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.5-9B | SPLIT-action | Qwen3.5-9B | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | Qwen3.6-35B-A3B | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Llama-3.3-70B-Instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Mistral-7B-Instruct-v0.3 | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Phi-4-mini-instruct | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | Qwen3.6-35B-A3B | 0.000 | [0.000, 0.000] |
| hotpotqa | gemma-3-4b-it | SPLIT-action | gemma-3-4b-it | 0.000 | [0.000, 0.000] |
