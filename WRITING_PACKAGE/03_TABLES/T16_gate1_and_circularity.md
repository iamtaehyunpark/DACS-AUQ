# T16 — Gate-1 R1–R4 and the circularity audit by sub-rule

**Caption-of-record.** Gate-1 replaced judge-ensemble labels with environment-derived labels under pre-registered rules: R1 FAIL (floors did not freeze; capable f 0.669 vs 0.70, ordering inverted), R2 PASS (weakest capable |r| 0.948 vs 0.85), R3 FLAG (161/240 cells move > 0.05), R4 REPORTED. The circularity audit, designed to indict the ensemble, substantially validated it where ground truth is certain — per-sub-rule error 0.0–1.9% ex-A4 (2.0% overall) — while proving the constructs diverge on A4 (31.5%). All 2,233 miscalled matrix-arm steps were unanimous. R4's error rate is a floor, not an estimate: it is measured only where errors are most blatant.

- Labels: L2 vs L1 (the audit compares them) · claim: C4-corpus
- assembled-from: `reports/gate1/GATE1_SUMMARY.md` + `reports/gate1/report_phase2_ensemble_audit.md`

| sub-rule | steps (judged) | ensemble said CORRECT |
|---|---|---|
| A1_inadmissible | 9768 (9610) | 126 (1.3%) |
| A1_malformed_toolcall | 89 (47) | 0 (0.0%) |
| A2_nothing_happens | 6062 (6000) | 49 (0.8%) |
| A3_exact_repeat | 14788 (14682) | 276 (1.9%) |
| A3_repeat_query | 2734 (2724) | 9 (0.3%) |
| A4_zero_result | 5785 (5785) | **1823 (31.5%)** |

Headline: matrix arms 9.1% (2233/24631), **2.0% ex-A4** (410/20521); all arms 10.6% (3174/29998).
