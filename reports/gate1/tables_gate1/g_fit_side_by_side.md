# Gate-1 Phase 5 — the g fit (mean U vs target error rate)

Per assessor, the correlation across its targets between pooled mean U and the target's error rate. R2 asks whether this drops below 0.85 for the capable judges under the environment label.

| assessor scope | ensemble | ensemble_on_env_support | env_restricted | env_full | n targets |
|---|---|---|---|---|---|
| ALL/Llama-3.3-70B-Instruct | 0.951 | 0.977 | 0.945 | 0.717 | 11 |
| ALL/Mistral-7B-Instruct-v0.3 | 0.856 | 0.815 | 0.695 | 0.736 | 11 |
| ALL/Phi-4-mini-instruct | 0.691 | 0.612 | 0.626 | 0.636 | 11 |
| ALL/Qwen3.5-27B | — | — | — | — | 1 |
| ALL/Qwen3.5-4B | — | — | — | — | 2 |
| ALL/Qwen3.5-9B | — | — | — | — | 2 |
| ALL/Qwen3.6-35B-A3B | 0.963 | 0.964 | 0.961 | 0.828 | 11 |
| ALL/deepseek-v4-flash | — | — | — | — | 1 |
| ALL/gemma-3-4b-it | 0.720 | 0.629 | 0.531 | 0.689 | 11 |
| alfworld/Llama-3.3-70B-Instruct | 0.990 | 0.990 | 0.948 | 0.981 | 6 |
| alfworld/Mistral-7B-Instruct-v0.3 | 0.824 | 0.826 | 0.810 | 0.818 | 6 |
| alfworld/Phi-4-mini-instruct | 0.653 | 0.676 | 0.805 | 0.725 | 6 |
| alfworld/Qwen3.5-27B | — | — | — | — | 1 |
| alfworld/Qwen3.5-4B | — | — | — | — | 1 |
| alfworld/Qwen3.5-9B | — | — | — | — | 1 |
| alfworld/Qwen3.6-35B-A3B | 0.960 | 0.964 | 0.987 | 0.978 | 6 |
| alfworld/deepseek-v4-flash | — | — | — | — | 1 |
| alfworld/gemma-3-4b-it | 0.673 | 0.685 | 0.755 | 0.733 | 6 |
| hotpotqa/Llama-3.3-70B-Instruct | 0.998 | 0.998 | 0.976 | 0.979 | 5 |
| hotpotqa/Mistral-7B-Instruct-v0.3 | 0.851 | 0.805 | 0.820 | 0.785 | 5 |
| hotpotqa/Phi-4-mini-instruct | 0.559 | 0.463 | 0.535 | 0.483 | 5 |
| hotpotqa/Qwen3.5-4B | — | — | — | — | 1 |
| hotpotqa/Qwen3.5-9B | — | — | — | — | 1 |
| hotpotqa/Qwen3.6-35B-A3B | 0.972 | 0.977 | 0.987 | 0.937 | 5 |
| hotpotqa/gemma-3-4b-it | 0.620 | 0.514 | 0.526 | 0.484 | 5 |
