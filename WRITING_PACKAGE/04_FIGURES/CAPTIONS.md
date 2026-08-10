# 04_FIGURES — captions-of-record

Raw plotting data only; no rendered images. Each caption is factual and final; the
writer may typeset but not reinterpret.

## F1 — Score-vs-verdict per-cell scatter
**Data:** `F1_verdict_vs_value_cells.csv` (copy of `reports/tables/verdict_vs_value.csv`, 60 cells).
**Caption.** Out-of-sample value (fitted-cut P(True)) vs verdict balanced accuracy per (judge, target, environment) cell; 60 cells. Value ≥ verdict in 55/60; mean gain +0.065 [0.052, 0.079]; in-sample optimism +0.009. Plot `value_out` against `verdict` with the diagonal; the five below-diagonal cells are identifiable from the `gain_out` column. Labels L1 (L2 per-construct gains +0.073…+0.133 quoted beside it from S1_SUMMARY).

## F2 — Flatness curves
**Data:** `F2_flatness_curves.csv` (copy of `figures/figures_gate2b1/flatness_curves_AGG-true.csv`; 2,178 data rows: dataset, assessor, target, pct, cut, bal_acc, realized_flag).
**Caption.** BA as a function of cut percentile per capable cell. Median flat region (within 0.01 of the optimum) is 16 percentile points wide (min 10): a cut placed within ~±8 points of the optimum loses ≤0.01 BA. This is the error budget every label-free placement rule is judged against, and the ±8-point budget used by GATE-4 Part C. Labels L1 (banked curves; the budget was reused as-registered for L2 gates).

## F3 — Part B conditional distances
**Data:** `F3_partB_wasserstein_pairs.csv` (copy of `tables_gate4/B_wasserstein_pairs.csv`, 100 rows).
**Caption.** Pairwise within-class between-target 1-Wasserstein distances per (judge, environment), violation+judgment, L2, self-cells excluded. Supports T13: conditional invariance holds on hotpotqa (ratios 0.162/0.151) and fails on alfworld (0.809/0.364). NOTE: per-target class-conditional density overlays (f₀, f₁ curves) were not banked as CSV; only these pairwise distances and the verdict table exist — see 06_GAPS.

## F4 — Prequential warm-up curves
**Data:** `F4_prequential_curves_violation-judgment.csv`, `F4b_prequential_curves_judgment.csv` (copies of `tables_S7/S7_curves_*.csv`; 4,554/4,540 data rows: cumulative BA per step index, per cell and ordering summary).
**Caption.** Cumulative balanced accuracy of the sequential g-rule vs step index, warm-up 100 steps, 10 episode orderings (seeds 13–22), 22 capable cells. Post-warm-up tracks batch to −0.0002 (v+j) / +0.0007 (judgment); warm-up-inclusive penalty −0.0011/−0.0005; P-warm fails 0/22 — the warm-up is not free. The batch rule itself failed its gate (G2b1-R3, L2); tracking a failed rule is faithfulness, not success. Labels L2.

## F5 — GATE-4 forecast π̂ vs π*
**Data:** `F5_forecast_pi_data.csv` (copy of `tables_gate4/A_forecast_evaluation.csv`, 100 rows; plot columns `pi_hat` vs `realised_pct`, filter `construct == eval_construct == violation+judgment`, `extrapolation == 0` for the 8 evaluable cells; `extrapolation == 1` rows are the 27B cell).
**Caption.** Sealed forecast percentile π̂ against realized optimal percentile π* per untouched-target cell, primary construct, h-noself variant. Llama-70B cells sit within 0.0–6.1 points of the diagonal; Qwen3.6 cells at 4.7–11.5 points; the ±8-point budget band decides P-A2. The 27B extrapolation cell misses by 31–55 points on environment constructs. Labels L2. Forecasts sealed at commit 5a4938fd before evaluation.

## F6 — Evidence-grid ladder
**Data:** `F6_evidence_grid_ladder.csv` (same values as T5; transcribed from `reports/results_report_2026-08-05.md` §4).
**Caption.** AUROC with 95% CI per evidence condition, ordered C0 → C6 with the rubric/rule arms beside the base. The ladder: action alone is chance (0.512); history carries the signal (0.697); realized evidence is the largest increment (0.813); a targeted rule reproduces it pre-execution (0.813) against a decoy floor (0.728). Labels L1; Qwen3.6-35B judge, n≈300/condition.

## F7 — h-arc timeline
**Data:** `F7_h_arc_timeline.csv` (assembled-from: `FINAL_BUNDLE/GATES_LEDGER.md`, `GATE2B_SUMMARY.md`, `GATE2B1_SUMMARY.md`, `S1_SUMMARY.md`, `GATE3_SUMMARY.md`, `GATE4_SUMMARY.md`).
**Caption.** Verdict per gate along the label-free placement arc, both label passes where both exist: A28 (L1 68% / L2 55%) → A28.1 (L1 82% PASS-marginal / L2 77% FAIL) → GATE-3 arms (h 91% PASS within-gate; mixture 36% FAIL; violation-calibrated 86% PASS, not label-free) → GATE-4 Part A (75%, FAIL against its ≥8/10 bar; closure invoked). Pass-rate percentages are not comparable across bars — each gate's bar is drawn in T11.
