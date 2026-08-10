# T14 — GATE-4 Part C: fit stability (disclosure, not a gate)

**Caption-of-record.** Stable iff max jackknife swing ≤ 8 percentile points. 3 of 4 fits stable; the exception is alfworld/Qwen3.6 at 11.7 points, whose leverage target is **the judge's own self-cell**, with a slope CI ~5× wider than the others. Qwen3.6 is also the judge whose Part A forecasts miss widest. Recorded as a disclosure beside Part A's verdict, not as its explanation. This table is the empirical basis of B-1 (S8) — a two-point track record, offered as such.

- Labels: L2 · construct: violation+judgment · claim: C-stability
- source: direct copies of `tables_gate4/C_fit_stability.csv` and `tables_gate4/C_jackknife_swings.csv` (T14b)

| env | judge | targets | slope | slope 95% CI | max swing | stable | leverage |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B | 6 | −0.494 | [−0.618, −0.378] | 3.4 | yes | — |
| alfworld | Qwen3.6-35B | 6 | −0.620 | [−1.249, −0.258] | **11.7** | **no** | Qwen3.6 self-cell |
| hotpotqa | Llama-3.3-70B | 5 | −0.614 | [−0.670, −0.462] | 1.2 | yes | — |
| hotpotqa | Qwen3.6-35B | 5 | −0.522 | [−0.657, −0.477] | 1.0 | yes | — |
