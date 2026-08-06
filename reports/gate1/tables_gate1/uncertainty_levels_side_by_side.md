# Gate-1 Phase 5 — uncertainty levels, ensemble vs environment label

Scope SPLIT-action. `gap` = mu_inc - mu_cor.

| dataset | target | assessor | ensemble gap | ensemble_on_env_support gap | env_restricted gap | env_full gap | n_inc(env) | n_cor(env) |
|---|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | 0.407 | 0.412 | 0.169 | 0.177 |  3937 | 555  |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | 0.068 | 0.067 | 0.015 | 0.014 |  3937 | 555  |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | 0.081 | 0.086 | 0.164 | 0.107 |  3937 | 555  |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | 0.439 | 0.442 | 0.308 | 0.260 |  3937 | 555  |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | -0.014 | -0.014 | 0.038 | 0.020 |  3937 | 555  |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | 0.579 | 0.581 | 0.426 | 0.410 |  6088 | 233  |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | 0.026 | 0.026 | 0.031 | 0.022 |  6088 | 233  |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | -0.005 | -0.005 | 0.147 | 0.096 |  6088 | 233  |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | 0.357 | 0.356 | 0.375 | 0.310 |  6088 | 233  |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | -0.028 | -0.030 | -0.005 | 0.008 |  6088 | 233  |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | 0.510 | 0.509 | 0.248 | 0.234 |  6172 | 273  |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | 0.021 | 0.020 | -0.016 | -0.008 |  6172 | 273  |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | -0.032 | -0.023 | 0.104 | 0.043 |  6172 | 273  |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | 0.294 | 0.297 | 0.225 | 0.173 |  6172 | 273  |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | -0.073 | -0.074 | -0.072 | -0.056 |  6172 | 273  |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | — | — | 0.108 | 0.105 |  2391 | 641  |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | 0.096 | 0.096 | 0.090 | 0.082 |  3415 | 566  |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | 0.121 | 0.120 | 0.048 | 0.046 |  3439 | 585  |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | 0.161 | 0.163 | 0.071 | 0.071 |  2398 | 712  |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | 0.030 | 0.030 | 0.014 | 0.012 |  2398 | 712  |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | 0.039 | 0.039 | 0.060 | 0.055 |  2398 | 712  |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | 0.208 | 0.207 | 0.198 | 0.186 |  2398 | 712  |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | 0.043 | 0.043 | 0.015 | 0.015 |  2398 | 712  |
| alfworld | deepseek-v4-flash | Llama-3.3-70B-Instruct | 0.236 | 0.241 | 0.098 | 0.090 |  2499 | 517  |
| alfworld | deepseek-v4-flash | Mistral-7B-Instruct-v0.3 | 0.010 | 0.009 | 0.001 | 0.003 |  2499 | 517  |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | 0.032 | 0.033 | 0.121 | 0.078 |  2499 | 517  |
| alfworld | deepseek-v4-flash | Qwen3.6-35B-A3B | 0.394 | 0.396 | 0.284 | 0.221 |  2499 | 517  |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | 0.195 | 0.198 | 0.190 | 0.148 |  2499 | 517  |
| alfworld | deepseek-v4-flash | gemma-3-4b-it | 0.006 | 0.002 | -0.002 | 0.001 |  2499 | 517  |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | 0.655 | 0.654 | 0.369 | 0.360 |  6545 | 185  |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | 0.034 | 0.035 | -0.067 | -0.052 |  6545 | 185  |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | 0.086 | 0.088 | 0.074 | 0.060 |  6545 | 185  |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | 0.415 | 0.414 | 0.319 | 0.286 |  6545 | 185  |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | -0.052 | -0.052 | -0.132 | -0.106 |  6545 | 185  |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | 0.169 | 0.187 | 0.079 | 0.085 |  981 | 182  |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | 0.019 | 0.008 | 0.001 | 0.003 |  981 | 182  |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | 0.199 | 0.157 | 0.252 | 0.140 |  981 | 182  |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | 0.421 | 0.363 | 0.419 | 0.281 |  981 | 182  |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | 0.066 | 0.040 | -0.068 | 0.037 |  981 | 182  |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | 0.589 | 0.547 | 0.624 | 0.447 |  2343 | 32  |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | 0.027 | 0.021 | 0.015 | 0.014 |  2343 | 32  |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | 0.059 | -0.009 | 0.218 | 0.096 |  2343 | 32  |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | 0.438 | 0.290 | 0.726 | 0.444 |  2343 | 32  |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | 0.028 | 0.005 | -0.164 | 0.026 |  2343 | 32  |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | 0.701 | 0.652 | 0.529 | 0.502 |  1855 | 30  |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | 0.074 | 0.073 | 0.010 | 0.042 |  1855 | 30  |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | 0.095 | 0.048 | 0.178 | 0.115 |  1855 | 30  |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | 0.581 | 0.418 | 0.584 | 0.485 |  1855 | 30  |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | 0.076 | 0.023 | -0.237 | 0.098 |  1855 | 30  |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | 0.292 | 0.259 | 0.256 | 0.228 |  1207 | 168  |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | 0.215 | 0.216 | 0.200 | 0.183 |  1129 | 180  |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | 0.106 | 0.121 | 0.039 | 0.030 |  895 | 219  |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | 0.018 | 0.015 | 0.008 | 0.002 |  895 | 219  |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | 0.067 | 0.049 | 0.172 | 0.103 |  895 | 219  |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | 0.333 | 0.277 | 0.290 | 0.246 |  895 | 219  |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | 0.001 | -0.002 | -0.017 | 0.003 |  895 | 219  |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | 0.698 | 0.685 | 0.498 | 0.501 |  1553 | 105  |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | 0.027 | 0.024 | 0.020 | 0.005 |  1553 | 105  |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | 0.095 | 0.045 | 0.207 | 0.115 |  1553 | 105  |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | 0.610 | 0.516 | 0.627 | 0.482 |  1553 | 105  |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | 0.016 | -0.028 | -0.055 | 0.028 |  1553 | 105  |
