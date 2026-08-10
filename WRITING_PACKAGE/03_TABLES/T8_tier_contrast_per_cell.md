# T8 — Tier contrast per cell: mid judge's score vs large judge's verdict, three regimes

**Caption-of-record.** Qwen3.6-35B (score rules) vs Llama-3.3-70B (verdict) on all 11 shared targets. With ~200 target labels the mid score sweeps the large verdict 11/11. Fully label-free (g-rule): 8/11 overall, 8/9 in cross-judging cells — the design's regime; the two real losses are Qwen judging itself (self-leniency), the third is −0.001. Single-cell anecdote: the external mid-size g-rule reads deepseek's trajectories at 0.800 vs deepseek's own self-reading at its own cut (~0.72–0.76).

- Labels: L1 · claim: C-tier · source: `reports/report_gate2_score_vs_verdict.md` §3

| cell | L70B verdict | Q35 g-rule (zero target labels) | Q35 fitted (~200 labels) |
|---|---|---|---|
| alfworld / Llama-70B | 0.762 | 0.790 | 0.823 |
| alfworld / Mistral-7B | 0.727 | 0.776 | 0.780 |
| alfworld / Phi-4-mini | 0.665 | 0.739 | 0.748 |
| alfworld / Qwen-35B *(self)* | 0.649 | 0.602 | 0.664 |
| alfworld / deepseek-v4-flash | 0.715 | **0.800** | 0.772 |
| alfworld / gemma-3-4b | 0.707 | 0.811 | 0.811 |
| hotpotqa / Llama-70B | 0.691 | 0.734 | 0.761 |
| hotpotqa / Mistral-7B | 0.769 | 0.771 | 0.771 |
| hotpotqa / Phi-4-mini | 0.826 | 0.825 | 0.836 |
| hotpotqa / Qwen-35B *(self)* | 0.619 | 0.597 | 0.790 |
| hotpotqa / gemma-3-4b | 0.833 | 0.834 | 0.843 |
