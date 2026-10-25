# GATE-4 SUMMARY (A34) — Is h Real? Forecast-First Validation and Mechanism Audit

**2026-08-10 · Spec `docs/specs/GATE4_SPEC_A34.md` · Parts A–D reported together**
**Labels L2, primary construct violation+judgment, capable judges, seed 13.**

---

## Forecast lock (mandatory line, spec §A.3)

| | |
|---|---|
| lock commit | `5a4938fd841a823c1023e10c7383fe20fde9cec8` |
| lock timestamp | 2026-08-10T09:12:40+09:00 |
| `forecasts_A34.csv` sha256 | `69b926a0a70608ed77d24515d3421645c59f016c3ac168535a4674cf2091156c` |
| forecasts sealed | 20 (10 cells × 2 variants) |
| evaluation run | after the lock commit |

The seal was computed by a code path (`gate4_partA.py --seal`) that is **never handed a
label file**. The lock is therefore structural, not a promise: the function that
produced π̂ cannot read an outcome. All 10 forecast cells were scored and passed the
A35 answer-distribution audit (100% U parse rate, Yes/No only, max single-token share
0.90) **before** sealing, satisfying spec §A.2's blocking condition — no partial
forecasting, no selection.

**Defect in the seal, disclosed:** both sealed variants are in fact **h-noself**. The
reference set is read from `crossprobe/<ds>/<target>/`, and the cross-probe pipeline
skips the diagonal, so the judge's own cell was never present to be dropped. GATE-3's
h **did** include self-cells. The h-primary forecast was therefore never sealed, and it
cannot be sealed now that outcomes are visible. Everything below is a validation of
**h-noself** — a registered A34.1 variant, so this is a real result, but it is not the
h-with-self that GATE-3 validated.

---

## Part A — forecast-first validation (the decisive part)

### Primary construct (violation+judgment), 8 of 10 cells evaluable

| prediction | result | bar | outcome |
|---|---|---|---|
| **P-A1** realised BA at forecast cut ≥ V | **6/8** | ≥ 8/10 | **fails** (6 < 8 strictly; 75% < 80% proportionally) |
| **P-A2** \|π̂ − π*\| ≤ 8 percentile points | **6/8** | ≥ 7/10 | passes proportionally (75% > 70%), fails strictly |
| **P-A3** pooled capture | **0.750** | ≥ 0.5 | **passes** |

**VERDICT: FAIL.** Spec §A.5 defines PASS as all three and PARTIAL as P-A1 alone.
P-A1 fails under both the strict and the proportional reading, so the x/10-versus-x/8
denominator question does not change the outcome.

Two of the ten cells (`alfworld/Qwen3.5-27B`, both judges) are unevaluable on this
construct: the 3-judge ensemble never ran on that arm, so `judgment` has zero labels
and the composite collapses to 763 positives with no negatives.

### Per-cell, primary construct

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

The failure is **judge-asymmetric**. Llama-70B forecasts land at 0.0–6.1 points and
beat V in 4/4. Qwen3.6 forecasts land at 4.7–11.5 points and lose to V in 2/4. Both
of Qwen3.6's losses are narrow (0.010 and 0.001), but they are losses, and they are
what takes P-A1 below its bar.

### The 27B extrapolation cell, reported separately (spec §A.5)

Unevaluable on the primary construct; recovered on the environment-labelled
constructs, where the forecast is scored against a different yardstick than the one it
was fitted for.

| construct | judge | π̂ | π* | BA@cut | V |
|---|---|---|---|---|---|
| violation | Llama-70B | 0.636 | 0.323 | 0.658 | 0.562 |
| violation | Qwen3.6 | 0.709 | 0.392 | 0.641 | **0.670** |
| outcome | Llama-70B | 0.636 | 0.265 | 0.574 | 0.521 |
| outcome | Qwen3.6 | 0.709 | 0.162 | 0.584 | **0.598** |
| y_env | Llama-70B | 0.636 | 0.263 | 0.595 | 0.526 |
| y_env | Qwen3.6 | 0.709 | 0.230 | 0.599 | **0.622** |

**Extrapolation degrades sharply.** π̂ misses π* by 31–55 percentile points on a target
larger than any reference. Llama's cut still beats V; Qwen3.6's does not. Spec §A.5
anticipated that extrapolation failure is more informative than interpolation failure,
and this is that failure, measured.

### Other constructs (spec §1: all constructs reported)

| construct | cells evaluable | P-A1 | pooled capture |
|---|---|---|---|
| violation+judgment (primary) | 8 | 6/8 | 0.750 |
| judgment | 8 | 6/8 | 0.782 |
| violation | 10 | 7/10 | 0.472 |
| outcome | 10 | 7/10 | 0.328 |
| y_env | 10 | 7/10 | 0.321 |

**P-A2 is not reported for the non-primary constructs and must not be read from them.**
π̂ predicts the optimal percentile *of the primary construct's labelling*; comparing it
to another construct's π* measures a different quantity, and it duly collapses (2/10,
0/10, 0/10). That is an artefact of the comparison, not evidence about h.

---

## Part B beside Part A — no reconciliation (spec §3)

| env | judge | within-median | class separation | ratio | CI supported |
|---|---|---|---|---|---|
| alfworld | Llama-70B | 6.375 | 7.880 | 0.809 | **no** |
| alfworld | Qwen3.6 | 1.239 | 3.404 | 0.364 | **no** |
| hotpotqa | Llama-70B | 1.850 | 11.410 | 0.162 | **yes** |
| hotpotqa | Qwen3.6 | 0.585 | 3.869 | 0.151 | **yes** |

Conditional invariance holds on hotpotqa and fails on alfworld. Part A also failed.
**The two results are reported side by side and are not reconciled.** Where Part A
succeeded per-cell it did so most clearly on Llama/hotpotqa — the same (judge,
environment) where CI holds — but this gate does not claim that as a mechanism, and no
statement here softens either result to fit the other.

## Part C — fit stability (disclosure)

3 of 4 fits stable against the ±8-point budget (max jackknife swing 3.4 / 1.2 / 1.0).
The exception is **alfworld/Qwen3.6 at 11.7 points**, leverage target = its own
self-cell, slope CI 5× wider than the others. Qwen3.6 is also the judge whose Part A
forecasts miss widest. Recorded as a disclosure beside Part A's verdict, not as its
explanation.

## Part D — cross-environment h (no success criterion)

Mean **−0.0024** balanced accuracy over 22 cells, CI [−0.0047, 0.0001], which includes
zero. Reported as **no-claim**: consistent with no degradation, not claimed as
transfer. Raw cuts degraded −0.035 to −0.103 on the same test.

---

## Closure (spec §Closure)

Part A returned **FAIL**, so per the pre-registered mapping:

> h's claim is scoped to **within-gate validation only**, the §6d lead reverts to the
> **~200-label calibrated tier**, and the forecast miss is published as the honest
> boundary.

No new rule variants are introduced in response — GATE-3 §6 closure stands.

**Sentence §6d leads with:** *a step-level operating point can be calibrated from
roughly 200 labelled episodes on the deployment target; placing it without target
labels was attempted three ways, and the one rule that passed within-gate did not
survive forecast-first validation on untouched targets.*

The floors decision (S8) proceeds on this outcome.
