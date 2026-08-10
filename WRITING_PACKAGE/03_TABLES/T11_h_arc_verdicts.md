# T11 — The h arc: A28 → A28.1 → GATE-3 → GATE-4, both label passes

**Caption-of-record.** Three label-free placement attempts, bars never moved (PASS needs ≥80% of countable capable cells at or above V and pooled capture ≥0.5). Fixed-percentile FAILED; the error-rate-indexed g-rule passed marginally on L1 and FAILED on L2 (the pass of record); the h-rule passed within-gate on L2 (20/22, capture 0.940) and then FAILED forecast-first validation on untouched targets (P-A1 6/8 vs ≥8/10). GATE-4's closure is invoked: h is scoped to within-gate validation only and §6d leads with the ~200-label tier.

- Labels: L1 and L2 as marked · construct: violation+judgment (capable stratum) · claims: N-fixedpct, N-grule, N-mixture, C-h-withingate, C-h-forecast
- assembled-from: `FINAL_BUNDLE/GATES_LEDGER.md` + `reports/gate2/GATE2B_SUMMARY.md` + `reports/gate2/GATE2B1_SUMMARY.md` + `S1_SUMMARY.md` + `GATE3_SUMMARY.md` + `GATE4_SUMMARY.md` + `tables_bundle/ci_registry_final.csv`

| gate | rule | labels | capable pass-rate | capture | verdict |
|---|---|---|---|---|---|
| A28 | fixed percentile | L1 | 15/22 (68%) [50, 86] | 0.552 [0.364, 0.718] | **FAIL** (capable) / PASS (all judges 44/55, 0.775) |
| A28 | fixed percentile | L2 | 12/22 (55%) | 0.310 | **FAIL** |
| A28.1 | g-rule (error-rate-indexed) | L1 | 18/22 (82%) [64, 95] | 0.555 [0.084, 0.844] | **PASS (marginal)** |
| A28.1 | g-rule | L2 | 17/22 (77%) | 0.455 | **FAIL** (pass of record) |
| A33 arm 0 | h-rule (percentile map) | L2 | 20/22 (91%) [0.77, 1.00] | 0.940 [0.80, 1.04] | **PASS** within-gate |
| A33 arm 1 | mixture cut | L2 | 8/22 (36%) [0.18, 0.55] | −0.180 [−0.98, 0.43] | **FAIL** (4 abstentions as losses) |
| A33 arm 2 | violation-calibrated | L2 | 19/22 (86%) [0.73, 1.00] | 0.969 [0.88, 1.03] | **PASS** — not label-free |
| A34 Part A | forecast-first (h-noself) | L2 | P-A1 6/8 vs ≥8/10 | 0.750 pooled | **FAIL** — closure invoked |
