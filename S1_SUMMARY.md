# S1 SUMMARY — stratified recompute + gate-2 L2 pass of record

Spec: `docs/specs/S1_SPEC.md`. Scope AGG-true, seed 13, 2000 bootstrap draws.

Labels: **L2 (gate-1) is the pass of record**; L1 reported beside it.

## Reproduction check (spec §7)

The L1 pass through this harness vs the banked A28.1 table, tolerance 0.001: **PASS**

Every cell and every arm reproduces. Nothing but the label input differs between this harness and the banked gates.

## S1a — crossprobe matrix per construct (L2)

| construct | cells | countable | underpowered | mean AUROC |
|---|---|---|---|---|
| violation | 56 | 56 | 0 | 0.7853 |
| outcome | 56 | 56 | 0 | 0.7203 |
| judgment | 56 | 56 | 0 | 0.7168 |
| y_env | 56 | 56 | 0 | 0.7396 |
| violation+judgment | 56 | 56 | 0 | 0.7140 |

## A30 §4 prediction (i) — capable external superiority intact on violation+judgment

**PASS** — capable wins in 11/11 countable external cells; pooled Δ 0.2222, 95% CI [0.1802, 0.2724].

## A30 §4 prediction (ii) — self-probe inflation confined to outcome strata

**PASS** — the self-minus-external gap is larger under `outcome` than under `violation+judgment` in 9/11 arms; mean difference-of-differences 0.1185, 95% CI [0.0359, 0.2054].

## S1b — independence restatement (R3 obligation)

Best-self vs best-external per arm, paired episode-clustered CI on Δ = AUROC(best external) − AUROC(self). **Positive Δ means the external judge reads the target better than the target reads itself.**

- **violation**: 11 arms; external beats self in 10; 7 have a CI excluding 0.
- **outcome**: 11 arms; external beats self in 10; 8 have a CI excluding 0.
- **judgment**: 11 arms; external beats self in 10; 10 have a CI excluding 0.
- **y_env**: 11 arms; external beats self in 10; 7 have a CI excluding 0.
- **violation+judgment**: 11 arms; external beats self in 9; 10 have a CI excluding 0.

## S1d — gate verdicts, L1 vs L2 per construct (capable stratum)

The capable stratum is the decisive one, declared in the A28.1 spec before any result existed.

| construct | b1 gain | b1 cells | A28 P-quantile | A28 | A28.1 P-g2 | A28.1 capture | A28.1 |
|---|---|---|---|---|---|---|---|
| L1 (banked) | +0.065 | 55/60 | 15/22 (68%) | **G2b-R3 FAIL** | 18/22 (82%) | 0.555 | **G2b1-R1 PASS** |
| violation | +0.133 | 48/56 | 9/22 (41%) | **G2b-R3 FAIL** | 13/22 (59%) | 0.737 | **G2b1-R3 FAIL** |
| outcome | +0.110 | 50/56 | 18/22 (82%) | **G2b-R1 PASS** | 9/22 (41%) | 0.361 | **G2b1-R3 FAIL** |
| judgment | +0.074 | 52/56 | 11/22 (50%) | **G2b-R3 FAIL** | 18/22 (82%) | 0.484 | **G2b1-R2 PARTIAL** |
| y_env | +0.117 | 49/56 | 15/22 (68%) | **G2b-R3 FAIL** | 8/22 (36%) | 0.271 | **G2b1-R3 FAIL** |
| violation+judgment | +0.073 | 52/56 | 12/22 (55%) | **G2b-R3 FAIL** | 17/22 (77%) | 0.455 | **G2b1-R3 FAIL** |

## Tables

- `tables_S1/S1a_crossprobe_L2_judgment.csv`
- `tables_S1/S1a_crossprobe_L2_outcome.csv`
- `tables_S1/S1a_crossprobe_L2_violation-judgment.csv`
- `tables_S1/S1a_crossprobe_L2_violation.csv`
- `tables_S1/S1a_crossprobe_L2_y_env.csv`
- `tables_S1/S1b_independence_L2_judgment.csv`
- `tables_S1/S1b_independence_L2_outcome.csv`
- `tables_S1/S1b_independence_L2_violation-judgment.csv`
- `tables_S1/S1b_independence_L2_violation.csv`
- `tables_S1/S1b_independence_L2_y_env.csv`
- `tables_S1/S1c_pred_i_L2.csv`
- `tables_S1/S1c_pred_ii_L2.csv`

