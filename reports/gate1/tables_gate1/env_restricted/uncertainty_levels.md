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
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.280 | 0.111 | +0.169 | 0.259 | 0.000 | 0.668 | 4492 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.628 | 0.203 | +0.426 | 0.613 | 0.001 | 0.748 | 6321 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.762 | 0.514 | +0.248 | 0.752 | 0.000 | 0.631 | 6445 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.095 | 0.025 | +0.071 | 0.079 | 0.000 | 0.648 | 3110 |
| Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.111 | 0.013 | +0.098 | 0.094 | 0.000 | 0.673 | 3016 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.859 | 0.490 | +0.369 | 0.849 | 0.182 | 0.690 | 6730 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.068 | 0.054 | +0.015 | 0.066 | 0.000 | 0.662 | 4492 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.053 | 0.022 | +0.031 | 0.051 | 0.000 | 0.635 | 6321 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.102 | 0.118 | -0.016 | 0.103 | 0.000 | 0.608 | 6445 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.020 | 0.005 | +0.014 | 0.016 | 0.000 | 0.645 | 3110 |
| Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.014 | 0.013 | +0.001 | 0.013 | 0.000 | 0.674 | 3016 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.076 | 0.143 | -0.067 | 0.078 | 0.000 | 0.679 | 6730 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.413 | 0.250 | +0.163 | 0.393 | 0.047 | 0.689 | 4492 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.395 | 0.248 | +0.147 | 0.390 | 0.119 | 0.635 | 6321 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.354 | 0.249 | +0.104 | 0.349 | 0.060 | 0.606 | 6445 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.113 | 0.052 | +0.060 | 0.099 | 0.018 | 0.674 | 3110 |
| Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.203 | 0.082 | +0.121 | 0.182 | 0.029 | 0.715 | 3016 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.303 | 0.229 | +0.074 | 0.301 | 0.076 | 0.633 | 6730 |
| Qwen3.5-27B | Qwen3.5-27B | self | 0.161 | 0.053 | +0.108 | 0.138 | 0.012 | 0.728 | 3032 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.244 | 0.154 | +0.090 | 0.231 | 0.060 | 0.650 | 3981 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.136 | 0.087 | +0.048 | 0.129 | 0.012 | 0.672 | 4024 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.693 | 0.386 | +0.308 | 0.655 | 0.277 | 0.684 | 4492 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.820 | 0.445 | +0.375 | 0.806 | 0.731 | 0.763 | 6321 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.885 | 0.660 | +0.225 | 0.875 | 0.805 | 0.652 | 6445 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.407 | 0.209 | +0.198 | 0.362 | 0.097 | 0.681 | 3110 |
| Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.509 | 0.225 | +0.284 | 0.460 | 0.154 | 0.713 | 3016 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.900 | 0.581 | +0.319 | 0.891 | 0.777 | 0.729 | 6730 |
| deepseek-v4-flash | deepseek-v4-flash | self | 0.319 | 0.129 | +0.190 | 0.286 | 0.009 | 0.674 | 3016 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.185 | 0.147 | +0.038 | 0.180 | 0.000 | 0.614 | 4492 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.260 | 0.265 | -0.005 | 0.260 | 0.000 | 0.618 | 6321 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.276 | 0.348 | -0.072 | 0.279 | 0.000 | 0.591 | 6445 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.043 | 0.029 | +0.015 | 0.040 | 0.000 | 0.579 | 3110 |
| gemma-3-4b-it | deepseek-v4-flash | cross | 0.030 | 0.032 | -0.002 | 0.030 | 0.000 | 0.597 | 3016 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.109 | 0.241 | -0.132 | 0.113 | 0.000 | 0.672 | 6730 |

## hotpotqa

| assessor | target | arm | mu_inc | mu_cor | gap | level | thr | bal_acc | n |
|---|---|---|---|---|---|---|---|---|---|
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.116 | 0.038 | +0.079 | 0.104 | 0.000 | 0.738 | 1163 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.624 | 0.000 | +0.624 | 0.616 | 0.000 | 0.907 | 2375 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.671 | 0.141 | +0.529 | 0.662 | 0.011 | 0.791 | 1885 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.044 | 0.005 | +0.039 | 0.037 | 0.000 | 0.741 | 1114 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.629 | 0.131 | +0.498 | 0.597 | 0.000 | 0.798 | 1658 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.019 | 0.019 | +0.001 | 0.019 | 0.000 | 0.775 | 1163 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.036 | 0.021 | +0.015 | 0.036 | 0.000 | 0.848 | 2375 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.070 | 0.060 | +0.010 | 0.070 | 0.000 | 0.692 | 1885 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.008 | 0.000 | +0.008 | 0.006 | 0.000 | 0.816 | 1114 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.028 | 0.008 | +0.020 | 0.027 | 0.000 | 0.819 | 1658 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.320 | 0.068 | +0.252 | 0.280 | 0.037 | 0.776 | 1163 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.270 | 0.052 | +0.218 | 0.267 | 0.018 | 0.858 | 2375 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.248 | 0.070 | +0.178 | 0.245 | 0.076 | 0.710 | 1885 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.182 | 0.011 | +0.172 | 0.149 | 0.023 | 0.846 | 1114 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.241 | 0.034 | +0.207 | 0.228 | 0.029 | 0.835 | 1658 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.336 | 0.080 | +0.256 | 0.305 | 0.068 | 0.786 | 1375 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.222 | 0.022 | +0.200 | 0.195 | 0.026 | 0.790 | 1309 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.548 | 0.129 | +0.419 | 0.483 | 0.321 | 0.796 | 1163 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.829 | 0.103 | +0.725 | 0.819 | 0.437 | 0.937 | 2375 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.817 | 0.233 | +0.584 | 0.808 | 0.752 | 0.853 | 1885 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.337 | 0.047 | +0.290 | 0.280 | 0.095 | 0.805 | 1114 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.764 | 0.137 | +0.627 | 0.724 | 0.294 | 0.860 | 1658 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.085 | 0.152 | -0.068 | 0.095 | 0.000 | 0.500 | 1163 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.055 | 0.219 | -0.164 | 0.057 | 1.000 | 0.501 | 2375 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.131 | 0.367 | -0.237 | 0.134 | 1.000 | 0.514 | 1885 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.010 | 0.027 | -0.017 | 0.014 | 1.000 | 0.502 | 1114 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.058 | 0.114 | -0.055 | 0.062 | 1.000 | 0.503 | 1658 |

## Is the operating point a property of the assessor?

Spread of `level` and `thr` across that assessor's targets. Small spread =
one threshold serves every target; large = re-fit per deployment.

| dataset | assessor | targets | level mean | level range | thr mean | thr range |
|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 0.441 | 0.079–0.849 | 0.031 | 0.000–0.182 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 0.055 | 0.013–0.103 | 0.000 | 0.000–0.000 |
| alfworld | Phi-4-mini-instruct | 6 | 0.286 | 0.099–0.393 | 0.058 | 0.018–0.119 |
| alfworld | Qwen3.6-35B-A3B | 6 | 0.675 | 0.362–0.891 | 0.474 | 0.097–0.805 |
| alfworld | gemma-3-4b-it | 6 | 0.150 | 0.030–0.279 | 0.000 | 0.000–0.000 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 0.403 | 0.037–0.662 | 0.002 | 0.000–0.011 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 0.032 | 0.006–0.070 | 0.000 | 0.000–0.000 |
| hotpotqa | Phi-4-mini-instruct | 5 | 0.234 | 0.149–0.280 | 0.037 | 0.018–0.076 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 0.623 | 0.280–0.819 | 0.380 | 0.095–0.752 |
| hotpotqa | gemma-3-4b-it | 5 | 0.072 | 0.014–0.134 | 0.800 | 0.000–1.000 |
