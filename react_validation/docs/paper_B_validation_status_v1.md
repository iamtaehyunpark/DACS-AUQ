# Paper B — proposal validation against existing data

**Taehyun Park · UW–Madison CS · v1, 2026-08-03**
Companion to `docs/paper_B_proposal_v1.md` (v3, amortized-metrology reframe).

What this document does: take every empirical claim Paper B makes, check it
against the data that actually exists **in this repository**, and say plainly
which claims are auditable today, which are asserted from server-side runs, and
which have no artifact at all. Where the tracked data supported a new analysis
the proposal calls for but has not yet run, that analysis was run here.

All new numbers come from `analysis/ctxrule_revalidation.py`, which reads only
`reports/tables/ptrue_ctxrule_e1b_n300_matrix.csv`. One command reproduces them.

---

## 1. What data exists, and where

The repository tracks summaries; the raw corpus does not live here.
`.gitignore` states it: `react_validation/result/` is ~34 GB of run logs, probe
records and judge output kept on the experiment server, and `v1/data/` is
another ~326 MB. Neither is present on this machine — `result/`, `runs/`,
`data/` and `v1/data/` do not exist locally.

| artifact | scope | status |
|---|---|---|
| `reports/tables/ptrue_ctxrule_e1b_n300_matrix.csv` | 300 steps × 11 conditions, per-step U, label, stratum, task, step_idx | **full per-step data, tracked** |
| `reports/tables/ptrue_ctxrule_e1b_n300.md` | same run, 24 worst-shift steps with judge votes and prompts | tracked (excerpt) |
| `reports/PTRUE_CTXRULE_REPORT.md` | the write-up of that run | tracked |
| `figures/ctxrule/*.png` (6) + `figures/ctxrule_n20/*.png` | n=300 figures and the superseded n=20 pilot | tracked |
| `reports/tables/ptrue_horizon_e1b.md` | 120 steps × 7 hindsight horizons, aggregates only | tracked (no per-step data) |
| `analysis/contamination_report.md` | 702 decoupled steps, full-vs-trimmed thought probes | tracked (aggregates) |
| `reports/PILOT_REPORT.md`, `reports/HOTPOT_REPORT.md` | harness validation, ALFWorld 10-ep and HotpotQA 100-q | tracked (behavioural) |
| transfer matrix, prober × agent matrix, ~30k labeled steps, sample-efficiency curves, 4/4 cross-probe arms | Paper A + Paper B headline claims | **no artifact in the repo** — server-side |

So: **one experiment is fully auditable here** (the P(True) context/rule
ablation), and it is the one the proposal leans on for §1's receipts 1–2 and
all of §4(a). Everything else is currently prose.

An important scoping fact that the proposal does not currently state: this run
is a **self-diagonal**. The prober is Qwen3.6-35B-A3B and the agent that
produced the frozen trajectories is Qwen3.6-35B-A3B. The evidence grid has
therefore been characterized only for the judge-equals-agent cell, on one
benchmark (ALFWorld), one arm (entangled), one model. §8(ii) asks for the grid
"under external judges" — that has not happened yet.

---

## 2. Reproduction check

Every headline number in `PTRUE_CTXRULE_REPORT.md` reproduces from the tracked
CSV, independently recomputed (AUROC with the positive class = judge-incorrect,
95% CIs from a 10k trajectory-clustered bootstrap over 111 episodes):

| condition | AUROC (report) | AUROC (recomputed) | ΔAUROC vs production |
|---|---|---|---|
| C0/R0 task + action | 0.512 | 0.512 [0.439, 0.586] | −0.229 |
| C1/R0 + last observation | 0.622 | 0.622 [0.559, 0.685] | −0.119 |
| C2/R0 + full history | 0.697 | 0.696 [0.636, 0.755] | −0.045 n.s. |
| **C3/R0 production** | 0.741 | 0.741 [0.676, 0.801] | — |
| C4/R0 no action | 0.740 | 0.739 [0.672, 0.802] | −0.002 n.s. |
| C5/R0 + realized outcome | 0.813 | 0.813 [0.758, 0.866] | **+0.072 [+0.007, +0.138]** |
| C6/R0 + outcome + next step | 0.845 | 0.845 [0.797, 0.890] | **+0.103 [+0.046, +0.164]** |
| C3/R1 generic rubric | 0.804 | 0.804 [0.749, 0.856] | **+0.063** |
| C3/R2 targeted rule | 0.813 | 0.813 [0.754, 0.868] | **+0.072** |
| C3/R3 decoy rule | 0.728 | 0.728 [0.664, 0.788] | −0.014 n.s. |
| C0/R2 rule, no history | 0.531 | 0.531 [0.457, 0.603] | −0.211 |

No discrepancies. The C5 delta prints as +0.072 here against +0.070 in the
report — bootstrap seed, not a difference in the estimate.

---

## 3. New result: the loop-stratified decomposition (§8.iii), run for the first time

Paper B pre-registers loop stratification as the test of whether a gain is a
real signal or degenerate-regime detection (§6 rung (b), §8.iii). It has never
been run on the evidence grid. The tracked CSV carries the error-type stratum
per step, so it can be run now.

Positive class held fixed at 150 correct steps; the error pool is split.

| condition | all errors (150) | **non-loop errors (72)** | loop errors (78) | non-loop errors vs plain-correct only (72 v 105) |
|---|---|---|---|---|
| C2/R0 history only | 0.696 | 0.659 (**−0.072** vs prod) | 0.732 (−0.020 n.s.) | 0.615 (−0.089) |
| **C3/R0 production** | 0.741 | 0.730 | 0.752 | 0.704 |
| **C5/R0 realized outcome** | 0.813 (+0.072) | **0.851 (+0.121 [+0.042, +0.207])** | 0.778 (+0.026 **n.s.**) | **0.849 (+0.145 [+0.064, +0.235])** |
| C6/R0 outcome + next step | 0.845 (+0.103) | 0.816 (+0.086) | 0.871 (+0.119) | 0.808 (+0.105) |
| C3/R1 generic rubric | 0.804 (+0.063) | 0.778 (+0.047) | 0.829 (+0.077) | 0.772 (+0.068) |
| **C3/R2 targeted rule** | 0.813 (+0.072) | **0.737 (+0.006 [−0.035, +0.051], n.s.)** | **0.884 (+0.132)** | 0.750 (+0.046) |
| C3/R3 decoy | 0.728 (−0.014) | 0.716 (−0.014 n.s.) | 0.739 (−0.013 n.s.) | 0.680 (−0.024 n.s.) |

Two findings, and they point in opposite directions:

**(a) The realized-observation row passes rung (b) — decisively.** The C5 gain
is not loop detection. It is *larger* on non-loop errors (+0.121) than pooled
(+0.072), and larger still against plain-correct steps only (+0.145). On loop
errors alone it is not significant (+0.026). The environment's response to the
action is exactly what a repetition heuristic cannot give you, and the numbers
say so. Per-stratum AUROC against all 150 correct steps:

| error stratum | n | production | C5 outcome | C6 | R1 | R2 |
|---|---|---|---|---|---|---|
| `loop` | 78 | 0.752 | 0.778 | 0.871 | 0.829 | **0.884** |
| `other` (wrong inference, out-of-order) | 49 | 0.716 | **0.790** | 0.781 | 0.751 | 0.724 |
| `inadmissible` | 23 | 0.761 | **0.983** | 0.890 | 0.836 | 0.764 |

The 0.983 on `inadmissible` is partly mechanical — the realized observation is
literally `Nothing happens.` — and should be reported as such rather than as
judgement. The load-bearing cell is `other` at 0.790 vs 0.716: on the stratum
with no environmental tell and no repetition tell, the realized observation
still adds +0.074.

**(b) The targeted-rule row fails rung (b).** R2's headline +0.072 is entirely
loop detection: +0.132 on loop errors, **+0.006 (n.s.)** on everything else,
and 0.724 vs 0.716 on the `other` stratum. Paper B §4(a) currently presents
"a **relevant** rule adds discrimination (+0.072, beating a decoy floor by
+0.086)" as an established grid finding. On this data the honest statement is
narrower: *a rule that names a specific degenerate failure mode detects that
failure mode, at a false-positive cost on the correct steps that superficially
resemble it, and adds nothing elsewhere.* The false-positive side is unchanged
and confirmed — R2 raises U on legitimate revisits (which are correct) by a
median +0.155, 93% of them.

This is a strictly better result for the paper than the current wording. It
converts a soft "rules help but cost something" into a sharp,
pre-registered-test-shaped claim: **the evidence grid's realized row is a
general signal; the prior row is a targeted detector.** That is a real evidence
hierarchy, which is what §4(a) is supposed to deliver.

---

## 4. New result: recipe transfer is a ranking property, not a threshold property

Paper B §7 defines the thesis gate on "the fixed judge's best elicited recipe
(probe format, evidence rows, calibration) stay[ing] stable". The tracked data
lets us test how those three components behave when only the *evidence row*
changes, holding judge and agent fixed. They behave very differently.

**Ranking is moderately stable; the operating point is not.** Spearman ρ
between the production probe's step scores and the other contexts:

| vs production | ρ | reading |
|---|---|---|
| C3/R3 decoy rule | +0.935 | a stated-but-irrelevant rule barely moves the ordering |
| C3/R1 generic rubric | +0.905 | |
| C3/R2 targeted rule | +0.863 | |
| C4/R0 no action | +0.842 | the action string is nearly inert |
| C2/R0 history only | +0.681 | |
| C5/R0 realized outcome | +0.570 | new evidence genuinely reorders steps |
| C6/R0 outcome + next step | +0.514 | |
| C0/R0 action only | +0.326 | |

**A threshold does not survive a change of evidence row.** Tuning the decision
threshold on the production prompt (Youden J, U ≥ 0.182) and applying it
unchanged to another context costs balanced accuracy:

| context | own-threshold bal. acc | production-threshold bal. acc | loss |
|---|---|---|---|
| C4/R0 | 0.673 | 0.660 | −0.013 |
| C3/R1 | 0.753 | 0.667 | −0.087 |
| **C5/R0** | 0.793 | 0.657 | **−0.137** |
| **C3/R2** | 0.770 | 0.617 | **−0.153** |
| **C6/R0** | 0.790 | 0.543 | **−0.247** |

C6 illustrates the mechanism: it has the best ranking of any condition (0.845)
and the worst threshold transfer (−0.247), because it compresses the scale —
correct steps move up with the errors. Mean U by condition ranges from 0.367
(production) to 0.731 (C0), so a fixed cut point is meaningless across rows.

**Consequence for gate 2′, which is worth deciding before the matrix runs.**
"Recipe invariance" must be defined at the level it can hold: *the same probe
format and the same evidence rows rank steps consistently across probed
agents*, with the operating point re-fit locally. If the gate is stated as
including the threshold, it is at risk of failing for a reason that has nothing
to do with the thesis — we can already see a fixed threshold breaking across
evidence rows *within a single judge and a single agent*. The proposal's own
§4 cost paragraph already concedes this ("local recipe calibration saturates at
~200 labeled steps"); §7's gate wording should match it.

**And local calibration is cheap — cheaper than claimed.** Tuning the threshold
on *k* random labeled steps and evaluating on the held-out remainder:

| k | held-out balanced accuracy | % of the all-300-step-tuned ceiling (0.677) |
|---|---|---|
| 25 | 0.643 ± 0.021 | 95.1% |
| 50 | 0.646 ± 0.015 | 95.4% |
| 100 | 0.642 ± 0.020 | 94.9% |
| 200 | 0.636 ± 0.037 | 94.0% |

Flat from k=25. The "~200 labeled steps" figure in §4 is conservative on this
task — good news for the amortization argument, and a cheaper deployment story
than the proposal currently tells.

---

## 5. The hindsight horizon (`ptrue_horizon_e1b.md`) — support for the τ policy

Aggregates only (no per-step data tracked), 120 steps × 7 horizons:

- Step-level AUROC by lookahead: k=0 **0.688** → k=1 **0.783** → k=2 0.740 →
  k=3 0.691 → k=4 0.742 → k=5 0.683 → k=6 0.650. The value is concentrated at
  **exactly one step** and decays after. That is a direct receipt for §4(b)'s
  reversible-step policy: assess post-observation at one-step latency, and buy
  no more lookahead than that. It also independently corroborates C5 > C6 as
  the cleaner instrument.
- Trajectory-level: U₀ predicts episode failure at **0.535**; full hindsight
  U_K at 0.480; ΔK at 0.419; the slope at 0.434 — all at or below chance.
  Within-half analysis is likewise null (ΔK AUROC 0.337 and 0.482). This
  supports the proposal's decision to keep trajectory-level aggregation out of
  scope, and it is a second, independent instance of the §2 methodological
  floor (step-level or nothing).

Caveat carried from the source table: k≥1 is not causally available online.
These bound what the cue is worth, not a deployable detector.

---

## 6. Claim-by-claim status

Legend: **A** = auditable in this repo · **S** = server-side, asserted in prose,
no artifact here · **—** = not yet measured anywhere.

| § | claim | status | note |
|---|---|---|---|
| 1.1 | action string alone is chance (0.512) | **A** | reproduced exactly |
| 1.2 | history 0.512→0.697; realized obs largest single gain (+0.070); reasoning dispensable | **A** | reproduced; see wording fix below |
| 1.3 | τ typing supplies invocation/evidence policy | **—** | τ is not in any tracked artifact; the CSV has no τ column |
| 1.4 | prefill + 1 token; 3,300 assessments ≈ 5 min on one A100 | **A** | logged in the report (job `64061a27`, ~9300 prefill tok/s) |
| 1.5 | loops/stagnation/cap carry 40–87% of error mass | **S** | locally: loop = 78/150 = 52% of the sampled error pool, but the sample is *stratified by design*, so it cannot establish the mass |
| 1.6 | consequence-anchored ground truth | **partial** | 3-judge votes are tracked for 24 steps; the environment-anchored recomputation has not run |
| 2 | non-transfer across 4 families × 2 benchmarks, ~30k steps; recipe transfer −0.10; P(True) best/tied 7/8, transfers at −0.016 | **S** | no matrix, no per-arm table, no corpus in the repo |
| 2 | length-only trajectory AUROC ≈ 1.0 | **S** | horizon table shows trajectory-level U is *useless* (0.535), which is adjacent evidence but not the length confound |
| 4a | evidence grid characterized, decoy-controlled | **A** | but self-diagonal only, one arm, one benchmark |
| 4a | relevant rule adds discrimination (+0.072 over decoy floor +0.086) | **A, needs restating** | §3(b) above: the gain is loop-specific (+0.006 n.s. off-loop) |
| 4a | rules manufacture false positives (+0.155 on revisits) | **A** | confirmed, 42/45 steps |
| 4b | cost of irreversibility ≈ 0.07 AUROC upper bound | **A** | = the C5 gain; §3(a) now sharpens it to +0.121 on non-loop errors |
| 4b | τ-gated invocation, budget-vs-detection curves | **—** | not run |
| 4 | local calibration saturates ~200 steps (96–99.9% retention) | **A (adjacent)** | threshold saturates by k=25 at 95% here |
| 5 | environment-anchored / gold recomputation (gate 1) | **—** | every local number is against 3-judge ensemble labels |
| 6 | external judge beats self-best 4/4 arms, +0.02 to +0.28 | **S** | `analysis/crossprobe_auroc.py` and `scripts/run_crossprobe_{qwen,mistral}.sh` exist; **no output is tracked** |
| 6 | rung (b) non-degeneracy of the instrument-selection margin | **—** | not run for the judge margin; §3 runs the analogous test for the grid |
| 7 | judge-recipe invariance across probed agents (**the thesis gate**) | **—** | **no artifact of any kind.** The single most load-bearing result has zero data here |
| 8.v | veridicality vs human gold | **—** | gold subset not tracked |
| 8.vi | hindsight ceiling | **partial** | the horizon table is a prefix-vs-lookahead ceiling at step level; §8.vi asks for prefix-only vs full-trajectory |
| 8.vii | bias battery | **—** | not run; the decoy arm is its only existing element |

Supporting infrastructure that *is* validated locally: the ReAct migrations
(ALFWorld pilot, HotpotQA EM 0.21/100 with 0 crashes), and the contamination
check showing the decoupled thought probes are not materially contaminated by
the committed action (mean |ΔU| = 0.035 for P(True), 0.017 for post-hoc
numeric; corr 0.93–0.94).

---

## 7. Gate readiness

| gate | what it needs | evidence here | read |
|---|---|---|---|
| **1 — circularity** | headline margins survive environment-anchored recomputation | none | **Untested.** Every local number uses judge labels. Mitigating: two of three error strata (`loop`, `inadmissible`) are environment-derivable, so ~101/150 errors in the ctxrule sample could be re-anchored today without new GPU time. The `other` stratum (49) is the one that will need the gold subset. |
| **2′ — invariance (thesis gate)** | judge recipe stable across probed agents | none | **The critical gap.** Nothing in the repo speaks to it. §4 above suggests the gate should be *scoped to ranking*, since thresholds demonstrably do not transfer even within one judge. |
| **2 — instrument credibility, rung (b)** | margin is not purely loop detection | analogous test passes for the evidence grid | **Encouraging, not sufficient.** C5's gain is non-degenerate; whether the *external-judge* margin is, is a different measurement. |
| **3 (soft) — τ** | gating curves show a knee vs uniform | none; τ absent from all tracked artifacts | **Untested**, and the horizon table's k=0→1→2 shape is the only indirect support for the pre/post split. |

---

## 8. Recommended edits to `paper_B_proposal_v1.md`

1. **§4(a) rule sentence.** Replace "a **relevant** rule adds discrimination
   (+0.072, beating a decoy floor by +0.086)" with the stratified version: the
   gain is +0.132 on the failure mode the rule names and +0.006 (n.s.)
   elsewhere. Keep the decoy floor and the revisit false-positive rate. This is
   a stronger, more falsifiable claim, and it makes the grid's internal
   hierarchy (realized row = general; prior row = targeted) an actual result.
2. **§1 receipt 2 and §2, "largest single gain".** +0.070 is the largest gain
   *beyond the production prompt*; history is a larger gain (+0.184, C0 → C2)
   and C6 is numerically larger (+0.103). Add the qualifier.
3. **§7 gate wording.** Scope invariance to probe format and evidence rows —
   ranking-level — with calibration explicitly local. §4's cost paragraph
   already says this; §7's gate should not silently require more.
4. **§4 calibration cost.** "~200 labeled steps" can be tightened; on the one
   task measured, the threshold saturates by 25.
5. **§4(a) scope disclosure.** State that the grid is currently characterized
   on the self-diagonal (Qwen probing Qwen), one benchmark, entangled arm. §8(ii)
   already promises the external-judge version; the proposal should not read as
   though it has been done.
6. **§1 receipt 5.** The 40–87% error-mass figure cannot be sourced from the
   ctxrule sample (which is stratified by construction). Cite the corpus arm it
   comes from, or drop the range.

## 9. What to run next, in order of return on effort

1. **Gate 2′ — the prober × agent matrix.** The thesis gate has no data. Nothing
   else in the plan matters as much, and `analysis/crossprobe_auroc.py` already
   exists. Track its output in `reports/tables/` so the invariance table is
   auditable off-server the way the ctxrule matrix is.
2. **Gate 1 on the ctxrule sample — nearly free.** Re-label the `loop` and
   `inadmissible` strata from environment state (repeated (action, observation)
   pairs; `Nothing happens.`) and recompute §2 and §3. No GPU. It converts the
   one fully auditable experiment from judge-anchored to partly
   environment-anchored and pre-tests the firewall before the headline arms.
3. **Rerun the grid with an external prober.** Same 300 steps, same 11
   conditions, a non-Qwen judge. ~5 min of A100 time per judge by the report's
   own timing. This turns the grid from self-diagonal into the §8(ii) result and
   gives a second data point on whether the grid recipe is agent-invariant —
   i.e. a cheap partial preview of gate 2′.
4. **Loop-stratify the 4/4 cross-probe margins** with the code in §3 of this
   document, to settle rung (b) for instrument selection rather than for the grid.
5. **Track τ.** No tracked artifact carries a τ column, so gate 3 cannot be
   evaluated or even previewed. Adding τ to the exported matrices is a schema
   change, not an experiment.

---

**Reproduce everything new in this document:**

```bash
python3 analysis/ctxrule_revalidation.py
```

Reads `reports/tables/ptrue_ctxrule_e1b_n300_matrix.csv` only. 10k
trajectory-clustered bootstrap resamples, fixed seed, ~4 min on CPU.
