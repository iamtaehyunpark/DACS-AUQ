# S4_COST — hindsight-ceiling pass (STOP gate)

**This branch is HALTED pending author budget acknowledgement (EXECUTION_HANDOVER.md §5).** Nothing has been launched.

## Exact assessment count

| judge | arms | steps per pass | assessments |
|---|---|---|---|
| Llama-3.3-70B-Instruct | 11 | 38,513 | 38,513 |
| Qwen3.6-35B-A3B | 11 | 38,513 | 38,513 |
| **total** | 11 | | **77,026** |

Only the **hindsight** condition is new inference; the online (C3-grade prefix) condition is banked and reused, so this is one matrix pass, not two.

## Hours

At the inherited 3300 assessments / 5 min / A100 — flagged **unverified** in the manifest — one A100 gives 1.9 A100-hours. Bracketing the rate at ±50% because §1 requires a 500-step probe before any GPU stage sizes itself: **1.3 – 3.9 A100-hours**.

With all 5 A100s free (S0 capacity check), wall clock is roughly **0.3 – 0.8 hours**.

> **This sizing disagrees with the handover.** §5 estimates 6–10 A100-hours; the arithmetic here gives 1.3–3.9. The handover figure is 2.6x the upper bound of this bracket. Either the inherited throughput constant is optimistic (likely — hindsight prompts are longer), or §5's estimate assumed both evidence conditions rather than the hindsight one alone. **The 500-step probe resolves which, and should be run before the author is asked to approve anything.** Until then treat 10 A100-hours as the number to budget against, not 3.9.

Hindsight prompts carry the full trajectory plus episode outcome, so they are LONGER than the banked online prompts and the true rate will be below the inherited constant. Treat the upper bound as the planning number.

## Per-arm breakdown

| dataset | arm | labelled steps | x2 judges |
|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 4,492 | 8,984 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6,321 | 12,642 |
| alfworld | Phi-4-mini-instruct | 6,452 | 12,904 |
| alfworld | Qwen3.6-35B-A3B | 3,255 | 6,510 |
| alfworld | deepseek-v4-flash | 3,025 | 6,050 |
| alfworld | gemma-3-4b-it | 6,730 | 13,460 |
| hotpotqa | Llama-3.3-70B-Instruct | 1,163 | 2,326 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 2,375 | 4,750 |
| hotpotqa | Phi-4-mini-instruct | 1,885 | 3,770 |
| hotpotqa | Qwen3.6-35B-A3B | 1,157 | 2,314 |
| hotpotqa | gemma-3-4b-it | 1,658 | 3,316 |

## What the author is being asked

Approve up to **10 A100-hours** (the handover's own §5 ceiling) for the hindsight condition; this document's arithmetic says 1.3–3.9 but the throughput constant behind it is unverified.

A30 calls this the keystone: it converts the construct taxonomy from argument into measurement, and decomposes the R3 movements into information-gap vs construct-gap. S1d raises the stakes — the construct choice now decides a gate verdict, not just a framing.

