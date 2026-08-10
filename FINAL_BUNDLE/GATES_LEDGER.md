# GATES_LEDGER — every gate and rule verdict, chronological

**2026-08-10 · L1 = 3-judge ensemble (preview) · L2 = gate-1 environment-anchored (pass of record)**

| gate | rule | labels | verdict | deciding numbers |
|---|---|---|---|---|
| **gate-1 R1** | qualification floors on *f* | L2 | **FAIL** | lowest capable-judge *f* 0.669 vs 0.70 floor; ordering inverted (Qwen 0.752 > Llama 0.669) |
| **gate-1 R2** | the g fit | L2 | **PASS** | weakest capable-judge \|r\| 0.948 vs 0.85 floor |
| **gate-1 R3** | crossprobe movement | L1→L2 | **FLAG** | 161 of 240 cells move > 0.05 AUROC |
| **gate-1 R4** | ensemble circularity audit | — | **REPORTED** | 9.1% of environment-settled steps called correct; 2.0% ex-A4; unanimous on all 2,233 |
| **gate-2 b1** | value vs verdict | L1 | **PASS** | +0.065 OOS, 55/60 cells |
| **gate-2 b1** | value vs verdict | L2 | **PASS** | +0.073…+0.133 per construct, 48–52/56 cells |
| **A28 (gate-2b)** | fixed-percentile transfer | L1 | **R3 FAIL** (capable) / R1 PASS (all) | P-quantile 15/22 (68%) vs 80% bar |
| **A28 (gate-2b)** | fixed-percentile transfer | L2 | **R3 FAIL** on primary | 12/22 (55%), capture 0.310 |
| **A28.1 (gate-2b.1)** | g-rule, error-rate-indexed | L1 | **R1 PASS (marginal)** | P-g2 18/22 (82%), capture 0.555; both CIs straddle their bars |
| **A28.1 (gate-2b.1)** | g-rule | L2 | **R3 FAIL** on primary | P-g2 17/22 (77%), capture 0.455 |
| **A33 (gate-3) arm 0** | h-rule, direct percentile | L2 | **PASS** | 20/22 (91%), capture 0.940; closure NOT invoked |
| **A33 (gate-3) arm 1** | mixture cut | L2 | **FAIL** | 8/22 (36%), capture −0.180, 4 abstentions counted as losses |
| **A33 (gate-3) arm 2** | violation-calibrated | L2 | **PASS** | 19/22 (86%), capture 0.969; NOT label-free — "human-annotation-free" |
| **A34 (gate-4) Part A** | forecast-first validation on untouched targets | L2 | **FAIL** | P-A1 6/8 vs ≥8/10; P-A2 6/8; capture 0.750. **Closure INVOKED** |
| **A34 Part B** | conditional invariance | L2 | **SPLIT** | hotpotqa holds (0.162, 0.151); alfworld fails (0.809, 0.364) |
| **A34 Part C** | fit stability | L2 | **3 of 4 stable** | swings 3.4 / 1.2 / 1.0; alfworld-Qwen3.6 11.7 pts, leverage = its own self-cell |
| **A34 Part D** | cross-environment h | L2 | **NO-CLAIM** | −0.0024, CI [−0.0047, 0.0001] includes 0 |
| **G2-R4 (S5/b3)** | frontier vs mid-tier judge | L2 | **RESOLVED** | gpt-4o −0.021 vs capable open judges; +0.147 vs all open judges |
| **S8 floors** | qualification, new registration | L2 | **SIGNED 2026-08-10** | A-1 + B-1 (necessary, not sufficient) + scope conditions 1–4 |

## Closure clauses invoked

- **GATE-3 §6** — NOT invoked (h passed within-gate). No rule variant #4 was ever proposed.
- **GATE-4 §Closure** — **INVOKED**. h scoped to within-gate validation only; §6d leads with the ~200-label tier; the forecast miss is published as the boundary.

## A-log entries bearing on verdicts

**A30** construct taxonomy (violation / outcome / judgment) · **A31** retrospective stream dropped, migrated to follow-up work · **A32** judgment-as-human-proxy, validated ~2% on the environment-certain band, untested on the contested band · **A34.1** h-noself registered pre-lock · **A35** S4 dropped after template-bug void; answer-distribution tripwire adopted.

## Registration integrity notes

- **R1's FAIL stands.** The S8 floors are a NEW registration, not a revision.
- **A28.1's L1 PASS was a preview.** The pass of record is L2, which FAILS. The CI registry carries the L2 point estimates.
- **GATE-4's seal** is at commit `5a4938fd`, sha256 `69b926a0…`, evaluated after. Both sealed variants proved to be **h-noself**; the h-with-self forecast was never sealed and cannot be now.
