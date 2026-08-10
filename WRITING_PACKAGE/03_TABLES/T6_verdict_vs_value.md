# T6 — Verdict vs value per judge (+ optimism)

**Caption-of-record.** Value (P(True) with a cut fitted out-of-sample by episode) vs the same judge's argmax verdict, balanced accuracy over 60 cells. Value ≥ verdict in 55/60 cells (92%); mean gain +0.065; the fitted cut's in-sample optimism is +0.009, so the win is not overfitting. The verdict needs no logprob access; the value does — the gain is the price of one logit read.

- Labels: L1 (L2 per-construct gains: +0.073…+0.133, `S1_SUMMARY.md` S1d) · claims: C-chan, C-chan-frac
- source: `reports/report_gate2_score_vs_verdict.md` §1; per-cell data `reports/tables/verdict_vs_value.csv` (also shipped as F1)

| judge | n | mean gain (value − verdict) | cells value < verdict |
|---|---|---|---|
| Llama-3.3-70B | 11 | +0.044 | 2 |
| Qwen3.6-35B | 11 | +0.048 | 1 |
| Mistral-7B | 11 | +0.110 | 0 |
| gemma-3-4b | 11 | +0.107 | 0 |
| Phi-4-mini | 11 | +0.024 | 2 |
| deepseek (self, 1 cell) + Qwen3.5-4B/9B (2 each) | 5 | +0.011…+0.098 | 0 |
| **ALL** | **60** | **+0.065** | **5** |
