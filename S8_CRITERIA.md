# S8_CRITERIA — Qualification Proposal (post-GATE-4)

**2026-08-10 · Directive of 2026-08-10 §1 · THREE PARTS, SIGNED SEPARATELY · then HALT**

> **R1 FAILED as registered** (lowest capable-judge *f* 0.669 against a 0.70 floor;
> ordering inverted, Qwen 0.752 > Llama 0.669). Nothing below un-fails that gate.
> Anything adopted here is a **NEW registration**, and R1's FAIL stays in the ledger.

Evidence base: L2 labels, per-construct S1a separation tables, GATE-3 (h PASS
within-gate), GATE-4 (Part A **FAIL** on forecast-first validation; Part B split; Part
C stability; Part D no-claim), S5 (frontier arm).

---

# (a) Qualification floors — DISCRIMINATION

Mean external-cell AUROC, L2, self-cells excluded, underpowered cells dropped.
Six judges have been tested as assessors; the frontier arm is measured on the b3
sample.

| judge | scale | viol+jud | judgment | violation | outcome | y_env |
|---|---|---|---|---|---|---|
| Qwen3.6-35B-A3B | 35B (3B active) | **0.898** | 0.907 | 0.862 | 0.774 | 0.800 |
| Llama-3.3-70B | 70B | **0.876** | 0.884 | 0.846 | 0.734 | 0.770 |
| gpt-4o (frontier) | API | **0.859** | 0.861 | 0.822 | 0.711 | 0.732 |
| Mistral-7B-v0.3 | 7B | 0.679 | 0.682 | 0.818 | 0.759 | 0.780 |
| gemma-3-4b-it | 4B | 0.590 | 0.582 | 0.649 | 0.598 | 0.605 |
| Phi-4-mini | 3.8B | 0.546 | 0.546 | 0.748 | 0.744 | 0.751 |

Two features the floor choice turns on. **The primary construct separates the field
much more sharply than the environment constructs** — 0.55→0.90 on violation+judgment
versus 0.60→0.86 on violation and a compressed 0.60→0.77 on outcome. And **Mistral and
Phi-4-mini are near the capable judges on `outcome` (0.759, 0.744) while far below on
the primary (0.679, 0.546)**: a floor set on an environment construct alone would
qualify judges the primary construct rejects.

### Candidate floor sets, per environment family

| set | criterion | qualifies | rejects |
|---|---|---|---|
| **A-1 permissive** | primary-construct external AUROC ≥ 0.70 | Qwen3.6, Llama-70B, gpt-4o | Mistral, gemma, Phi |
| **A-2 moderate** | primary ≥ 0.80 | Qwen3.6, Llama-70B, gpt-4o | Mistral, gemma, Phi |
| **A-3 strict** | primary ≥ 0.80 **and** violation ≥ 0.80 **and** outcome ≥ 0.70 | Qwen3.6, Llama-70B, gpt-4o | Mistral (outcome 0.759 passes, primary 0.679 fails), gemma, Phi |

**All three partition the field identically** on the judges tested. That is itself the
finding: the gap between the 35B–70B tier and the ≤7B tier is wide enough (0.679 →
0.876, a 0.20 jump) that the floor's exact placement inside it does not change the
roster. A-1 is therefore recommended on parsimony — a higher bar buys no additional
discrimination on current evidence and would be a tighter claim than the data
compels.

**Per-environment note:** the table pools both environments. Per-family AUROC differs
(hotpotqa separates classes ~3× more widely than alfworld, Part B), but no judge
changes side of any candidate floor when the families are split.

---

# (b) Qualification floors — CHARACTERIZATION STABILITY *(new dimension)*

> **Evidentiary status, stated verbatim as required.** This dimension rests on **one
> confirmation** (Llama stable → forecasts land) and **one refutation-of-instability**
> (Qwen unstable → forecasts miss). Both were registered before outcomes were seen.
> **n = 2 judges. Validation is open.** This is a proposal built on a two-point track
> record, and it is offered as such.

### The measurement (GATE-4 Part C)

| env | judge | max jackknife swing | slope | slope CI width | stable |
|---|---|---|---|---|---|
| alfworld | Llama-70B | 3.4 pts | −0.494 | 0.240 | yes |
| hotpotqa | Llama-70B | 1.2 pts | −0.614 | 0.207 | yes |
| hotpotqa | Qwen3.6 | 1.0 pts | −0.522 | 0.180 | yes |
| alfworld | Qwen3.6 | **11.7 pts** | −0.620 | **0.991** | **no** |

### The track record it rests on (GATE-4 Part A)

| judge | Part C verdict | Part A forecast error | beat V |
|---|---|---|---|
| Llama-70B | stable (3.4 / 1.2) | 0.0, 6.1, 2.8, 3.2 pts | 4/4 |
| Qwen3.6 | unstable on alfworld (11.7) | 4.7, 7.3, 10.1, 11.5 pts | 2/4 |

The stable judge's forecasts landed inside the ±8-point budget in 4 of 4 cells and beat
the verdict every time. The unstable judge exceeded the budget in 2 of 4 and lost to
the verdict twice. **That pattern is what P-A1 failing on 6/8 actually consists of.**

### Candidate criterion

| | |
|---|---|
| **B-1** | max jackknife swing ≤ **8 percentile points** (the measured flatness budget) **and** slope CI width ≤ **0.36** |

The 0.36 is the directive's "stable fits × 1.5": stable widths are 0.180–0.240, so
1.5 × 0.240 = 0.36. Under B-1, Llama qualifies in both environments, Qwen3.6 qualifies
on hotpotqa and **fails on alfworld** — a per-(judge, environment) verdict, not a
per-judge one.

**What B-1 would have predicted:** exactly the Part A outcome. It is not independent
evidence — it is the rule fitted to the two observations that motivated it.

---

# (c) Scope conditions — HARD PRECONDITIONS, not floors

These are not thresholds to clear; they bound where any qualified judge may be used.

1. **External-judge only.** Self-cells are excluded from fitting pools and from
   deployment. Basis: independence holds 9–10/11 arms under every construct; Part C's
   only unstable fit has the judge's own self-cell as its leverage point.

2. **Per environment family.** Fit and deploy within one environment. Part B shows
   conditional invariance holds on hotpotqa and fails on alfworld; Part D's
   cross-environment result is **no-claim** (−0.0024, CI [−0.0047, 0.0001] includes
   zero) and must not be read as licence to transfer.

3. **Interpolation only.** No deployment on a target outside the reference pool's
   capability range. Basis: the 27B extrapolation cell missed π* by **31–55 percentile
   points**, and the forecast cut lost to the verdict for Qwen3.6 on all three
   evaluable constructs. This is the strongest scope evidence in the gate.

4. **Label-free claims additionally require (b).** A deployment claiming no target
   labels must satisfy the stability criterion, not only discrimination. GATE-4's
   closure already scopes h to within-gate validation; condition 4 is what any future
   label-free claim would have to clear.

---

## What is NOT proposed

**No floor on *f*.** R1 failed on it and its ordering inverted; reusing it as the
incumbent would be the wrong reason.

**No floor on frontier/API status.** S5 measured that axis: gpt-4o (0.859 primary)
sits *below* both capable open judges and above the small tier. Model class does not
predict quality; scale tier does.

**No multi-judge selection rule.** Closed by the directive as named future work.

---

## The signature

Three separate decisions:

- **(a)** adopt A-1, A-2, A-3, or none.
- **(b)** adopt B-1 or none — knowing it rests on n=2 with validation open.
- **(c)** adopt scope conditions 1–4, or a subset.

On signature: floors freeze as a **new registration**, R1's FAIL remains in the
ledger, bundle assembly proceeds, and the rewrite begins.

**HALTED for author signature. Nothing downstream consumes these floors until signed.**
