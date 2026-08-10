# T5 — Evidence grid with CIs

**Caption-of-record.** Paired, decoy-controlled ablation of what the judge reads (Qwen3.6-35B judge, n≈300/condition, AUROC with 95% CI). An action alone is chance (0.512); history is the signal carrier (→0.697); the realized observation is the largest single increment (+0.072 over base, →0.813); a targeted rule reproduces that gain pre-execution (0.813, +0.085 over the decoy floor); the action token is dispensable given history+reasoning (0.740 ≈ 0.741). Rules also manufacture false positives on rule-adjacent correct steps (+0.155 on legitimate revisits — proposal v4 §6a).

- Labels: L1 · claim: C1-nointrinsic (grid receipts) · source: `reports/results_report_2026-08-05.md` §4; FP number from `docs/paper_proposal_v4.md` §6a

| condition | contents | ΔU (inc−cor) | AUROC [95% CI] |
|---|---|---|---|
| C0/R0 | task + action | 0.011 | 0.512 [0.438, 0.586] |
| C1/R0 | + last observation | 0.150 | 0.622 [0.555, 0.685] |
| C2/R0 | + full history | 0.242 | 0.697 [0.637, 0.755] |
| C3/R0 (base) | + reasoning | 0.248 | 0.741 [0.675, 0.801] |
| C4/R0 | C3 − action | 0.229 | 0.740 [0.673, 0.798] |
| C5/R0 | C3 + realized observation | 0.396 | 0.813 [0.756, 0.865] |
| C6/R0 | C5 + next thought/action | 0.299 | 0.845 [0.799, 0.888] |
| C3/R1 | + generic rubric | 0.325 | 0.804 [0.746, 0.853] |
| C3/R2 | + targeted rule | 0.366 | 0.813 [0.753, 0.866] |
| C3/R3 | + decoy rule | 0.242 | 0.728 [0.661, 0.789] |
| C0/R2 | rule without history | 0.026 | 0.531 [0.455, 0.603] |
