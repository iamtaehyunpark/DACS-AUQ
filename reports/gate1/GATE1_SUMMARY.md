# GATE1_SUMMARY

Each pre-registered rule with its verdict and the single number that decided it. Primary label `y_env`, restricted mode, scope SPLIT-action.

| rule | verdict | deciding number | what it is |
|---|---|---|---|
| R1 | **FAIL** | 0.669 | lowest capable-judge f under y_env |
| R2 | **PASS** | 0.948 | weakest capable-judge |r| for g (mean U vs error rate) |
| R3 | **FLAG** | 161 | cells moving more than 0.05 AUROC (of 240 compared) |
| R4 | **REPORTED** | 9.1% | share of Tier-A-incorrect steps the ensemble called correct |

## R1 — qualification floors

*If capable-judge f >= 0.70 under y_env and the assessor ordering is preserved, the qualification floors freeze.*

- floor met: **False**
- ordering preserved: **False**
- observed ordering: Llama-3.3-70B-Instruct (0.669) > Qwen3.6-35B-A3B (0.752) > Mistral-7B-Instruct-v0.3 (0.577) > gemma-3-4b-it (-0.181) > Phi-4-mini-instruct (0.636)
- Llama-3.3-70B-Instruct f=0.669 (range 0.34-1.00, width 0.66, 11 cells)
- Qwen3.6-35B-A3B f=0.752 (range 0.40-1.00, width 0.61, 11 cells)

## R2 — the g fit

*If g's correlation drops below 0.85 for capable judges, the deployment policy is reported quantile-only and g is demoted to heuristic.*

| scope / assessor | r | targets |
|---|---|---|
| alfworld/Llama-3.3-70B-Instruct | 0.948 | 6 |
| alfworld/Qwen3.6-35B-A3B | 0.987 | 6 |
| hotpotqa/Llama-3.3-70B-Instruct | 0.976 | 5 |
| hotpotqa/Qwen3.6-35B-A3B | 0.987 | 5 |

## R3 — crossprobe cell movement

*If any cell moves by more than 0.05 AUROC, flag it; headline independence deltas must be restated from the env-labelled matrix.*

161 of 240 comparable cells move by more than 0.05. Largest move -0.476 in hotpotqa / Qwen3.6-35B-A3B / gemma-3-4b-it / SPLIT-action.

| dataset | target | assessor | scope | ensemble | y_env | Δ |
|---|---|---|---|---|---|---|
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | SPLIT-action | 0.663 | 0.187 | -0.476 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | SPLIT-action | 0.717 | 0.245 | -0.472 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | SPLIT-action | 0.691 | 0.242 | -0.449 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | SPLIT-action | 0.696 | 0.251 | -0.445 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | SPLIT-thought | 0.502 | 0.934 | +0.432 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | AGG-true | 0.530 | 0.924 | +0.394 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | SPLIT-action | 0.714 | 0.328 | -0.387 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | AGG-mean | 0.541 | 0.923 | +0.381 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.528 | 0.887 | +0.359 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | SPLIT-thought | 0.525 | 0.884 | +0.358 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | AGG-true | 0.586 | 0.942 | +0.356 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | SPLIT-thought | 0.594 | 0.946 | +0.351 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | SPLIT-thought | 0.522 | 0.853 | +0.330 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.547 | 0.873 | +0.326 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | AGG-true | 0.592 | 0.915 | +0.323 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | SPLIT-thought | 0.607 | 0.924 | +0.316 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | AGG-true | 0.550 | 0.863 | +0.313 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | SPLIT-action | 0.586 | 0.889 | +0.303 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.602 | 0.904 | +0.303 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | AGG-mean | 0.624 | 0.925 | +0.301 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.531 | 0.828 | +0.296 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | AGG-mean | 0.625 | 0.914 | +0.289 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.531 | 0.810 | +0.279 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.570 | 0.848 | +0.278 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | SPLIT-thought | 0.626 | 0.892 | +0.266 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | AGG-true | 0.668 | 0.932 | +0.264 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | AGG-mean | 0.576 | 0.835 | +0.258 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | SPLIT-thought | 0.564 | 0.808 | +0.245 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | SPLIT-action | 0.651 | 0.894 | +0.243 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | SPLIT-thought | 0.603 | 0.841 | +0.238 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | SPLIT-action | 0.644 | 0.881 | +0.237 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.658 | 0.892 | +0.233 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.651 | 0.878 | +0.227 |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | SPLIT-action | 0.545 | 0.761 | +0.216 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | AGG-mean | 0.783 | 0.574 | -0.209 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | AGG-true | 0.677 | 0.884 | +0.206 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | AGG-true | 0.668 | 0.871 | +0.203 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | AGG-true | 0.704 | 0.907 | +0.203 |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | AGG-true | 0.483 | 0.685 | +0.202 |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | AGG-mean | 0.538 | 0.736 | +0.198 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | AGG-mean | 0.847 | 0.652 | -0.196 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | SPLIT-action | 0.891 | 0.697 | -0.194 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | AGG-mean | 0.600 | 0.407 | -0.194 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | SPLIT-thought | 0.699 | 0.511 | -0.189 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | AGG-true | 0.865 | 0.679 | -0.186 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | AGG-true | 0.805 | 0.619 | -0.186 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | SPLIT-action | 0.823 | 0.642 | -0.181 |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | SPLIT-thought | 0.532 | 0.713 | +0.181 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | SPLIT-thought | 0.772 | 0.591 | -0.181 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | AGG-mean | 0.693 | 0.871 | +0.179 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | AGG-mean | 0.603 | 0.428 | -0.175 |
| alfworld | deepseek-v4-flash | Llama-3.3-70B-Instruct | AGG-mean | 0.863 | 0.692 | -0.172 |
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | AGG-mean | 0.872 | 0.705 | -0.167 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.723 | 0.888 | +0.166 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.652 | 0.818 | +0.165 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | SPLIT-thought | 0.551 | 0.715 | +0.164 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | AGG-true | 0.676 | 0.840 | +0.164 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | AGG-true | 0.887 | 0.724 | -0.163 |
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | SPLIT-action | 0.883 | 0.720 | -0.163 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | AGG-true | 0.736 | 0.899 | +0.163 |

_101 further flagged cells in `tables_gate1/crossprobe_side_by_side.md`._

## R4 — ensemble error rate

*Report regardless of outcome.*

On the 24631 judged steps the environment labelled incorrect, the 3-judge ensemble called **9.1%** of them correct. Mean fraction of judges voting correct on those steps: 0.139.
