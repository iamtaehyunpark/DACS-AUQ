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
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.448 | 0.041 | +0.407 | 0.249 | 0.000 | 0.824 | 4765 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.745 | 0.167 | +0.579 | 0.603 | 0.001 | 0.810 | 6482 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.858 | 0.348 | +0.510 | 0.747 | 0.963 | 0.759 | 6604 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.177 | 0.016 | +0.161 | 0.078 | 0.000 | 0.753 | 3197 |
| Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.247 | 0.011 | +0.236 | 0.089 | 0.000 | 0.786 | 3304 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.920 | 0.265 | +0.655 | 0.846 | 0.971 | 0.834 | 6790 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.099 | 0.031 | +0.068 | 0.066 | 0.000 | 0.673 | 4765 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.058 | 0.031 | +0.026 | 0.051 | 0.000 | 0.580 | 6482 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.107 | 0.087 | +0.021 | 0.103 | 0.000 | 0.583 | 6604 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.035 | 0.005 | +0.030 | 0.017 | 0.000 | 0.588 | 3197 |
| Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.019 | 0.010 | +0.010 | 0.013 | 0.000 | 0.596 | 3304 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.082 | 0.047 | +0.034 | 0.078 | 0.000 | 0.675 | 6790 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.434 | 0.353 | +0.081 | 0.394 | 0.321 | 0.564 | 4765 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.388 | 0.394 | -0.005 | 0.389 | 0.023 | 0.516 | 6482 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.344 | 0.376 | -0.032 | 0.351 | 0.009 | 0.514 | 6604 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.123 | 0.084 | +0.039 | 0.099 | 0.023 | 0.555 | 3197 |
| Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.206 | 0.173 | +0.032 | 0.184 | 0.007 | 0.543 | 3304 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.311 | 0.225 | +0.086 | 0.301 | 0.095 | 0.601 | 6790 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.275 | 0.179 | +0.096 | 0.230 | 0.164 | 0.618 | 4113 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.192 | 0.071 | +0.121 | 0.127 | 0.047 | 0.669 | 4265 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.863 | 0.424 | +0.439 | 0.648 | 0.746 | 0.836 | 4765 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.889 | 0.532 | +0.357 | 0.801 | 0.789 | 0.797 | 6482 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.938 | 0.644 | +0.294 | 0.874 | 0.917 | 0.753 | 6604 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.489 | 0.281 | +0.208 | 0.360 | 0.407 | 0.650 | 3197 |
| Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.718 | 0.325 | +0.394 | 0.455 | 0.611 | 0.790 | 3304 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.937 | 0.522 | +0.415 | 0.890 | 0.873 | 0.842 | 6790 |
| deepseek-v4-flash | deepseek-v4-flash | self | 0.413 | 0.218 | +0.195 | 0.283 | 0.037 | 0.678 | 3304 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.174 | 0.188 | -0.014 | 0.181 | 0.000 | 0.553 | 4765 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.253 | 0.281 | -0.028 | 0.260 | 0.000 | 0.573 | 6482 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.263 | 0.337 | -0.074 | 0.279 | 0.000 | 0.575 | 6604 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.066 | 0.023 | +0.043 | 0.040 | 0.000 | 0.604 | 3197 |
| gemma-3-4b-it | deepseek-v4-flash | cross | 0.033 | 0.028 | +0.006 | 0.030 | 0.000 | 0.544 | 3304 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.107 | 0.159 | -0.052 | 0.113 | 0.000 | 0.669 | 6790 |

## hotpotqa

| assessor | target | arm | mu_inc | mu_cor | gap | level | thr | bal_acc | n |
|---|---|---|---|---|---|---|---|---|---|
| Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.198 | 0.029 | +0.169 | 0.064 | 0.000 | 0.771 | 2530 |
| Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.772 | 0.183 | +0.588 | 0.502 | 0.622 | 0.798 | 3224 |
| Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.822 | 0.121 | +0.701 | 0.512 | 0.001 | 0.855 | 2716 |
| Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.117 | 0.010 | +0.106 | 0.027 | 0.000 | 0.763 | 2192 |
| Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.800 | 0.102 | +0.698 | 0.431 | 0.000 | 0.867 | 2565 |
| Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.033 | 0.014 | +0.019 | 0.018 | 0.000 | 0.685 | 2530 |
| Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.045 | 0.018 | +0.027 | 0.033 | 0.000 | 0.680 | 3224 |
| Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.089 | 0.015 | +0.074 | 0.057 | 0.000 | 0.680 | 2716 |
| Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.022 | 0.004 | +0.018 | 0.007 | 0.000 | 0.736 | 2192 |
| Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.040 | 0.013 | +0.027 | 0.026 | 0.000 | 0.688 | 2565 |
| Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.391 | 0.192 | +0.199 | 0.234 | 0.076 | 0.681 | 2530 |
| Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.271 | 0.212 | +0.059 | 0.244 | 0.076 | 0.572 | 3224 |
| Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.254 | 0.159 | +0.095 | 0.212 | 0.076 | 0.598 | 2716 |
| Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.178 | 0.111 | +0.067 | 0.121 | 0.037 | 0.649 | 2192 |
| Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.246 | 0.150 | +0.095 | 0.195 | 0.095 | 0.615 | 2565 |
| Qwen3.5-4B | Qwen3.5-4B | self | 0.446 | 0.153 | +0.292 | 0.224 | 0.164 | 0.762 | 2371 |
| Qwen3.5-9B | Qwen3.5-9B | self | 0.301 | 0.086 | +0.216 | 0.129 | 0.026 | 0.762 | 2286 |
| Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.709 | 0.288 | +0.421 | 0.376 | 0.269 | 0.766 | 2530 |
| Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.908 | 0.470 | +0.438 | 0.707 | 0.813 | 0.792 | 3224 |
| Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.921 | 0.340 | +0.581 | 0.663 | 0.785 | 0.863 | 2716 |
| Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.473 | 0.140 | +0.333 | 0.191 | 0.202 | 0.786 | 2192 |
| Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.896 | 0.286 | +0.610 | 0.574 | 0.700 | 0.866 | 2565 |
| gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.114 | 0.048 | +0.066 | 0.062 | 0.000 | 0.659 | 2530 |
| gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.061 | 0.033 | +0.028 | 0.048 | 0.000 | 0.664 | 3224 |
| gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.133 | 0.057 | +0.076 | 0.100 | 0.000 | 0.690 | 2716 |
| gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.010 | 0.009 | +0.001 | 0.009 | 0.000 | 0.649 | 2192 |
| gemma-3-4b-it | gemma-3-4b-it | self | 0.056 | 0.040 | +0.016 | 0.047 | 0.000 | 0.679 | 2565 |

## Is the operating point a property of the assessor?

Spread of `level` and `thr` across that assessor's targets. Small spread =
one threshold serves every target; large = re-fit per deployment.

| dataset | assessor | targets | level mean | level range | thr mean | thr range |
|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 0.435 | 0.078–0.846 | 0.322 | 0.000–0.971 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 0.054 | 0.013–0.103 | 0.000 | 0.000–0.000 |
| alfworld | Phi-4-mini-instruct | 6 | 0.286 | 0.099–0.394 | 0.080 | 0.007–0.321 |
| alfworld | Qwen3.6-35B-A3B | 6 | 0.671 | 0.360–0.890 | 0.724 | 0.407–0.917 |
| alfworld | gemma-3-4b-it | 6 | 0.150 | 0.030–0.279 | 0.000 | 0.000–0.000 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 0.307 | 0.027–0.512 | 0.125 | 0.000–0.622 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 0.028 | 0.007–0.057 | 0.000 | 0.000–0.000 |
| hotpotqa | Phi-4-mini-instruct | 5 | 0.201 | 0.121–0.244 | 0.072 | 0.037–0.095 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 0.502 | 0.191–0.707 | 0.554 | 0.202–0.813 |
| hotpotqa | gemma-3-4b-it | 5 | 0.053 | 0.009–0.100 | 0.000 | 0.000–0.000 |
