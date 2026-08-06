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
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.75 | 1.12–2.80 | 0.09 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.35 | 1.02–1.86 | 0.07 |
| alfworld | Phi-4-mini-instruct | 6 | 1.18 | 0.97–1.51 | 0.06 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.72 | 1.12–2.80 | 0.09 |
| alfworld | gemma-3-4b-it | 6 | 1.01 | 0.83–1.61 | 0.05 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 2.02 | 1.38–3.28 | 0.10 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.47 | 1.10–2.36 | 0.07 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.11 | 0.97–1.30 | 0.06 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 2.00 | 1.38–3.28 | 0.10 |
| hotpotqa | gemma-3-4b-it | 5 | 0.97 | 0.76–1.14 | 0.05 |

## Consistency of lift@10% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.71 | 1.12–2.65 | 0.17 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.33 | 1.04–1.68 | 0.13 |
| alfworld | Phi-4-mini-instruct | 6 | 1.12 | 0.98–1.36 | 0.11 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.67 | 1.12–2.67 | 0.17 |
| alfworld | gemma-3-4b-it | 6 | 1.03 | 0.83–1.48 | 0.10 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.87 | 1.38–2.77 | 0.19 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.48 | 1.17–2.19 | 0.15 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.17 | 0.98–1.52 | 0.12 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.82 | 1.38–2.54 | 0.18 |
| hotpotqa | gemma-3-4b-it | 5 | 0.99 | 0.69–1.28 | 0.10 |

## Consistency of lift@20% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.65 | 1.11–2.41 | 0.33 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.27 | 1.05–1.52 | 0.25 |
| alfworld | Phi-4-mini-instruct | 6 | 1.10 | 0.97–1.27 | 0.22 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.59 | 1.12–2.44 | 0.32 |
| alfworld | gemma-3-4b-it | 6 | 1.08 | 0.90–1.44 | 0.21 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.77 | 1.39–2.32 | 0.36 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.42 | 1.20–2.01 | 0.28 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.15 | 0.97–1.42 | 0.23 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.70 | 1.37–2.20 | 0.34 |
| hotpotqa | gemma-3-4b-it | 5 | 1.02 | 0.90–1.10 | 0.20 |

## Consistency of lift@30% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.58 | 1.11–2.20 | 0.47 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.23 | 1.06–1.43 | 0.37 |
| alfworld | Phi-4-mini-instruct | 6 | 1.07 | 0.98–1.18 | 0.32 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.51 | 1.12–2.17 | 0.45 |
| alfworld | gemma-3-4b-it | 6 | 1.08 | 0.95–1.36 | 0.32 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 1.69 | 1.38–2.10 | 0.51 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.38 | 1.20–1.90 | 0.41 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.17 | 0.99–1.46 | 0.35 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 1.60 | 1.34–1.92 | 0.48 |
| hotpotqa | gemma-3-4b-it | 5 | 1.04 | 0.98–1.10 | 0.31 |

## Per-cell detail (k=10%)

| dataset | assessor | target | arm | base | prec | lift | recall |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.531 | 0.940 | 1.77 | 0.177 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.767 | 0.975 | 1.27 | 0.130 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.789 | 0.953 | 1.21 | 0.121 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.386 | 0.865 | 2.24 | 0.224 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.348 | 0.924 | 2.65 | 0.266 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.889 | 0.993 | 1.12 | 0.117 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.531 | 0.795 | 1.50 | 0.150 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.767 | 0.869 | 1.13 | 0.113 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.789 | 0.818 | 1.04 | 0.104 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.386 | 0.650 | 1.68 | 0.168 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.348 | 0.543 | 1.56 | 0.156 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.889 | 0.939 | 1.06 | 0.106 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.531 | 0.584 | 1.10 | 0.110 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.767 | 0.780 | 1.02 | 0.102 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.789 | 0.776 | 0.98 | 0.098 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.386 | 0.524 | 1.36 | 0.136 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.348 | 0.434 | 1.25 | 0.125 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.889 | 0.918 | 1.03 | 0.103 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 0.542 | 0.678 | 1.25 | 0.125 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 0.474 | 0.816 | 1.72 | 0.172 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.531 | 0.969 | 1.82 | 0.182 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.767 | 0.976 | 1.27 | 0.127 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.789 | 0.958 | 1.21 | 0.121 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.386 | 0.749 | 1.94 | 0.194 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.348 | 0.930 | 2.67 | 0.268 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.889 | 1.000 | 1.12 | 0.112 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 0.348 | 0.513 | 1.47 | 0.148 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.531 | 0.494 | 0.93 | 0.093 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.767 | 0.682 | 0.89 | 0.089 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.789 | 0.654 | 0.83 | 0.083 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.386 | 0.572 | 1.48 | 0.148 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 0.348 | 0.377 | 1.08 | 0.109 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 0.889 | 0.832 | 0.94 | 0.094 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.317 | 0.698 | 2.20 | 0.220 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.670 | 0.983 | 1.47 | 0.148 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.716 | 0.989 | 1.38 | 0.139 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.234 | 0.649 | 2.77 | 0.276 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.647 | 0.994 | 1.54 | 0.156 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.317 | 0.457 | 1.44 | 0.144 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.670 | 0.786 | 1.17 | 0.117 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.716 | 0.910 | 1.27 | 0.127 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.234 | 0.514 | 2.19 | 0.218 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.647 | 0.867 | 1.34 | 0.134 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.317 | 0.483 | 1.52 | 0.152 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.670 | 0.660 | 0.98 | 0.099 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.716 | 0.782 | 1.09 | 0.109 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.234 | 0.288 | 1.23 | 0.123 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.647 | 0.651 | 1.01 | 0.101 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 0.334 | 0.688 | 2.06 | 0.207 |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | self | 0.277 | 0.606 | 2.19 | 0.219 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.317 | 0.716 | 2.26 | 0.225 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.670 | 0.937 | 1.40 | 0.140 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.716 | 0.984 | 1.38 | 0.137 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.234 | 0.595 | 2.54 | 0.253 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.647 | 0.982 | 1.52 | 0.152 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.317 | 0.405 | 1.28 | 0.127 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.670 | 0.706 | 1.05 | 0.106 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.716 | 0.755 | 1.06 | 0.105 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.234 | 0.162 | 0.69 | 0.069 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 0.647 | 0.578 | 0.89 | 0.090 |

## Where does the INCORRECT pool sit, in percentile rank?

U is rank-transformed within each cell (0 = lowest U here, 100 = highest),
so this is comparable across targets where raw U is not. `inc med` is the
median percentile of incorrect steps; `cut` is the separating cut expressed
as 'flag the top X%'. Stability of these across an assessor's targets is
what would make a percentile policy characterisable once.

| dataset | assessor | targets | inc med mean | inc med range | cor med mean | cut mean | cut range |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 66.7 | 54.9–79.2 | 21.7 | 60.2 | 37.0–81.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 57.6 | 52.9–64.4 | 36.0 | 60.0 | 29.0–85.0 |
| alfworld | Phi-4-mini-instruct | 6 | 52.8 | 49.4–55.8 | 45.6 | 72.8 | 48.0–90.0 |
| alfworld | Qwen3.6-35B-A3B | 6 | 65.2 | 55.3–79.5 | 23.2 | 56.2 | 38.0–74.0 |
| alfworld | gemma-3-4b-it | 6 | 54.4 | 50.6–61.7 | 40.5 | 67.2 | 43.0–85.0 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 70.0 | 63.9–77.6 | 26.8 | 53.4 | 35.0–66.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 62.6 | 57.3–74.7 | 33.2 | 65.0 | 55.0–74.0 |
| hotpotqa | Phi-4-mini-instruct | 5 | 57.1 | 50.6–65.5 | 43.6 | 72.8 | 47.0–92.0 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 68.4 | 62.0–76.6 | 26.7 | 60.0 | 45.0–69.0 |
| hotpotqa | gemma-3-4b-it | 5 | 53.9 | 52.9–55.2 | 41.8 | 74.8 | 65.0–85.0 |

### Per-cell

| dataset | assessor | target | arm | inc med | inc q25-q75 | cor med | cut |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 71.2 | 54.6-85.8 | 25.7 | 54.0 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 59.9 | 38.6-80.2 | 14.0 | 73.0 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 58.4 | 35.4-79.4 | 14.8 | 71.0 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 76.4 | 55.9-88.9 | 34.2 | 45.0 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 79.2 | 62.6-90.6 | 34.9 | 37.0 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 54.9 | 31.8-77.6 | 6.7 | 81.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 64.4 | 41.2-82.9 | 33.7 | 51.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 53.7 | 28.0-77.5 | 38.2 | 55.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 53.1 | 28.6-76.4 | 37.2 | 67.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 59.6 | 35.0-84.5 | 43.5 | 29.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 61.8 | 37.4-83.5 | 43.5 | 73.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 52.9 | 28.6-76.6 | 19.6 | 85.0 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 55.8 | 29.7-78.0 | 43.8 | 48.0 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 49.8 | 25.5-74.8 | 50.5 | 87.0 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 49.4 | 25.3-74.5 | 53.2 | 86.0 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 55.4 | 31.3-80.4 | 46.5 | 60.0 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 54.4 | 29.2-77.8 | 47.7 | 90.0 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 51.9 | 27.1-76.0 | 32.2 | 66.0 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 60.4 | 35.4-80.8 | 37.8 | 68.0 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 66.1 | 40.7-84.7 | 36.6 | 47.0 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 71.9 | 55.8-86.2 | 26.3 | 48.0 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 59.9 | 38.2-80.3 | 15.1 | 69.0 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 58.1 | 35.4-79.4 | 14.6 | 69.0 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 66.6 | 40.6-86.0 | 40.0 | 39.0 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 79.5 | 62.7-90.7 | 35.9 | 38.0 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 55.3 | 32.4-77.7 | 7.1 | 74.0 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 66.1 | 47.9-82.7 | 37.2 | 62.0 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 54.1 | 30.0-75.0 | 44.3 | 58.0 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 50.9 | 27.9-74.2 | 44.7 | 85.0 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 50.6 | 27.8-73.4 | 44.6 | 85.0 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 61.7 | 36.7-83.2 | 41.9 | 53.0 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 56.8 | 30.8-78.4 | 47.1 | 43.0 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 52.1 | 28.4-75.2 | 20.1 | 79.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 76.3 | 57.5-88.6 | 36.3 | 43.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 65.0 | 43.4-83.0 | 21.7 | 58.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 63.9 | 43.5-82.0 | 16.1 | 65.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 77.6 | 59.4-91.2 | 40.8 | 35.0 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 67.0 | 48.6-83.9 | 19.0 | 66.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 63.1 | 44.3-81.7 | 40.8 | 70.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 58.0 | 34.8-79.2 | 30.2 | 66.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 57.3 | 33.4-79.5 | 29.7 | 60.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 74.7 | 55.8-88.6 | 40.8 | 55.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 59.8 | 37.9-81.2 | 24.5 | 74.0 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 65.5 | 44.9-83.1 | 41.1 | 47.0 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 50.6 | 25.1-74.5 | 48.7 | 92.0 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 52.6 | 27.8-76.2 | 43.4 | 77.0 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 62.1 | 46.3-79.4 | 43.8 | 65.0 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 54.6 | 29.9-76.8 | 40.6 | 83.0 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 72.8 | 52.4-87.7 | 36.3 | 58.0 |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | self | 74.1 | 51.7-88.9 | 39.1 | 56.0 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 74.7 | 55.9-88.7 | 36.4 | 45.0 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 62.0 | 40.4-81.8 | 21.4 | 69.0 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 62.5 | 41.6-81.9 | 16.5 | 68.0 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 76.6 | 58.0-90.1 | 40.8 | 49.0 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 66.1 | 47.3-83.5 | 18.6 | 69.0 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 53.5 | 33.0-75.9 | 48.0 | 69.0 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 55.2 | 32.4-77.3 | 35.3 | 76.0 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 52.9 | 30.2-75.2 | 39.8 | 79.0 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 54.8 | 35.0-73.5 | 47.7 | 65.0 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 53.1 | 31.3-75.9 | 38.4 | 85.0 |
