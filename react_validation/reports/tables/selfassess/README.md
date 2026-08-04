# Self-assessment raw metric extraction

One CSV per (dataset x model): one row per step, one column per
metric x stage. Suffixes: _T thought, _A action, _R whole response,
_J joint/step-level. Blank where that metric does not exist for that stage.

`judge_correct_frac` is a LABEL (fraction of 3 judges voting correct),
carried for convenience; tau / loop_flag / obs_changed / in_admissible are
environment facts carried for stratification. Neither are metrics.

| dataset | model | steps | metric cols | file |
|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 4765 | 17 | `alfworld__Llama-3.3-70B-Instruct.csv` |
| alfworld | Mistral-7B-Instruct-v0.3 | 6482 | 17 | `alfworld__Mistral-7B-Instruct-v0.3.csv` |
| alfworld | Phi-4-mini-instruct | 6611 | 17 | `alfworld__Phi-4-mini-instruct.csv` |
| alfworld | Qwen3.6-35B-A3B | 3342 | 17 | `alfworld__Qwen3.6-35B-A3B.csv` |
| alfworld | deepseek-v4-flash | 3313 | 12 | `alfworld__deepseek-v4-flash.csv` |
| alfworld | gemma-3-4b-it | 6790 | 17 | `alfworld__gemma-3-4b-it.csv` |
| hotpotqa | Llama-3.3-70B-Instruct | 2530 | 16 | `hotpotqa__Llama-3.3-70B-Instruct.csv` |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 3224 | 16 | `hotpotqa__Mistral-7B-Instruct-v0.3.csv` |
| hotpotqa | Phi-4-mini-instruct | 2716 | 16 | `hotpotqa__Phi-4-mini-instruct.csv` |
| hotpotqa | Qwen3.6-35B-A3B | 2235 | 16 | `hotpotqa__Qwen3.6-35B-A3B.csv` |
| hotpotqa | gemma-3-4b-it | 2565 | 16 | `hotpotqa__gemma-3-4b-it.csv` |

## Coverage — steps carrying each metric

| metric | alfworld/Llama | alfworld/Mistral | alfworld/Phi | alfworld/Qwen3.6 | alfworld/deepseek | alfworld/gemma | hotpotqa/Llama | hotpotqa/Mistral | hotpotqa/Phi | hotpotqa/Qwen3.6 | hotpotqa/gemma |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MTE_A | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| MTE_T | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| MaxTE_A | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| MaxTE_T | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| PPL_A | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| PPL_T | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| SP_A | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| SP_T | 4765 | 6482 | 6611 | 3342 | 3313 | 6790 | 2530 | 3224 | 2716 | 2235 | 2565 |
| chat_ingen_J | 4765 | 6480 | 6611 | 2807 | 3303 | 2813 | 2529 | 3224 | 2713 | 2160 | 1102 |
| posthoc_num_A | 4764 | 6482 | 6577 | 3192 | 0 | 6790 | 2530 | 3224 | 2714 | 2191 | 2565 |
| posthoc_num_T | 4765 | 6482 | 6595 | 3339 | 0 | 6790 | 2530 | 3224 | 2713 | 2233 | 2565 |
| ptrue_A | 4765 | 6482 | 6604 | 3197 | 3304 | 6790 | 2530 | 3224 | 2716 | 2192 | 2565 |
| ptrue_R | 4765 | 6482 | 6604 | 3197 | 2322 | 6790 | 2530 | 3224 | 2716 | 2192 | 2565 |
| ptrue_T | 4765 | 6482 | 6611 | 3339 | 3313 | 6790 | 2530 | 3224 | 2716 | 2234 | 2565 |
| sep_verbalized_A | 4765 | 6482 | 6604 | 3197 | 0 | 6790 | 2530 | 3216 | 2716 | 2192 | 2565 |
| sep_verbalized_T | 4765 | 6482 | 6611 | 3339 | 0 | 6790 | 2530 | 3224 | 2716 | 2234 | 2565 |
| targeted_posthoc_T | 4765 | 6482 | 6611 | 3339 | 0 | 6790 | 0 | 0 | 0 | 0 | 0 |
