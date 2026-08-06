# Gate-1 Phase 5 — normalised separation f, ensemble vs environment label

`f = (median percentile of the incorrect pool - 50) / (perfect-ranking bound - 50)`, bound `= 100*(1 - p/2)` for error rate p. Base-rate free. This is the quantity R1's floor is stated on (f >= 0.70, range width <= 0.25).

| assessor | ensemble mean (range) | ensemble_on_env_support mean (range) | env_restricted mean (range) | env_full mean (range) | cells |
|---|---|---|---|---|---|
| Llama-3.3-70B-Instruct | 0.876 (0.78–0.98) | 0.867 (0.72–0.98) | 0.669 (0.34–1.00) | 0.624 (0.36–0.85) | 11 |
| Mistral-7B-Instruct-v0.3 | 0.484 (0.27–0.71) | 0.455 (0.29–0.64) | 0.577 (0.23–0.96) | 0.349 (0.06–0.55) | 11 |
| Phi-4-mini-instruct | 0.259 (-0.08–0.57) | 0.189 (-0.05–0.45) | 0.636 (0.34–0.97) | 0.394 (0.16–0.55) | 11 |
| Qwen3.5-27B | — | — | 0.673 (0.67–0.67) | 0.605 (0.60–0.60) | 1 |
| Qwen3.5-4B | 0.603 (0.45–0.75) | 0.569 (0.45–0.68) | 0.614 (0.42–0.81) | 0.559 (0.39–0.73) | 2 |
| Qwen3.5-9B | 0.667 (0.62–0.71) | 0.640 (0.61–0.67) | 0.681 (0.44–0.92) | 0.614 (0.41–0.82) | 2 |
| Qwen3.6-35B-A3B | 0.842 (0.54–0.97) | 0.810 (0.54–0.97) | 0.752 (0.40–1.00) | 0.630 (0.38–0.81) | 11 |
| deepseek-v4-flash | 0.485 (0.49–0.49) | 0.495 (0.50–0.50) | 0.582 (0.58–0.58) | 0.476 (0.48–0.48) | 1 |
| gemma-3-4b-it | 0.323 (0.05–0.52) | 0.201 (0.06–0.39) | -0.181 (-0.92–0.35) | 0.314 (0.03–0.63) | 11 |
