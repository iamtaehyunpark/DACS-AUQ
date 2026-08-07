# GATE-4 SPEC (A34) — Is h Real? Forecast-First Validation and Mechanism Audit
## Untouched-target forecasts · conditional-invariance overlay · fit-stability audit · family-granularity probe

**2026-08-07 · Pre-registered before any arm is computed. Commit before running; record
sha in the manifest. This gate exists to answer one doubt, raised by the author and
sharpened in external review of the mechanism: h passed on the same 22 cells that
taught us to build it — attempt #3 in a sequence whose hypotheses were formed by
inspecting attempts #1–2's failures. Pre-registration bounded that risk; it cannot
zero it. The only fully convincing answer is prediction on data no gate has touched,
plus direct exhibition of the invariance h presupposes. That is this gate.**

## 0. Scope discipline

Everything here is per-(judge, environment). No cross-environment pooling anywhere
except Part D, whose entire purpose is to measure cross-environment failure. Labels:
L2, all constructs reported, primary violation+judgment (A30 §5.3, unchanged by A32).
Judges: capable stratum (Llama-3.3-70B, Qwen3.6-35B). Seed 13; 2000-draw bootstraps
where CIs are reported. Anchors in every table: V, S-fitted, and banked h numbers
from GATE-3.

## Part A — Forecast-first validation on untouched targets (the decisive part)

**A.1 Eligible targets.** Agents present in the labeled corpus but excluded from every
gate (pool-size exclusion; never used to fit, tune, or select any rule):
- alfworld: Qwen3.5-4B, Qwen3.5-9B, Qwen3.5-27B
- hotpotqa: Qwen3.5-4B, Qwen3.5-9B
Five (judge × target × env) forecasts per judge = 10 forecast cells.

**A.2 Score availability check (blocking).** Verify capable-judge P(True) scores exist
over these targets' frozen trajectories. If absent for any cell: size and run the
missing scoring pass FIRST (est. from measured online-prompt rate 3,300/5min; these
are online-length prompts, not hindsight-length), and only then proceed. Scores must
exist for all forecast cells before A.3 — partial forecasting invites selection.

**A.3 Forecast lock (the point of the protocol).** Using ONLY the already-fitted
per-(judge, env) h from GATE-3 (refit on the full 5–6 reference targets of that env —
no LOTO needed here since forecast targets are outside the reference set) and each
forecast target's UNLABELED mean-U:
1. Compute predicted optimal percentile π̂ = h(mean-U);
2. Compute the implied raw cut from the target's own unlabeled score distribution;
3. Predict resulting balanced accuracy BÂ via the reference targets' flatness curves
   (predicted BA = mean reference BA at π̂, with a ± band from the ±8-point flatness
   tolerance).
Write all 10 forecasts (π̂, cut, BÂ ± band) to `forecasts_A34.csv`, commit, record
sha. **Labels for forecast targets must not be read by any process before this
commit.** The commit timestamp is the evidence.

**A.4 Evaluation.** After the lock: score each forecast cell's realized optimal
percentile π*, realized BA at the forecast cut, and V / S-fitted anchors.

**A.5 Pre-registered success criteria.**
- P-A1: realized BA at the forecast cut ≥ V in ≥ 8/10 cells.
- P-A2: |π̂ − π*| ≤ 8 percentile points (the flatness budget) in ≥ 7/10 cells.
- P-A3: pooled capture over forecast cells ≥ 0.5 (same definition as GATE-3).
**PASS** = all three. **PARTIAL** = P-A1 only. **FAIL** otherwise. Note: the 27B cell
is a size extrapolation (larger than any reference target) — reported inside the
counts, and separately, since extrapolation failure is more informative than
interpolation failure.

## Part B — Conditional-invariance overlay (the mechanism exhibit)

For each (judge, env): overlay f(u | correct) and f(u | incorrect) across all matrix
targets (kernel density on logit scale + the 20-bin histograms), one panel per class
per (judge, env) — 8 panels. Quantitative companion: pairwise
1-Wasserstein distance between targets' class-conditionals, reported as a matrix,
with the between-CLASS distance as the scale reference.
**Pre-registered read:** CI supported iff median within-class between-target distance
< ⅓ of the class-separation distance, per (judge, env). Self-cells plotted but
excluded from the criterion (known self-leniency shifts the conditionals — their
visible deviation is a positive control, not a failure). If CI fails while Part A
passes, h works for a shallower reason — say so in the summary; do not soften either
result to fit the other.

## Part C — Fit-stability audit (the small-m objection, answered with numbers)

Per (judge, env) h-fit: (i) jackknife — drop each reference target, refit, report the
swing in predicted percentile at every other target's mean-U (max and median swing,
in percentile points, against the ±8 flatness budget); (ii) slope/intercept with
pairs-bootstrap CIs; (iii) leverage — identify any single target whose removal
changes any held-out prediction by > 8 points; name it in the summary if it exists.
**Pre-registered read:** the fit is called stable iff max jackknife swing ≤ 8 points
in ≥ 3 of 4 (judge, env) fits. Not a pass/fail gate on h — a required disclosure
beside Part A's verdict.

## Part D — Family-granularity probe (how badly does h itself break across envs)

Fit h on alfworld, apply to hotpotqa targets (and reverse), both judges, no pooling.
Report per-cell BA vs the within-env h, vs V, and the capture degradation. This
quantifies for h what was only measured for raw cuts (−0.035…−0.103, direction-
asymmetric). **No success criterion — this arm is expected to degrade**; its number
goes verbatim into the limitations section as the measured boundary of "per
environment family". If it unexpectedly transfers, that is reported as an anomaly
requiring its own follow-up, not claimed as a feature of this paper.

## Closure

Whatever Parts A–D return, no new rule variants are introduced in response (GATE-3
§6 closure stands). Outcomes map to the paper as: A PASS → §6d ships h with
forecast-validated provenance and Part B/C as its mechanism and disclosure; A
PARTIAL/FAIL → h's claim is scoped to "within-gate validation only," the §6d lead
reverts to the ~200-label tier, and the forecast miss is published as the honest
boundary. Floors (S8) freeze only after this gate.

## Deliverables

`forecasts_A34.csv` (committed pre-evaluation, sha in manifest) ·
`tables_gate4/` per-part tables, all constructs · `figures_gate4/` overlay panels +
Wasserstein matrices + jackknife swing plot · `GATE4_SUMMARY.md` — one page:
P-A1/2/3 with deciding numbers, CI criterion verdict, stability disclosure,
cross-env degradation numbers, and the single §6d provenance sentence.
