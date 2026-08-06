# Percentile-rule consistency — scope SPLIT-action

An absolute threshold does not transfer across targets. This asks whether a
PERCENTILE rule does: is the top-k% by U enriched for incorrect steps by the
same factor everywhere?

`lift` = precision / base rate. Base-rate free, so it IS comparable across
targets; raw precision is not. lift 1.0 = ranking worthless.
Labels are the 3-judge ensemble — provisional until gate 1.

## Consistency of lift@5% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.08 | 0.99–1.20 | 0.06 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.04 | 0.95–1.20 | 0.05 |
| alfworld | Phi-4-mini-instruct | 6 | 1.05 | 0.98–1.14 | 0.05 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.10 | 1.01–1.22 | 0.05 |
| alfworld | gemma-3-4b-it | 6 | 1.01 | 0.94–1.07 | 0.05 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.09 | 1.01–1.20 | 0.05 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.07 | 0.99–1.24 | 0.05 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.10 | 1.01–1.24 | 0.06 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.10 | 1.01–1.24 | 0.06 |
| hotpotqa | gemma-3-4b-it | 5 | 0.89 | 0.67–0.98 | 0.04 |

## Consistency of lift@10% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.08 | 1.00–1.21 | 0.11 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.05 | 0.98–1.16 | 0.10 |
| alfworld | Phi-4-mini-instruct | 6 | 1.05 | 0.99–1.16 | 0.11 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.09 | 1.01–1.20 | 0.11 |
| alfworld | gemma-3-4b-it | 6 | 1.01 | 0.96–1.06 | 0.10 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.08 | 1.01–1.21 | 0.11 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.08 | 1.01–1.24 | 0.11 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.10 | 1.01–1.24 | 0.11 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.10 | 1.01–1.24 | 0.11 |
| hotpotqa | gemma-3-4b-it | 5 | 0.87 | 0.62–0.97 | 0.09 |

## Consistency of lift@20% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.07 | 1.01–1.19 | 0.22 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.05 | 1.00–1.14 | 0.21 |
| alfworld | Phi-4-mini-instruct | 6 | 1.06 | 1.00–1.18 | 0.21 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.08 | 1.01–1.16 | 0.22 |
| alfworld | gemma-3-4b-it | 6 | 1.02 | 0.98–1.08 | 0.20 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.09 | 1.01–1.21 | 0.22 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.09 | 1.00–1.23 | 0.22 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.10 | 1.01–1.24 | 0.22 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.10 | 1.01–1.24 | 0.22 |
| hotpotqa | gemma-3-4b-it | 5 | 0.88 | 0.68–0.98 | 0.18 |

## Consistency of lift@30% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.07 | 1.01–1.15 | 0.32 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.05 | 1.01–1.12 | 0.31 |
| alfworld | Phi-4-mini-instruct | 6 | 1.06 | 1.01–1.16 | 0.32 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.07 | 1.01–1.15 | 0.32 |
| alfworld | gemma-3-4b-it | 6 | 1.03 | 0.99–1.08 | 0.31 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.09 | 1.01–1.21 | 0.33 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.09 | 1.01–1.23 | 0.33 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.10 | 1.01–1.24 | 0.33 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.10 | 1.01–1.23 | 0.33 |
| hotpotqa | gemma-3-4b-it | 5 | 0.89 | 0.70–0.98 | 0.27 |

## Per-cell detail (k=10%)

| dataset | assessor | target | arm | base | prec | lift | recall |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.876 | 0.940 | 1.07 | 0.107 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.963 | 0.991 | 1.03 | 0.105 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.958 | 0.960 | 1.00 | 0.100 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.771 | 0.932 | 1.21 | 0.121 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.829 | 0.974 | 1.17 | 0.118 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.973 | 0.976 | 1.00 | 0.105 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.876 | 0.915 | 1.04 | 0.104 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.963 | 0.983 | 1.02 | 0.102 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.958 | 0.949 | 0.99 | 0.099 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.771 | 0.897 | 1.16 | 0.116 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.829 | 0.887 | 1.07 | 0.107 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.973 | 0.954 | 0.98 | 0.098 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.876 | 0.902 | 1.03 | 0.103 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.963 | 0.972 | 1.01 | 0.101 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.958 | 0.957 | 1.00 | 0.100 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.771 | 0.894 | 1.16 | 0.116 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.829 | 0.930 | 1.12 | 0.112 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.973 | 0.966 | 0.99 | 0.099 |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | self | 0.789 | 0.931 | 1.18 | 0.118 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 0.858 | 0.907 | 1.06 | 0.106 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 0.855 | 0.898 | 1.05 | 0.105 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.876 | 0.955 | 1.09 | 0.109 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.963 | 0.994 | 1.03 | 0.103 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.958 | 0.964 | 1.01 | 0.101 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.771 | 0.923 | 1.20 | 0.120 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.829 | 0.967 | 1.17 | 0.117 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.973 | 0.991 | 1.02 | 0.102 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 0.829 | 0.957 | 1.15 | 0.116 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.876 | 0.900 | 1.03 | 0.103 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.963 | 0.953 | 0.99 | 0.099 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.958 | 0.927 | 0.97 | 0.097 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.771 | 0.814 | 1.06 | 0.106 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 0.829 | 0.877 | 1.06 | 0.106 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 0.973 | 0.935 | 0.96 | 0.096 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.844 | 0.940 | 1.11 | 0.111 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.987 | 1.000 | 1.01 | 0.102 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.984 | 1.000 | 1.02 | 0.102 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.803 | 0.973 | 1.21 | 0.121 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.937 | 0.994 | 1.06 | 0.108 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.844 | 0.914 | 1.08 | 0.108 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.987 | 0.996 | 1.01 | 0.101 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.984 | 0.989 | 1.01 | 0.100 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.803 | 1.000 | 1.24 | 0.124 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.937 | 0.994 | 1.06 | 0.106 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.844 | 0.966 | 1.14 | 0.114 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.987 | 0.996 | 1.01 | 0.101 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.984 | 1.000 | 1.02 | 0.101 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.803 | 1.000 | 1.24 | 0.124 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.937 | 1.000 | 1.07 | 0.107 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 0.878 | 0.993 | 1.13 | 0.114 |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | self | 0.862 | 1.000 | 1.16 | 0.116 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.844 | 0.991 | 1.18 | 0.117 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.987 | 1.000 | 1.01 | 0.102 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.984 | 1.000 | 1.02 | 0.101 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.803 | 1.000 | 1.24 | 0.124 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.937 | 1.000 | 1.07 | 0.107 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.844 | 0.750 | 0.89 | 0.089 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.987 | 0.954 | 0.97 | 0.097 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.984 | 0.957 | 0.97 | 0.097 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.803 | 0.495 | 0.62 | 0.061 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 0.937 | 0.855 | 0.91 | 0.091 |

## Where does the INCORRECT pool sit, in percentile rank?

U is rank-transformed within each cell (0 = lowest U here, 100 = highest),
so this is comparable across targets where raw U is not. `inc med` is the
median percentile of incorrect steps; `cut` is the separating cut expressed
as 'flag the top X%'. Stability of these across an assessor's targets is
what would make a percentile policy characterisable once.

| dataset | assessor | targets | inc med mean | inc med range | cor med mean | cut mean | cut range |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 52.8 | 50.6–55.7 | 20.8 | 73.3 | 63.0–86.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 52.1 | 50.5–55.0 | 25.4 | 77.5 | 62.0–91.0 |
| alfworld | Phi-4-mini-instruct | 6 | 52.8 | 50.5–56.7 | 23.9 | 71.0 | 65.0–82.0 |
| alfworld | Qwen3.6-35B-A3B | 6 | 53.0 | 50.8–56.0 | 17.1 | 77.3 | 74.0–81.0 |
| alfworld | gemma-3-4b-it | 6 | 51.6 | 50.2–53.5 | 32.6 | 70.0 | 51.0–87.0 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 53.6 | 50.7–58.6 | 13.3 | 70.2 | 58.0–80.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 53.9 | 50.4–59.5 | 14.4 | 69.6 | 60.0–87.0 |
| hotpotqa | Phi-4-mini-instruct | 5 | 54.0 | 50.5–59.6 | 10.9 | 72.6 | 58.0–92.0 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 54.1 | 50.7–58.9 | 9.7 | 75.8 | 62.0–89.0 |
| hotpotqa | gemma-3-4b-it | 5 | 46.4 | 41.0–49.6 | 78.0 | 20.8 | 1.0–99.0 |

### Per-cell

| dataset | assessor | target | arm | inc med | inc q25-q75 | cor med | cut |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 53.4 | 29.0-76.8 | 22.1 | 68.0 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 51.3 | 26.8-75.7 | 11.2 | 74.0 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 50.7 | 26.0-75.3 | 27.1 | 83.0 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 55.7 | 31.7-78.9 | 27.7 | 63.0 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 54.8 | 30.7-78.0 | 23.0 | 66.0 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 50.6 | 26.0-74.9 | 13.6 | 86.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 52.6 | 28.8-76.2 | 21.8 | 77.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 50.6 | 25.9-75.5 | 25.9 | 72.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 50.5 | 25.7-75.1 | 34.9 | 91.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 55.0 | 31.4-77.8 | 28.2 | 62.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 53.4 | 30.6-76.8 | 22.8 | 74.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 50.5 | 25.9-75.1 | 18.6 | 89.0 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 52.6 | 29.1-76.0 | 17.3 | 82.0 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 50.7 | 25.9-75.4 | 25.9 | 67.0 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 50.7 | 25.8-75.4 | 31.4 | 67.0 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 56.7 | 32.6-78.8 | 25.2 | 65.0 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 55.4 | 31.9-77.9 | 17.9 | 73.0 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 50.5 | 25.7-75.2 | 25.5 | 72.0 |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | self | 57.1 | 34.2-78.9 | 16.0 | 74.0 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 53.0 | 28.8-76.7 | 26.1 | 79.0 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 53.2 | 29.6-76.4 | 21.5 | 85.0 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 53.8 | 29.2-77.2 | 18.4 | 80.0 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 51.4 | 26.9-75.8 | 11.6 | 74.0 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 50.8 | 26.2-75.2 | 22.6 | 81.0 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 56.0 | 32.7-78.4 | 23.1 | 75.0 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 55.3 | 32.0-78.3 | 16.9 | 76.0 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 50.9 | 26.2-75.5 | 10.3 | 78.0 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 55.0 | 30.8-77.8 | 22.2 | 73.0 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 52.1 | 27.7-75.8 | 30.7 | 64.0 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 50.4 | 25.8-75.0 | 32.9 | 80.0 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 50.2 | 25.6-74.7 | 38.3 | 87.0 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 53.5 | 28.4-76.6 | 38.8 | 52.0 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 53.0 | 28.1-76.9 | 35.6 | 51.0 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 50.4 | 25.8-74.9 | 19.1 | 86.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 55.6 | 32.2-78.1 | 21.8 | 63.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 50.7 | 26.0-75.4 | 4.4 | 80.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 50.7 | 25.8-75.5 | 8.2 | 73.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 58.6 | 34.1-79.4 | 21.4 | 58.0 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 52.5 | 28.7-76.4 | 10.7 | 77.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 56.0 | 33.6-77.8 | 17.0 | 66.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 50.6 | 25.8-75.3 | 6.3 | 87.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 50.4 | 25.5-75.1 | 19.0 | 61.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 59.5 | 37.3-79.8 | 18.5 | 60.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 52.9 | 28.8-76.5 | 11.2 | 74.0 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 56.7 | 33.3-78.4 | 14.5 | 73.0 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 50.5 | 25.8-75.3 | 2.9 | 92.0 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 50.6 | 25.5-75.3 | 13.0 | 58.0 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 59.6 | 38.2-80.0 | 16.4 | 66.0 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 52.8 | 29.0-76.3 | 7.7 | 74.0 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 54.9 | 31.7-77.9 | 13.9 | 71.0 |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | self | 56.3 | 32.0-78.4 | 17.7 | 63.0 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 56.8 | 34.0-78.8 | 16.4 | 70.0 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 50.7 | 25.9-75.4 | 2.4 | 89.0 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 50.7 | 26.1-75.4 | 6.2 | 76.0 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 58.9 | 36.7-79.9 | 16.4 | 62.0 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 53.2 | 29.3-76.6 | 7.2 | 82.0 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 43.5 | 21.2-69.5 | 74.4 | 1.0 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 49.6 | 24.7-74.5 | 84.3 | 99.0 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 49.4 | 24.6-74.5 | 84.3 | 2.0 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 41.0 | 20.3-65.7 | 78.8 | 1.0 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 48.5 | 23.8-73.6 | 68.1 | 1.0 |
