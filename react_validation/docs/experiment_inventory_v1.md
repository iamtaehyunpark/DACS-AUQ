# Experiment & Data Inventory — everything the paper needs, and what exists

**Taehyun Park · UW–Madison CS · v1, 2026-08-03**
Consolidates `handoff_v1.md` (E0–E6, D1–D9), `paper_B_proposal_v1.md` (§8.i–viii,
gates), and `paper_B_validation_status_v1.md` (audit against tracked data).
One row per experiment. Status is the *audit* status, not the plan status.

**Legend** — **A** auditable in this repo · **S** server-side, asserted in prose,
no artifact here · **P** partial · **—** not measured anywhere.

---

## 1. Experiments

| # | Experiment | Proves | Data needed | Status | What is actually missing | Gate |
|---|---|---|---|---|---|---|
| **E0** | Measurement bed (agent pool × env pool, volume, pre-registration) | infrastructure for all | D1, D2 | **S** | corpus not local (`result/` ~34 GB, `v1/data/` ~326 MB server-side); 3rd env, closed-frontier arm not built | — |
| **E1** | **Evidence law** — cumulative evidence ladder {action} → {+history} → {+reasoning} → {+realized obs}; permuted- and wrong-episode-history controls | Arg 1 (step quality is environment-relational) | D1, D3, D7 | **A**, scope-limited | run is a **self-diagonal** (Qwen3.6-35B-A3B probes its own trajectories), ALFWorld only, entangled only, n=300; no external-judge version; wrong-episode control never run | — |
| **E2** | **Metric map** — every intrinsic metric × agent × env; winner per cell; (a) no-universal bootstrap, (b) winner-variance decomposition | Arg 2 (no universal signal; preference is a stable model trait) | D1, D3, D6, D8 | **S** | no matrix, no per-arm table, no corpus tracked; meta-model baselines (D8) not built | — |
| **E3** | **Invariance test** — fixed judge, per-target recipe search vs globally-fixed recipe; adaptation curve on a **held-out agent** | **THESIS** (Arg 3) | D1, D3, D7 | **—** | **zero artifact of any kind.** ε not pre-registered. Second judge not run. Held-out-agent exclusion not defined | **2′** |
| **E4** | **Reading matrix** — assessor × target incl. self-diagonal; (i) peer/upward vs self, (ii) judge-size curve, (iii) loop-stratified non-triviality | Arg 4 (instrument should be external) | D1, D3, D6, D7, D2 | **S** for the 4/4 margin; **—** for (i)/(ii)/(iii) | 4/4 cross-probe output **not tracked** though `analysis/crossprobe_auroc.py` + `scripts/run_crossprobe_{qwen,mistral}.sh` exist; peer/upward cells not run; rung (b) never run *for the judge margin* | **2** |
| **E5** | **Human alignment** — judge-vs-gold vs self-vs-gold on identical steps, against the IAA ceiling; re-verification of every E3/E4 headline | Arg 5 (veridicality) | D4 | **—** | gold subset does not exist; no power analysis, no annotators, no IAA | **1** |
| **E6a** | **τ gating** — budget-vs-detection curves vs uniform inspection | Arg 6 (invocation policy) | D2 (τ), D7 | **—** | **no tracked artifact carries a τ column.** Gate 3 cannot even be previewed. NB: `analysis/backfill_tau.py` exists — verify before treating as unstarted | **3** (soft) |
| **E6b** | **Bias battery** — decoy-controlled rule injection; perturbation battery (order, format, length, position) | Arg 6 | D7 | **P** | decoy arm is the only element that exists; perturbation battery not run | — |
| **E6c** | **Cost card** — tokens/latency per check across judge sizes; adaptation cost; closed-frontier demo | Arg 6 | D9 | **A** (partial) | timing logged (job `64061a27`, ~9300 prefill tok/s, 3,300 probes ≈ 5 min / A100); no size sweep, no closed-frontier demo | — |
| **E-aux** | **Hindsight ceiling** — same judge, prefix-only vs full-trajectory | validity rule 2; §1 framing | D7 | **P** | horizon table is step-level *lookahead* (k=0…6), not prefix-vs-full-trajectory; aggregates only, no per-step data | — |
| **E-aux** | **Length confound** — length-only trajectory AUROC baseline | Paper A contribution 2; B's methodological floor | D1, D2 | **S** | asserted ≈1.0; no artifact. Horizon table shows trajectory-level U is *useless* (0.535) — adjacent, not the same thing | — |
| **E-aux** | **Failure-mode census** — loop/stagnation/cap error mass | E1 secondary; §1 receipt 5 | D2 | **S** | 40–87% range unsourceable from the ctxrule sample (stratified by construction) — cite the corpus arm or drop | — |
| **E-aux** | **Contamination check** — decoupled thought probes vs committed action | harness validity | D1 | **A** | done: mean \|ΔU\| 0.035 (P(True)), 0.017 (post-hoc numeric), corr 0.93–0.94 | — |

---

## 2. Data artifacts

| # | Artifact | Feeds | Status | Note |
|---|---|---|---|---|
| **D1** | Trajectory corpus — state, action, reasoning, observation, **agent logprobs**, **in-generation verbalized confidence** | everything | **S** | ~30k banked (4 families 4B–70B × ALFWorld + HotpotQA × 2 architectures); from-scratch target 80–120k over 6–8 agents × 3–4 envs. **Logprobs + in-generation confidence are unrecoverable after generation** — the suite's one irreversible decision |
| **D2** | Step metadata (mechanical): τ types, loop/stagnation flags, state predicates, cap events, outcomes | D3, E4(iii), E6a, census | **P** | error-type stratum is tracked in the ctxrule CSV; **τ is absent everywhere** |
| **D3** | Environment-verified labels — PRIMARY target for every headline number | all headlines | **—** | every local number is against 3-judge ensemble labels. ~101/150 errors in the ctxrule sample (`loop` + `inadmissible`) are re-anchorable with **no GPU** |
| **D4** | Human gold set — stratified ~1.5–3k steps, ≥2 annotators, adjudication, published IAA | E5, headline re-verification, calibration truth | **—** | not started. One annotation effort, three uses. The `other` stratum (49 steps in ctxrule) needs it |
| **D5** | Ensemble fill labels | corpus construction only | **A** (partial) | 3-judge votes tracked for 24 steps. **Never validates any judge** |
| **D6** | Intrinsic metric table | E2, E4 self-diagonal | **S** | self-probe rows ARE E4's self-diagonal — dedup, don't recompute |
| **D7** | Master probe tensor (assessor × target × env × step × evidence-condition × recipe × perturbation) | E1/E3/E4/E5/E6 are all slices | **P** | one slice tracked in full: `reports/tables/ptrue_ctxrule_e1b_n300_matrix.csv` (300 steps × 11 conditions, per-step U/label/stratum/task/step_idx). Full volume ~1.5–3M single-token probe calls |
| **D8** | Meta-model baselines | E2 | **—** | leak-proof split protocol over D3 not defined |
| **D9** | Cost/latency logs | E6c | **A** (partial) | byproduct of D7 runs |

**Dependency chain**: D1 → D2 → D3/D5 → D6, D7 → all analyses; D4 parallel after D1.
**Schedule-critical**: (1) D1's logging spec complete before the first episode;
(2) D7's search-sampling rule and E3's ε pre-registered before any scoring.

---

## 3. What is auditable off-server today

Exactly one experiment: the P(True) context/rule ablation, and it carries §1
receipts 1–2 and all of §4(a).

| tracked artifact | scope |
|---|---|
| `reports/tables/ptrue_ctxrule_e1b_n300_matrix.csv` | 300 steps × 11 conditions, **full per-step data** |
| `reports/tables/ptrue_ctxrule_e1b_n300.md` | 24 worst-shift steps, judge votes + prompts |
| `reports/PTRUE_CTXRULE_REPORT.md` | write-up |
| `figures/ctxrule/*.png` (6), `figures/ctxrule_n20/*.png` | n=300 figures + superseded n=20 pilot |
| `reports/tables/ptrue_horizon_e1b.md` | 120 steps × 7 horizons, **aggregates only** |
| `analysis/contamination_report.md` | 702 decoupled steps, aggregates |
| `reports/PILOT_REPORT.md`, `reports/HOTPOT_REPORT.md` | harness validation (behavioural) |

Everything else in both proposals is prose.

⚠️ `analysis/ctxrule_revalidation.py` — the script behind every new number in
`paper_B_validation_status_v1.md` and its one-command reproduction claim — is
**untracked**, as are all five docs in `docs/`. Its input CSV is tracked.

---

## 4. Ordered by return on effort

| # | Task | Cost | Unblocks |
|---|---|---|---|
| 1 | **Pre-register ε, scoped to ranking** | none (a decision) | gate 2′ has no criterion without it. Thresholds already fail to transfer *within one judge and one agent* (−0.247 bal. acc, C6) — a threshold-inclusive gate risks failing for reasons unrelated to the thesis |
| 2 | **E3 prober × agent matrix** | GPU; `crossprobe_auroc.py` exists | **the thesis gate, with zero data.** Track output in `reports/tables/` so the invariance table is auditable off-server |
| 3 | **Gate 1 on the ctxrule sample** | **no GPU** | re-label `loop` + `inadmissible` from environment state; converts the one auditable experiment from judge-anchored to partly environment-anchored, and pre-tests the firewall |
| 4 | **External-judge grid rerun** | ~5 min A100 per judge | same 300 steps, 11 conditions, non-Qwen judge → turns E1 from self-diagonal into §8(ii), and previews gate 2′ cheaply |
| 5 | **Loop-stratify the 4/4 cross-probe margins** | code exists (§3 of validation doc) | rung (b) for *instrument selection* (currently only run for the grid) |
| 6 | **Add τ to exported matrices** | schema change, not an experiment | gate 3 is otherwise unevaluable. Check `backfill_tau.py` first |
| 7 | **D4 gold subset** | annotation effort | E5, headline re-verification, and the `other` stratum of gate 1 |

**Checkpoint 2026-08-14**: gates 1, 2, 2′ decidable on tasks 1–3 + 5 alone.

---

## 5. Rung-(b) status — the credibility split

Loop stratification has been run **for the evidence grid only**. It splits:

- **Realized-observation row passes decisively.** +0.121 on non-loop errors vs
  +0.072 pooled; +0.145 vs plain-correct only; not significant on loop errors
  alone (+0.026). The load-bearing cell is the `other` stratum: 0.790 vs 0.716.
- **Targeted-rule row fails.** +0.132 on loop errors, **+0.006 (n.s.)**
  elsewhere; 0.724 vs 0.716 on `other`. The honest claim: *the realized row is
  a general signal; the prior row is a targeted detector.*
- The `inadmissible` 0.983 is partly mechanical (the observation is literally
  `Nothing happens.`) — report as such.

The analogous test for the **external-judge margin** (E4.iii, gate 2) has not
been run. Encouraging ≠ sufficient.

---

## 6. From-scratch delta (scoping decision pending)

Beyond the banked design, `handoff_v1.md` adds: a 3rd+ environment (tool-use /
web); a closed-frontier agent arm; a second judge in E3; the held-out-agent
adaptation test; wrong-episode controls in E1; powered human-label sizing; E4
peer/upward cells; E6a curves; the full battery.

**Kill-order under resource pressure**: survivable without E6b's full battery
and with 3 environments; **not** survivable without E3, E4(iii), or E5's
re-verification.
