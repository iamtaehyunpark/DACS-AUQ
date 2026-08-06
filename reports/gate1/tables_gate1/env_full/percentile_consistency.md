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
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.11 | 1.00–1.29 | 0.06 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.04 | 0.95–1.17 | 0.05 |
| alfworld | Phi-4-mini-instruct | 6 | 1.06 | 0.98–1.17 | 0.05 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.13 | 1.02–1.27 | 0.06 |
| alfworld | gemma-3-4b-it | 6 | 1.01 | 0.93–1.09 | 0.05 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.58 | 1.35–1.78 | 0.08 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.30 | 1.12–1.65 | 0.06 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.36 | 1.14–1.69 | 0.07 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.58 | 1.24–2.05 | 0.08 |
| hotpotqa | gemma-3-4b-it | 5 | 1.24 | 1.11–1.36 | 0.06 |

## Consistency of lift@10% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.11 | 1.01–1.25 | 0.11 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.05 | 0.98–1.16 | 0.10 |
| alfworld | Phi-4-mini-instruct | 6 | 1.05 | 0.99–1.16 | 0.10 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.11 | 1.02–1.24 | 0.11 |
| alfworld | gemma-3-4b-it | 6 | 1.01 | 0.96–1.07 | 0.10 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.61 | 1.33–1.86 | 0.16 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.31 | 1.15–1.63 | 0.13 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.36 | 1.11–1.74 | 0.14 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.58 | 1.25–1.98 | 0.16 |
| hotpotqa | gemma-3-4b-it | 5 | 1.23 | 1.13–1.33 | 0.12 |

## Consistency of lift@20% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.10 | 1.02–1.21 | 0.22 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.05 | 1.00–1.12 | 0.21 |
| alfworld | Phi-4-mini-instruct | 6 | 1.06 | 1.00–1.18 | 0.21 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.10 | 1.02–1.21 | 0.22 |
| alfworld | gemma-3-4b-it | 6 | 1.02 | 0.97–1.07 | 0.20 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.56 | 1.32–1.78 | 0.31 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.28 | 1.13–1.52 | 0.26 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.34 | 1.13–1.61 | 0.27 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.56 | 1.26–1.97 | 0.31 |
| hotpotqa | gemma-3-4b-it | 5 | 1.22 | 1.12–1.30 | 0.24 |

## Consistency of lift@30% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.09 | 1.02–1.16 | 0.33 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.05 | 1.01–1.10 | 0.31 |
| alfworld | Phi-4-mini-instruct | 6 | 1.06 | 1.01–1.17 | 0.32 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.09 | 1.02–1.18 | 0.33 |
| alfworld | gemma-3-4b-it | 6 | 1.03 | 0.99–1.08 | 0.31 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.51 | 1.29–1.72 | 0.45 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.28 | 1.13–1.51 | 0.39 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.32 | 1.13–1.53 | 0.40 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.51 | 1.24–1.87 | 0.45 |
| hotpotqa | gemma-3-4b-it | 5 | 1.22 | 1.12–1.26 | 0.37 |

## Per-cell detail (k=10%)

| dataset | assessor | target | arm | base | prec | lift | recall |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.826 | 0.918 | 1.11 | 0.111 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.939 | 0.983 | 1.05 | 0.105 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.935 | 0.950 | 1.02 | 0.105 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.750 | 0.925 | 1.23 | 0.123 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.756 | 0.942 | 1.25 | 0.124 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.964 | 0.974 | 1.01 | 0.105 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.826 | 0.874 | 1.06 | 0.106 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.939 | 0.963 | 1.03 | 0.102 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.935 | 0.929 | 0.99 | 0.099 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.750 | 0.869 | 1.16 | 0.116 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.756 | 0.818 | 1.08 | 0.108 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.964 | 0.944 | 0.98 | 0.098 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.826 | 0.842 | 1.02 | 0.102 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.939 | 0.954 | 1.02 | 0.102 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.935 | 0.932 | 1.00 | 0.100 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.750 | 0.869 | 1.16 | 0.116 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.756 | 0.842 | 1.11 | 0.111 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.964 | 0.954 | 0.99 | 0.099 |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | self | 0.738 | 0.923 | 1.25 | 0.125 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 0.830 | 0.883 | 1.06 | 0.106 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 0.806 | 0.869 | 1.08 | 0.108 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.826 | 0.935 | 1.13 | 0.113 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.939 | 0.980 | 1.04 | 0.104 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.935 | 0.955 | 1.02 | 0.102 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.750 | 0.897 | 1.20 | 0.120 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.756 | 0.939 | 1.24 | 0.124 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.964 | 0.991 | 1.03 | 0.103 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 0.756 | 0.891 | 1.18 | 0.118 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.826 | 0.845 | 1.02 | 0.102 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.939 | 0.940 | 1.00 | 0.100 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.935 | 0.897 | 0.96 | 0.096 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.750 | 0.800 | 1.07 | 0.107 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 0.756 | 0.797 | 1.05 | 0.105 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 0.964 | 0.923 | 0.96 | 0.096 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.388 | 0.719 | 1.86 | 0.186 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.727 | 0.969 | 1.33 | 0.134 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.683 | 0.978 | 1.43 | 0.144 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.408 | 0.740 | 1.81 | 0.181 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.605 | 0.977 | 1.61 | 0.161 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.388 | 0.494 | 1.27 | 0.127 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.727 | 0.839 | 1.15 | 0.115 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.683 | 0.842 | 1.23 | 0.123 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.408 | 0.667 | 1.63 | 0.163 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.605 | 0.750 | 1.24 | 0.124 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.388 | 0.530 | 1.37 | 0.137 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.727 | 0.804 | 1.11 | 0.111 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.683 | 0.857 | 1.25 | 0.126 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.408 | 0.712 | 1.74 | 0.174 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.605 | 0.797 | 1.32 | 0.131 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 0.509 | 0.857 | 1.68 | 0.168 |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | self | 0.492 | 0.909 | 1.85 | 0.185 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.388 | 0.692 | 1.78 | 0.178 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.727 | 0.907 | 1.25 | 0.125 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.683 | 0.915 | 1.34 | 0.134 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.408 | 0.808 | 1.98 | 0.198 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.605 | 0.938 | 1.55 | 0.155 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.388 | 0.514 | 1.33 | 0.133 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.727 | 0.820 | 1.13 | 0.113 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.683 | 0.897 | 1.31 | 0.132 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.408 | 0.484 | 1.19 | 0.118 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 0.605 | 0.738 | 1.22 | 0.122 |

## Where does the INCORRECT pool sit, in percentile rank?

U is rank-transformed within each cell (0 = lowest U here, 100 = highest),
so this is comparable across targets where raw U is not. `inc med` is the
median percentile of incorrect steps; `cut` is the separating cut expressed
as 'flag the top X%'. Stability of these across an assessor's targets is
what would make a percentile policy characterisable once.

| dataset | assessor | targets | inc med mean | inc med range | cor med mean | cut mean | cut range |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 53.4 | 50.9–56.0 | 25.3 | 67.5 | 44.0–81.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 52.0 | 50.2–54.7 | 35.9 | 73.7 | 62.0–91.0 |
| alfworld | Phi-4-mini-instruct | 6 | 52.6 | 50.5–56.7 | 33.3 | 70.2 | 64.0–81.0 |
| alfworld | Qwen3.6-35B-A3B | 6 | 53.6 | 51.1–56.2 | 22.2 | 71.3 | 52.0–83.0 |
| alfworld | gemma-3-4b-it | 6 | 51.5 | 50.1–53.7 | 40.2 | 67.7 | 45.0–88.0 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 66.1 | 60.6–71.0 | 27.2 | 53.0 | 41.0–64.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 60.2 | 55.8–66.3 | 35.7 | 59.4 | 37.0–71.0 |
| hotpotqa | Phi-4-mini-instruct | 5 | 60.8 | 55.4–66.2 | 37.7 | 45.4 | 40.0–55.0 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 66.0 | 59.5–73.8 | 26.5 | 54.2 | 40.0–66.0 |
| hotpotqa | gemma-3-4b-it | 5 | 59.4 | 55.8–60.7 | 35.1 | 59.0 | 50.0–67.0 |

### Per-cell

| dataset | assessor | target | arm | inc med | inc q25-q75 | cor med | cut |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 54.9 | 29.4-77.7 | 29.2 | 44.0 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 52.2 | 27.8-76.2 | 15.3 | 77.0 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 51.2 | 26.5-75.5 | 29.0 | 76.0 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 56.0 | 31.8-79.2 | 29.9 | 63.0 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 55.3 | 30.4-79.1 | 32.8 | 64.0 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 50.9 | 26.3-75.0 | 15.6 | 81.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 52.9 | 28.4-76.5 | 33.8 | 62.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 50.6 | 25.8-75.6 | 36.7 | 64.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 50.2 | 25.5-75.1 | 47.8 | 91.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 54.7 | 31.1-77.6 | 31.7 | 62.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 53.2 | 29.6-77.1 | 37.2 | 75.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 50.5 | 25.9-75.1 | 28.0 | 88.0 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 52.5 | 28.8-76.0 | 33.2 | 81.0 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 50.8 | 25.7-75.5 | 37.2 | 66.0 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 50.5 | 25.7-75.3 | 40.5 | 68.0 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 56.7 | 32.6-78.8 | 27.2 | 64.0 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 54.7 | 31.1-77.6 | 31.0 | 75.0 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 50.5 | 25.7-75.2 | 30.8 | 67.0 |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | self | 57.9 | 35.0-79.7 | 22.9 | 73.0 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 53.3 | 28.9-77.0 | 30.6 | 79.0 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 53.9 | 29.9-76.8 | 29.4 | 81.0 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 55.1 | 29.9-78.0 | 26.5 | 52.0 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 52.1 | 27.8-76.1 | 14.5 | 71.0 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 51.2 | 26.6-75.5 | 27.7 | 79.0 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 56.2 | 32.9-78.5 | 24.9 | 75.0 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 55.9 | 32.3-79.4 | 27.5 | 68.0 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 51.1 | 26.5-75.6 | 12.2 | 83.0 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 55.8 | 30.8-78.2 | 31.7 | 51.0 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 52.2 | 27.5-75.8 | 37.7 | 64.0 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 50.5 | 25.8-75.1 | 39.9 | 79.0 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 50.1 | 25.5-74.6 | 47.8 | 88.0 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 53.7 | 28.6-76.7 | 40.4 | 51.0 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 52.3 | 27.3-76.6 | 43.8 | 45.0 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 50.4 | 25.8-74.8 | 31.6 | 79.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 69.2 | 48.2-86.3 | 37.2 | 45.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 60.6 | 38.7-81.0 | 18.2 | 61.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 63.1 | 42.2-82.3 | 19.9 | 64.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 71.0 | 46.4-86.2 | 36.3 | 41.0 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 66.8 | 46.7-84.1 | 24.4 | 54.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 61.7 | 39.0-80.7 | 41.2 | 64.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 55.8 | 33.1-77.9 | 28.1 | 71.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 57.4 | 32.3-79.3 | 34.7 | 70.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 66.3 | 38.8-83.8 | 40.2 | 37.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 59.8 | 35.3-80.3 | 34.3 | 55.0 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 65.4 | 41.4-83.0 | 39.9 | 44.0 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 55.4 | 31.0-77.6 | 33.9 | 55.0 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 56.8 | 29.5-79.3 | 38.7 | 45.0 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 66.2 | 40.8-84.8 | 39.4 | 40.0 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 60.3 | 33.2-80.6 | 36.5 | 43.0 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 67.8 | 47.9-84.9 | 29.7 | 55.0 |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | self | 70.9 | 49.7-86.3 | 31.2 | 45.0 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 69.0 | 47.0-86.0 | 37.0 | 44.0 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 59.5 | 38.3-80.1 | 17.3 | 66.0 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 62.0 | 42.0-81.3 | 19.6 | 63.0 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 73.8 | 53.5-87.6 | 34.8 | 40.0 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 65.7 | 46.1-83.5 | 24.0 | 58.0 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 60.5 | 38.9-79.8 | 41.8 | 65.0 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 55.8 | 32.4-77.7 | 30.3 | 67.0 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 59.9 | 35.8-80.8 | 28.4 | 61.0 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 60.7 | 35.3-79.7 | 42.3 | 50.0 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 60.3 | 36.9-79.5 | 32.7 | 52.0 |
