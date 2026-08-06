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
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.280 | 0.103 | +0.177 | 0.249 | 0.000 | 0.644 | 4765 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.628 | 0.218 | +0.410 | 0.603 | 0.000 | 0.731 | 6482 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.762 | 0.528 | +0.234 | 0.747 | 0.269 | 0.621 | 6604 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.095 | 0.024 | +0.071 | 0.078 | 0.000 | 0.641 | 3197 |
| Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.111 | 0.021 | +0.090 | 0.089 | 0.000 | 0.621 | 3304 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.859 | 0.499 | +0.360 | 0.846 | 0.977 | 0.687 | 6790 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.068 | 0.054 | +0.014 | 0.066 | 0.000 | 0.611 | 4765 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.053 | 0.031 | +0.022 | 0.051 | 0.000 | 0.576 | 6482 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.102 | 0.110 | -0.008 | 0.103 | 0.000 | 0.558 | 6604 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.020 | 0.007 | +0.012 | 0.017 | 0.000 | 0.629 | 3197 |
| Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.014 | 0.010 | +0.003 | 0.013 | 0.000 | 0.602 | 3304 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.076 | 0.128 | -0.052 | 0.078 | 0.000 | 0.644 | 6790 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.413 | 0.306 | +0.107 | 0.394 | 0.060 | 0.626 | 4765 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.395 | 0.300 | +0.096 | 0.389 | 0.119 | 0.573 | 6482 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.354 | 0.311 | +0.043 | 0.351 | 0.060 | 0.559 | 6604 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.113 | 0.057 | +0.055 | 0.099 | 0.018 | 0.660 | 3197 |
| Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.203 | 0.125 | +0.078 | 0.184 | 0.029 | 0.636 | 3304 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.303 | 0.243 | +0.060 | 0.301 | 0.095 | 0.601 | 6790 |
| Qwen3.5-27B | Qwen3.5-27B | self | 0.161 | 0.056 | +0.105 | 0.134 | 0.012 | 0.696 | 3241 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.244 | 0.162 | +0.082 | 0.230 | 0.060 | 0.628 | 4113 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.136 | 0.090 | +0.046 | 0.127 | 0.012 | 0.635 | 4265 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.693 | 0.434 | +0.260 | 0.648 | 0.731 | 0.653 | 4765 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.820 | 0.510 | +0.310 | 0.801 | 0.755 | 0.734 | 6482 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.885 | 0.712 | +0.173 | 0.874 | 0.812 | 0.630 | 6604 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.407 | 0.221 | +0.186 | 0.360 | 0.097 | 0.668 | 3197 |
| Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.509 | 0.288 | +0.221 | 0.455 | 0.225 | 0.652 | 3304 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.900 | 0.615 | +0.286 | 0.890 | 0.857 | 0.711 | 6790 |
| deepseek-v4-flash | deepseek-v4-flash | self | 0.319 | 0.171 | +0.148 | 0.283 | 0.095 | 0.625 | 3304 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.185 | 0.164 | +0.020 | 0.181 | 0.000 | 0.582 | 4765 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.260 | 0.252 | +0.008 | 0.260 | 0.000 | 0.573 | 6482 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.276 | 0.332 | -0.056 | 0.279 | 0.000 | 0.560 | 6604 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.043 | 0.028 | +0.015 | 0.040 | 0.000 | 0.577 | 3197 |
| gemma-3-4b-it | deepseek-v4-flash | cross | 0.030 | 0.029 | +0.001 | 0.030 | 0.000 | 0.554 | 3304 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.109 | 0.215 | -0.106 | 0.113 | 0.000 | 0.632 | 6790 |

## hotpotqa

| assessor | target | arm | mu_inc | mu_cor | gap | level | thr | bal_acc | n |
|---|---|---|---|---|---|---|---|---|---|
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.116 | 0.031 | +0.085 | 0.064 | 0.000 | 0.700 | 2530 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.624 | 0.177 | +0.447 | 0.502 | 0.002 | 0.753 | 3224 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.671 | 0.169 | +0.502 | 0.512 | 0.000 | 0.786 | 2716 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.044 | 0.015 | +0.030 | 0.027 | 0.000 | 0.694 | 2192 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.629 | 0.128 | +0.501 | 0.431 | 0.000 | 0.780 | 2565 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.019 | 0.017 | +0.002 | 0.018 | 0.000 | 0.617 | 2530 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.036 | 0.022 | +0.014 | 0.033 | 0.000 | 0.652 | 3224 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.070 | 0.028 | +0.042 | 0.057 | 0.000 | 0.624 | 2716 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.008 | 0.006 | +0.002 | 0.007 | 0.000 | 0.653 | 2192 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.028 | 0.023 | +0.005 | 0.026 | 0.000 | 0.637 | 2565 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.320 | 0.179 | +0.140 | 0.234 | 0.148 | 0.643 | 2530 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.270 | 0.174 | +0.096 | 0.244 | 0.095 | 0.624 | 3224 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.248 | 0.133 | +0.115 | 0.212 | 0.095 | 0.614 | 2716 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.182 | 0.080 | +0.103 | 0.121 | 0.060 | 0.654 | 2192 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.241 | 0.125 | +0.115 | 0.195 | 0.095 | 0.637 | 2565 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.336 | 0.108 | +0.228 | 0.224 | 0.068 | 0.738 | 2371 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.222 | 0.039 | +0.183 | 0.129 | 0.023 | 0.758 | 2296 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.548 | 0.267 | +0.281 | 0.376 | 0.398 | 0.693 | 2530 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.829 | 0.384 | +0.444 | 0.707 | 0.704 | 0.757 | 3224 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.817 | 0.332 | +0.485 | 0.663 | 0.703 | 0.776 | 2716 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.337 | 0.090 | +0.246 | 0.191 | 0.147 | 0.753 | 2192 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.764 | 0.282 | +0.482 | 0.574 | 0.501 | 0.773 | 2565 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.085 | 0.047 | +0.037 | 0.062 | 0.000 | 0.617 | 2530 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.055 | 0.029 | +0.026 | 0.048 | 0.000 | 0.637 | 3224 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.131 | 0.033 | +0.098 | 0.100 | 0.000 | 0.679 | 2716 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.010 | 0.008 | +0.003 | 0.009 | 0.000 | 0.605 | 2192 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.058 | 0.031 | +0.028 | 0.047 | 0.000 | 0.652 | 2565 |

## Is the operating point a property of the assessor?

Spread of `level` and `thr` across that assessor's targets. Small spread =
one threshold serves every target; large = re-fit per deployment.

| dataset | assessor | targets | level mean | level range | thr mean | thr range |
|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 0.435 | 0.078–0.846 | 0.208 | 0.000–0.977 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 0.054 | 0.013–0.103 | 0.000 | 0.000–0.000 |
| alfworld | Phi-4-mini-instruct | 6 | 0.286 | 0.099–0.394 | 0.064 | 0.018–0.119 |
| alfworld | Qwen3.6-35B-A3B | 6 | 0.671 | 0.360–0.890 | 0.579 | 0.097–0.857 |
| alfworld | gemma-3-4b-it | 6 | 0.150 | 0.030–0.279 | 0.000 | 0.000–0.000 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 0.307 | 0.027–0.512 | 0.000 | 0.000–0.002 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 0.028 | 0.007–0.057 | 0.000 | 0.000–0.000 |
| hotpotqa | Phi-4-mini-instruct | 5 | 0.201 | 0.121–0.244 | 0.099 | 0.060–0.148 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 0.502 | 0.191–0.707 | 0.491 | 0.147–0.704 |
| hotpotqa | gemma-3-4b-it | 5 | 0.053 | 0.009–0.100 | 0.000 | 0.000–0.000 |
