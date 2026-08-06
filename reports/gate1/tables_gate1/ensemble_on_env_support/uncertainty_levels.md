# Uncertainty level by correct/incorrect group — scope SPLIT-action

AUROC measures ranking; this measures WHERE the scores sit. A judge whose
level and optimal cut point hold across targets can have its threshold
characterised once. One whose level moves must be re-calibrated per target
even if its recipe transfers.

`gap` = mean U on judge-incorrect minus mean U on judge-correct steps.
Labels are the 3-judge ensemble, so provisional until gate 1.

## alfworld

| assessor | target | arm | mu_inc | mu_cor | gap | level | thr | bal_acc | n |
|---|---|---|---|---|---|---|---|---|---|
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.452 | 0.040 | +0.412 | 0.259 | 0.000 | 0.828 | 4492 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.748 | 0.167 | +0.580 | 0.613 | 0.001 | 0.810 | 6321 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.859 | 0.350 | +0.509 | 0.752 | 0.963 | 0.758 | 6445 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.179 | 0.016 | +0.163 | 0.079 | 0.000 | 0.755 | 3110 |
| Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.252 | 0.010 | +0.242 | 0.094 | 0.000 | 0.789 | 3016 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.921 | 0.267 | +0.654 | 0.849 | 0.986 | 0.832 | 6730 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.098 | 0.031 | +0.067 | 0.066 | 0.000 | 0.678 | 4492 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.058 | 0.031 | +0.027 | 0.051 | 0.000 | 0.584 | 6321 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.107 | 0.087 | +0.020 | 0.103 | 0.000 | 0.589 | 6445 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.035 | 0.005 | +0.030 | 0.016 | 0.000 | 0.592 | 3110 |
| Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.019 | 0.010 | +0.009 | 0.013 | 0.000 | 0.605 | 3016 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.082 | 0.046 | +0.035 | 0.078 | 0.000 | 0.678 | 6730 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.433 | 0.347 | +0.086 | 0.393 | 0.321 | 0.567 | 4492 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.389 | 0.394 | -0.005 | 0.390 | 0.023 | 0.519 | 6321 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.344 | 0.367 | -0.023 | 0.349 | 0.023 | 0.517 | 6445 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.123 | 0.084 | +0.039 | 0.099 | 0.018 | 0.556 | 3110 |
| Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.204 | 0.171 | +0.033 | 0.182 | 0.007 | 0.545 | 3016 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.311 | 0.223 | +0.088 | 0.301 | 0.095 | 0.602 | 6730 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.275 | 0.179 | +0.096 | 0.231 | 0.095 | 0.618 | 3981 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.192 | 0.072 | +0.120 | 0.129 | 0.053 | 0.667 | 4024 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.862 | 0.421 | +0.442 | 0.655 | 0.794 | 0.836 | 4492 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.889 | 0.533 | +0.356 | 0.806 | 0.789 | 0.796 | 6321 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.938 | 0.641 | +0.297 | 0.875 | 0.909 | 0.752 | 6445 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.489 | 0.282 | +0.207 | 0.362 | 0.407 | 0.650 | 3110 |
| Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.718 | 0.322 | +0.396 | 0.460 | 0.619 | 0.790 | 3016 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.937 | 0.524 | +0.414 | 0.891 | 0.888 | 0.842 | 6730 |
| deepseek-v4-flash | deepseek-v4-flash | self | 0.415 | 0.217 | +0.198 | 0.286 | 0.029 | 0.685 | 3016 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.173 | 0.188 | -0.014 | 0.180 | 0.000 | 0.557 | 4492 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.253 | 0.283 | -0.030 | 0.260 | 0.000 | 0.579 | 6321 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.263 | 0.337 | -0.074 | 0.279 | 0.000 | 0.580 | 6445 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.067 | 0.023 | +0.043 | 0.040 | 0.000 | 0.608 | 3110 |
| gemma-3-4b-it | deepseek-v4-flash | cross | 0.032 | 0.029 | +0.002 | 0.030 | 0.000 | 0.552 | 3016 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.107 | 0.159 | -0.052 | 0.113 | 0.000 | 0.672 | 6730 |

## hotpotqa

| assessor | target | arm | mu_inc | mu_cor | gap | level | thr | bal_acc | n |
|---|---|---|---|---|---|---|---|---|---|
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.232 | 0.045 | +0.187 | 0.104 | 0.000 | 0.740 | 1163 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.796 | 0.249 | +0.547 | 0.616 | 0.881 | 0.781 | 2375 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.848 | 0.196 | +0.652 | 0.662 | 0.731 | 0.835 | 1885 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.130 | 0.008 | +0.121 | 0.037 | 0.000 | 0.730 | 1114 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.839 | 0.154 | +0.685 | 0.597 | 0.007 | 0.847 | 1658 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.025 | 0.017 | +0.008 | 0.019 | 0.000 | 0.666 | 1163 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.043 | 0.022 | +0.021 | 0.036 | 0.000 | 0.650 | 2375 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.091 | 0.017 | +0.073 | 0.070 | 0.000 | 0.657 | 1885 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.017 | 0.003 | +0.014 | 0.006 | 0.000 | 0.712 | 1114 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.035 | 0.011 | +0.023 | 0.027 | 0.000 | 0.701 | 1658 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.387 | 0.231 | +0.157 | 0.280 | 0.182 | 0.653 | 1163 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.264 | 0.273 | -0.009 | 0.267 | 0.018 | 0.513 | 2375 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.259 | 0.211 | +0.048 | 0.245 | 0.023 | 0.562 | 1885 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.186 | 0.137 | +0.049 | 0.149 | 0.018 | 0.649 | 1114 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.244 | 0.198 | +0.045 | 0.228 | 0.014 | 0.595 | 1658 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.477 | 0.219 | +0.258 | 0.305 | 0.164 | 0.712 | 1375 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.352 | 0.136 | +0.216 | 0.196 | 0.047 | 0.710 | 1092 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.730 | 0.368 | +0.363 | 0.483 | 0.591 | 0.728 | 1163 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.914 | 0.625 | +0.290 | 0.819 | 0.834 | 0.745 | 2375 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.927 | 0.509 | +0.418 | 0.808 | 0.862 | 0.814 | 1885 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.492 | 0.215 | +0.277 | 0.280 | 0.202 | 0.719 | 1114 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.906 | 0.390 | +0.516 | 0.724 | 0.702 | 0.834 | 1658 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.122 | 0.083 | +0.040 | 0.095 | 0.000 | 0.568 | 1163 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.059 | 0.054 | +0.005 | 0.057 | 0.000 | 0.618 | 2375 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.141 | 0.118 | +0.023 | 0.134 | 0.000 | 0.612 | 1885 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.012 | 0.014 | -0.002 | 0.014 | 0.000 | 0.568 | 1114 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.052 | 0.080 | -0.028 | 0.062 | 0.000 | 0.614 | 1658 |

## Is the operating point a property of the assessor?

Spread of `level` and `thr` across that assessor's targets. Small spread =
one threshold serves every target; large = re-fit per deployment.

| dataset | assessor | targets | level mean | level range | thr mean | thr range |
|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 0.441 | 0.079–0.849 | 0.325 | 0.000–0.986 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 0.055 | 0.013–0.103 | 0.000 | 0.000–0.000 |
| alfworld | Phi-4-mini-instruct | 6 | 0.286 | 0.099–0.393 | 0.081 | 0.007–0.321 |
| alfworld | Qwen3.6-35B-A3B | 6 | 0.675 | 0.362–0.891 | 0.734 | 0.407–0.909 |
| alfworld | gemma-3-4b-it | 6 | 0.150 | 0.030–0.279 | 0.000 | 0.000–0.000 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 0.403 | 0.037–0.662 | 0.324 | 0.000–0.881 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 0.032 | 0.006–0.070 | 0.000 | 0.000–0.000 |
| hotpotqa | Phi-4-mini-instruct | 5 | 0.234 | 0.149–0.280 | 0.051 | 0.014–0.182 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 0.623 | 0.280–0.819 | 0.638 | 0.202–0.862 |
| hotpotqa | gemma-3-4b-it | 5 | 0.072 | 0.014–0.134 | 0.000 | 0.000–0.000 |
