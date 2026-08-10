# T12 — GATE-4 Part A per-cell forecasts (+ the 27B extrapolation cell)

**Caption-of-record.** Sealed forecasts (π̂) vs realized optima (π*) on untouched targets, primary construct, 8 of 10 cells evaluable. The failure is judge-asymmetric: Llama-70B forecasts land at 0.0–6.1 points and beat V 4/4; Qwen3.6 forecasts land at 4.7–11.5 points and lose to V twice — narrowly (−0.010 and −0.001), but those losses take P-A1 below its bar. The evaluated variant is **h-noself** (registered A34.1; see seal-defect disclosure). The 27B cell (T12c) is unevaluable on the primary construct and reported separately: π̂ misses π* by 31–55 percentile points on environment constructs — extrapolation degrades sharply, and this is the basis of scope condition 3 (interpolation only).

- Labels: L2 · construct: violation+judgment (T12c: violation/outcome/y_env) · claim: C-h-forecast
- source: `GATE4_SUMMARY.md` per-cell tables; full evaluation grid `T12b_partA_full_evaluation.csv` (copy of `tables_gate4/A_forecast_evaluation.csv`, 100 rows: 20 cells × 5 constructs)

| judge | target | π̂ | π* | \|Δ\| pts | BA@cut | V | fitted |
|---|---|---|---|---|---|---|---|
| Llama-70B | alfworld/Qwen3.5-4B | 0.506 | 0.506 | 0.0 | 0.695 | 0.675 | 0.696 |
| Llama-70B | alfworld/Qwen3.5-9B | 0.551 | 0.490 | 6.1 | 0.682 | 0.651 | 0.688 |
| Llama-70B | hotpotqa/Qwen3.5-4B | 0.706 | 0.678 | 2.8 | 0.818 | 0.764 | 0.839 |
| Llama-70B | hotpotqa/Qwen3.5-9B | 0.730 | 0.698 | 3.2 | 0.832 | 0.731 | 0.842 |
| Qwen3.6 | alfworld/Qwen3.5-4B | 0.533 | 0.460 | 7.3 | 0.696 | 0.692 | 0.700 |
| Qwen3.6 | alfworld/Qwen3.5-9B | 0.579 | 0.464 | 11.5 | 0.702 | **0.712** | 0.717 |
| Qwen3.6 | hotpotqa/Qwen3.5-4B | 0.592 | 0.693 | 10.1 | 0.836 | **0.837** | 0.842 |
| Qwen3.6 | hotpotqa/Qwen3.5-9B | 0.613 | 0.660 | 4.7 | 0.821 | 0.806 | 0.829 |
