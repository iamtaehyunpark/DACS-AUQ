# GATE-3 SUMMARY (A33) — final label-free attempt

Spec: `GATE3_SPEC_A33.md`. Primary construct **violation+judgment**, capable stratum, seed 13, 2000 draws.

## Arm 0 — h-rule (spec §2)

The direct percentile map was pre-registered as an S1 secondary and **was not computed there** (S1d ran b1/A28/A28.1 only). It is computed here as the S1 spec defined it.

## Verdicts, primary construct, capable stratum

| arm | pass-rate | 95% CI | pooled capture | 95% CI | abstain | verdict |
|---|---|---|---|---|---|---|
| arm 0 — h-rule (pct* ~ mean-U) | 20/22 (91%) | [0.77, 1.00] | 0.940 | [0.80, 1.04] | 0 | **PASS** |
| arm 1 — mixture cut | 8/22 (36%) | [0.18, 0.55] | -0.180 | [-0.98, 0.43] | 4 | **FAIL** |
| arm 2 — violation-calibrated | 19/22 (86%) | [0.73, 1.00] | 0.969 | [0.88, 1.03] | 0 | **PASS** |

Bars are A28.1's, unchanged: PASS needs ≥80% of countable cells at or above V **and** pooled capture ≥0.5. Abstentions count as losses (spec §3.4).

## Closure clause (spec §6)

**NOT INVOKED** — an arm reached PASS on the primary construct. §6d recovers a deployment story with this gate as its provenance; the A28 and A28.1 verdicts remain beside it in the record.

Sentence §6d leads with: *a label-free operating point transfers across targets when it is placed by the arm above, at the capture and pass-rate recorded here.*

## Per-construct tables

- `tables_gate3/gate3_cells_violation-judgment.csv` (55 cells)
- `tables_gate3/gate3_cells_judgment.csv` (55 cells)
- `tables_gate3/gate3_cells_violation.csv` (55 cells)
- `tables_gate3/gate3_cells_outcome.csv` (55 cells)
- `tables_gate3/gate3_cells_y_env.csv` (55 cells)

