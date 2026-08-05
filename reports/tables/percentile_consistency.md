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
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.79 | 1.13–2.93 | 0.09 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.38 | 1.02–1.88 | 0.07 |
| alfworld | Phi-4-mini-instruct | 6 | 1.19 | 0.97–1.51 | 0.06 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.77 | 1.13–2.95 | 0.09 |
| alfworld | gemma-3-4b-it | 6 | 1.02 | 0.83–1.64 | 0.05 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 2.52 | 1.76–3.85 | 0.13 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.79 | 1.31–2.79 | 0.09 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.42 | 1.09–1.82 | 0.07 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 2.63 | 1.74–4.09 | 0.13 |
| hotpotqa | gemma-3-4b-it | 5 | 1.35 | 1.13–1.82 | 0.07 |

## Consistency of lift@10% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.74 | 1.12–2.75 | 0.18 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.34 | 1.04–1.69 | 0.13 |
| alfworld | Phi-4-mini-instruct | 6 | 1.12 | 0.98–1.36 | 0.11 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.72 | 1.13–2.80 | 0.17 |
| alfworld | gemma-3-4b-it | 6 | 1.03 | 0.82–1.48 | 0.10 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 2.46 | 1.77–3.52 | 0.25 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.80 | 1.38–2.65 | 0.18 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.43 | 1.12–1.98 | 0.14 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 2.40 | 1.70–3.40 | 0.24 |
| hotpotqa | gemma-3-4b-it | 5 | 1.38 | 1.25–1.70 | 0.14 |

## Consistency of lift@20% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.69 | 1.12–2.51 | 0.34 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.27 | 1.06–1.51 | 0.25 |
| alfworld | Phi-4-mini-instruct | 6 | 1.10 | 0.96–1.27 | 0.22 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.62 | 1.13–2.53 | 0.32 |
| alfworld | gemma-3-4b-it | 6 | 1.07 | 0.90–1.44 | 0.21 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 2.21 | 1.77–2.80 | 0.44 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.72 | 1.35–2.46 | 0.34 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.44 | 1.15–1.92 | 0.29 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 2.19 | 1.64–2.84 | 0.44 |
| hotpotqa | gemma-3-4b-it | 5 | 1.38 | 1.28–1.54 | 0.28 |

## Consistency of lift@30% across targets, per assessor

| dataset | assessor | targets | lift mean | lift range | recall mean |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 1.60 | 1.12–2.24 | 0.48 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 1.24 | 1.06–1.46 | 0.37 |
| alfworld | Phi-4-mini-instruct | 6 | 1.07 | 0.97–1.18 | 0.32 |
| alfworld | Qwen3.6-35B-A3B | 6 | 1.54 | 1.12–2.22 | 0.46 |
| alfworld | gemma-3-4b-it | 6 | 1.08 | 0.95–1.35 | 0.32 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 2.04 | 1.72–2.40 | 0.61 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 1.64 | 1.35–2.27 | 0.49 |
| hotpotqa | Phi-4-mini-instruct | 5 | 1.42 | 1.15–1.81 | 0.43 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 2.01 | 1.60–2.54 | 0.60 |
| hotpotqa | gemma-3-4b-it | 5 | 1.41 | 1.27–1.61 | 0.42 |

## Per-cell detail (k=10%)

| dataset | assessor | target | arm | base | prec | lift | recall |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.511 | 0.931 | 1.82 | 0.182 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.755 | 0.974 | 1.29 | 0.130 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.782 | 0.955 | 1.22 | 0.126 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.382 | 0.859 | 2.25 | 0.225 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 0.331 | 0.909 | 2.75 | 0.274 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.886 | 0.993 | 1.12 | 0.116 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.511 | 0.784 | 1.53 | 0.153 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.755 | 0.858 | 1.14 | 0.114 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.782 | 0.814 | 1.04 | 0.104 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.382 | 0.644 | 1.69 | 0.169 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 0.331 | 0.524 | 1.58 | 0.158 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.886 | 0.935 | 1.06 | 0.106 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.511 | 0.563 | 1.10 | 0.110 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.755 | 0.767 | 1.02 | 0.102 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.782 | 0.762 | 0.98 | 0.097 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.382 | 0.519 | 1.36 | 0.136 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 0.331 | 0.412 | 1.25 | 0.124 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.886 | 0.913 | 1.03 | 0.103 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 0.530 | 0.672 | 1.27 | 0.127 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 0.460 | 0.808 | 1.75 | 0.175 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.511 | 0.971 | 1.90 | 0.190 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.755 | 0.977 | 1.29 | 0.129 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.782 | 0.959 | 1.23 | 0.123 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.382 | 0.747 | 1.96 | 0.196 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 0.331 | 0.927 | 2.80 | 0.280 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.886 | 1.000 | 1.13 | 0.113 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 0.331 | 0.494 | 1.49 | 0.149 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.511 | 0.479 | 0.94 | 0.094 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.755 | 0.677 | 0.90 | 0.090 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.782 | 0.641 | 0.82 | 0.082 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.382 | 0.566 | 1.48 | 0.148 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 0.331 | 0.364 | 1.10 | 0.110 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 0.886 | 0.828 | 0.93 | 0.093 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 0.209 | 0.652 | 3.12 | 0.312 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 0.542 | 0.966 | 1.78 | 0.179 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 0.557 | 0.985 | 1.77 | 0.178 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 0.153 | 0.539 | 3.52 | 0.351 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 0.472 | 0.992 | 2.10 | 0.210 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 0.209 | 0.379 | 1.81 | 0.181 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 0.542 | 0.745 | 1.38 | 0.137 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 0.557 | 0.846 | 1.52 | 0.152 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 0.153 | 0.406 | 2.65 | 0.265 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 0.472 | 0.766 | 1.62 | 0.162 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 0.209 | 0.415 | 1.98 | 0.198 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 0.542 | 0.609 | 1.12 | 0.112 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 0.557 | 0.724 | 1.30 | 0.130 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 0.153 | 0.228 | 1.49 | 0.149 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 0.472 | 0.602 | 1.28 | 0.127 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 0.243 | 0.629 | 2.58 | 0.258 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 0.209 | 0.636 | 3.04 | 0.304 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 0.542 | 0.922 | 1.70 | 0.170 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 0.557 | 0.985 | 1.77 | 0.177 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 0.153 | 0.521 | 3.40 | 0.339 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 0.472 | 0.980 | 2.08 | 0.207 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 0.209 | 0.356 | 1.70 | 0.170 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 0.542 | 0.680 | 1.26 | 0.125 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 0.557 | 0.746 | 1.34 | 0.134 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 0.153 | 0.205 | 1.34 | 0.134 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 0.472 | 0.590 | 1.25 | 0.125 |

## Where does the INCORRECT pool sit, in percentile rank?

U is rank-transformed within each cell (0 = lowest U here, 100 = highest),
so this is comparable across targets where raw U is not. `inc med` is the
median percentile of incorrect steps; `cut` is the separating cut expressed
as 'flag the top X%'. Stability of these across an assessor's targets is
what would make a percentile policy characterisable once.

| dataset | assessor | targets | inc med mean | inc med range | cor med mean | cut mean | cut range |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | 67.1 | 55.0–80.1 | 22.2 | 58.8 | 36.0–81.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6 | 57.6 | 52.9–64.9 | 36.6 | 60.2 | 29.0–85.0 |
| alfworld | Phi-4-mini-instruct | 6 | 52.6 | 49.2–55.7 | 46.0 | 72.0 | 48.0–90.0 |
| alfworld | Qwen3.6-35B-A3B | 6 | 65.8 | 55.5–80.4 | 23.6 | 55.3 | 37.0–74.0 |
| alfworld | gemma-3-4b-it | 6 | 54.0 | 50.6–61.5 | 41.1 | 65.3 | 38.0–85.0 |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | 76.6 | 71.1–83.1 | 31.7 | 47.4 | 38.0–60.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 5 | 68.3 | 62.6–79.9 | 36.0 | 59.6 | 40.0–69.0 |
| hotpotqa | Phi-4-mini-instruct | 5 | 63.5 | 56.1–72.7 | 42.3 | 49.4 | 43.0–54.0 |
| hotpotqa | Qwen3.6-35B-A3B | 5 | 75.9 | 68.5–83.8 | 31.4 | 49.4 | 34.0–60.0 |
| hotpotqa | gemma-3-4b-it | 5 | 64.4 | 60.8–69.5 | 37.1 | 60.6 | 45.0–69.0 |

### Per-cell

| dataset | assessor | target | arm | inc med | inc q25-q75 | cor med | cut |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 72.1 | 55.8-86.2 | 26.8 | 50.0 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 60.5 | 39.2-80.5 | 14.7 | 72.0 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 58.7 | 35.8-79.6 | 15.0 | 70.0 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 76.5 | 56.1-89.0 | 34.4 | 44.0 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | cross | 80.1 | 62.6-90.9 | 35.7 | 36.0 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 55.0 | 32.0-77.8 | 6.9 | 81.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 64.9 | 41.4-83.3 | 34.6 | 50.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 53.8 | 28.0-77.6 | 38.5 | 55.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 53.0 | 28.4-76.5 | 37.9 | 68.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 59.3 | 34.8-84.4 | 43.9 | 29.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | deepseek-v4-flash | cross | 61.8 | 36.4-83.7 | 44.7 | 74.0 |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 52.9 | 28.7-76.6 | 20.1 | 85.0 |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 55.7 | 29.8-78.0 | 44.2 | 48.0 |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 49.8 | 25.3-74.8 | 50.6 | 87.0 |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 49.2 | 25.2-74.3 | 54.1 | 86.0 |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 55.3 | 31.2-80.4 | 46.6 | 55.0 |
| alfworld | Phi-4-mini-instruct | deepseek-v4-flash | cross | 53.6 | 28.2-77.9 | 48.1 | 90.0 |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | cross | 51.9 | 27.1-76.0 | 32.4 | 66.0 |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | self | 60.7 | 35.5-81.1 | 38.2 | 52.0 |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | self | 66.8 | 41.3-85.1 | 36.9 | 48.0 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 72.9 | 57.1-86.7 | 27.1 | 47.0 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 60.5 | 39.0-80.6 | 15.6 | 68.0 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 58.4 | 35.8-79.6 | 15.1 | 67.0 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 66.8 | 40.8-86.1 | 40.1 | 39.0 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | cross | 80.4 | 63.5-91.2 | 36.6 | 37.0 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 55.5 | 32.6-77.8 | 7.2 | 74.0 |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | self | 66.2 | 48.3-82.8 | 38.3 | 62.0 |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 54.1 | 29.5-75.1 | 44.8 | 51.0 |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 50.9 | 27.8-74.2 | 45.9 | 85.0 |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | cross | 50.6 | 27.7-73.3 | 45.2 | 85.0 |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 61.5 | 36.3-83.3 | 42.4 | 54.0 |
| alfworld | gemma-3-4b-it | deepseek-v4-flash | cross | 54.7 | 28.9-77.9 | 48.1 | 38.0 |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | self | 52.1 | 28.4-75.2 | 20.4 | 79.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | self | 81.7 | 66.0-92.1 | 40.4 | 39.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | cross | 71.1 | 51.9-86.1 | 24.9 | 50.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | cross | 71.7 | 54.9-86.0 | 22.8 | 60.0 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | cross | 83.1 | 68.4-93.3 | 43.3 | 38.0 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | cross | 75.5 | 60.5-88.1 | 27.0 | 50.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | cross | 69.7 | 52.0-86.8 | 42.3 | 58.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | self | 62.6 | 41.0-81.7 | 31.1 | 63.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | cross | 63.6 | 40.4-83.1 | 30.4 | 69.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | cross | 79.9 | 64.7-90.4 | 43.8 | 40.0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | cross | 65.8 | 44.5-84.2 | 32.4 | 68.0 |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | cross | 72.7 | 53.5-87.5 | 42.8 | 54.0 |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | cross | 56.1 | 30.9-77.8 | 42.5 | 50.0 |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | self | 57.9 | 32.1-79.6 | 40.2 | 50.0 |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | cross | 69.1 | 50.1-84.0 | 45.6 | 50.0 |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | cross | 61.5 | 34.6-81.2 | 40.3 | 43.0 |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | self | 78.4 | 63.0-90.3 | 39.0 | 42.0 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | cross | 81.9 | 64.8-92.1 | 40.1 | 43.0 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | cross | 68.5 | 50.3-85.0 | 24.6 | 60.0 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | cross | 70.6 | 53.8-85.9 | 22.5 | 58.0 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | self | 83.8 | 70.6-93.6 | 42.9 | 34.0 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | cross | 74.6 | 60.0-87.9 | 26.8 | 52.0 |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | cross | 67.3 | 49.2-83.7 | 43.7 | 60.0 |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | cross | 60.8 | 39.4-80.5 | 32.5 | 69.0 |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | cross | 61.5 | 40.7-80.4 | 29.8 | 68.0 |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | cross | 69.5 | 48.4-83.7 | 46.0 | 45.0 |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | self | 62.9 | 43.1-80.9 | 33.7 | 61.0 |
