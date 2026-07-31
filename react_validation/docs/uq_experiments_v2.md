# Experimental Specification — **V2 (post-pivot)**
## Stage-Separated, Action-Typed Uncertainty Measurement in LLM Agents

**Version:** 2.0 · 2026-07-21 · supersedes `uq_experiments.md` (v1 retained)
**Companion:** `uq_theory_v2.md` · Written for the CLI coding agent: decisions are
stated as decisions.

**Pivot in one line:** decoupled inference is the primary coordinate system; the
headline is a **metric-by-stage-by-type map** (not "Cell D beats Cell A"); entangled
generation is a theory-loaded ablation (H4); the promise check is the map's delta
column; no metric is privileged a priori.

---

## A. Amendment Log (dated; all pre-data for the full runs — smoke ≠ data)

| # | Date | Amendment |
|---|---|---|
| A1 | 07-18 | Verbalized := in-generation (definitional); post-hoc probes are a separate class; strip-before-pass invariant (handoff doc) |
| A2 | 07-19 | Targeted elicitation: q_t (thought) and g_t / u_A(g_t) (action) |
| A3 | 07-20 | Loop findings: environment-side loop definition; loop-collapse covariate; loop-stratified reporting; dedup sensitivity |
| A4 | 07-21 | **Seed policy: per-step** (`seed = 1000 + task_index*1000 + step_idx`), adopted jointly for E0-full and E1 |
| A5 | 07-21 | **Pivot**: E-series restructured; v1 outcome table replaced by H1–H4 + new kill switch |
| A6 | 07-21 | Metric roster frozen (§0.6): +MaxTE, +P(True) (canonical rename of yes/no), PPL≡LN-NLL aliased, +u_A(g_t) |
| A7 | 07-21 | Judge rendering `include_thought: false` (architecture-invariant labels); E0 sample stratified τ × loop × architecture |
| A8–A13 | 07-22 | Pilot-review fixes (see `handoff_pilot_fixes.md`): thought contract de-actioned + trim rule; in-gen elicited class both arms (AUQ verbatim, thoughts-in-history entangled); u_A(g_t) single tag; continuation-repair; τ inline + backfill; bookkeeping |
| A14 | 07-22 | **E0 v3**: three-API-judge ensemble + human adjudication of disagreements = final annotation; no separate audit arm; local judge dropped from headline labeling |
| A15 | 07-22 | Both arms act/obs-only history; entangled = joint call + AUQ-style in-gen ĉ, no retention (not "AUQ System-1"); targeted probes decoupled-only by design; H4 sharpened to single-axis contract contrast; retention arm shelved; entropy-direction prediction withdrawn from freeze |
| A16 | 07-22 | Format-native contracts (plain labels, no XML): THOUGHT_TARGET + targeted THOUGHT_CONFIDENCE = u(q_t) restored in-gen (E3 anchor); ACTION_CONFIDENCE = u_A(g_t); one in-gen label per stage; roster rows 5–6 amended accordingly |
| A17 | 07-22 | Seed formula = harness/audit version: `1000 + task*100000 + step*100 + call_offset` |
| A18 | 07-22 | Specs committed into the repo; freeze tag valid only after spec–code reconciliation (this document at this revision) |
| A19 | 07-22 | u⁺ contract: probe-style value-excised call on the declared q_t (never agent-context continuation); provenance field split (`U_T_targeted_ingen` / `_posthoc` / `_uplus`); E3 reports mixed- and same-provenance deltas; continuation-repair demoted to fallback (smoke: 100% first-pass label compliance) |

Post-freeze changes = dated deviation notes, never silent edits.

---

## §0 Global Setup

### 0.1 Models and serving
| Role | Model | Notes |
|---|---|---|
| Primary agent | Qwen3.6-35B-A3B (instruct) | decides H1–H4; full E-series |
| Sweep, upper | largest servable Qwen (80B-class) | winning contrasts only |
| Sweep, floor | Qwen ~4B | deliberately below AUQ's ~7B verbalization threshold — measures the capability boundary |
| Judges (A14) | three API judges, three families, versions pinned | **all disjoint from the Qwen agent family**; identical rendering + rubric; ensemble votes released with corpus |
| (dropped) | local Llama judge | not used for headline labels; optional sweep relabeler only |

vLLM; sampling one config everywhere: `temperature=0.7, top_p=0.95, max_tokens=512`
per stage, **`logprobs=20` on every generation** (entropy support truncation at
top-20 — documented approximation, ReDAct-consistent). Judge at T=0; one retry at
T=0.2 on unparseable output; then label `null`, counted.

### 0.2 Environments and seeds
- **ALFWorld** Seen split, all 140 episodes, 50-step cap (AUQ-matched). Unseen-split
  extension if labeled steps < ~2,400; report the extension.
- **WebShop** (E4 only): 140 random Dev episodes, 50-step cap, AUQ-matched; episode
  draw seed logged.
- **Seeds (A4, formula per A17):** per-step per-call,
  `seed = 1000 + task_index*100000 + step_idx*100 + call_offset`. Reproducible;
  restores across-step sampling independence; loops persist as natural
  drift-and-fork rather than byte-exact lock. Same policy for E0-full and E1.

### 0.3 Repository layout
```
uq-agentic/
├── configs/                  # yaml per experiment/condition
├── prompts/                  # versioned; any change bumps suffix
│   ├── decoupled_thought_v3.txt      # + q_t declaration + <confidence> tag
│   ├── decoupled_action_v2.txt       # ReDAct contract + line-2 confidence + g_t reference
│   ├── entangled_auq_v1.txt          # AUQ A.6.2 verbatim suffix (thoughts-in-history)
│   ├── entangled_vanilla_v1.txt      # reserve anchor (trigger-only)
│   ├── posthoc_numeric_v1.txt / posthoc_verbal_v1.txt / ptrue_v1.txt
│   ├── judge_redact_fig9_v2.txt      # rendering: actions+observations, NO thoughts (A7)
│   └── judge_webshop_v1.txt
├── src/ {env, agent, probes, judge, analysis, run.py}
├── data/ {trajectories, labels, perturbations, analysis}
└── results/                  # every table generated by a script; no hand edits
```

### 0.4 τ tagging (environment-derived, config-frozen, unit-tested)
ALFWorld map as v1 §0.4 (look/examine/inventory/goto → I=1; open/close/take/put →
W=1,R=1; heat/cool/clean/slice → W=1,R=0,costly). WebShop: search → I=1;
click[item/option] → W=1,R=1; click[buy now] → W=1,R=0,costly.
**Mandatory: unit test per action family** — a silent τ mis-tag corrupts E2/E3 while
E1 looks healthy. τ never comes from the model.

### 0.5 Agent loops and contracts
- **Decoupled (primary, A16 format-native).** Thought call: reason about state
  (no action vocabulary in the prompt, A8); close with plain labels
  `THOUGHT_TARGET: <one short declarative claim the next decision turns on>` and
  `THOUGHT_CONFIDENCE: <0.00-1.00 that the target claim is true>` — this is the
  **targeted** in-gen reading u(q_t) (roster #6); no generic in-gen thought
  confidence (generic coverage: entangled ĉ + post-hoc probes). Both labels
  parsed then **stripped before the action call and before the probe-facing
  thought span** (strip-before-pass; defensive trim rule A8 also applies).
  Action call: ReDAct contract, one command line, then
  `ACTION_CONFIDENCE: <0.00-1.00 that this action will achieve its intended
  effect as stated in the reasoning>` = u_A(g_t), stripped before env execution.
  Label parse failure → value null, raw kept, exclusion rate reported per arm
  (smoke: 100% first-pass compliance); same-context retry (A11) retained as
  optional fallback only.
- **Entangled (E1b ablation, A15).** One joint generation per step (thought +
  action + AUQ-style in-gen confidence ĉ + explanation), **history = actions +
  observations only — identical content to the decoupled arm**. Describe in the
  paper as "standard act/obs-history ReAct with AUQ-style in-generation
  elicitation," NOT "AUQ System-1" (their memory-retention mechanism is not
  present). The ĉ/explanation are logged but never persist into later contexts.
  No targeted probe in this arm — by design (targeted readings presuppose a
  separable pre-commitment epistemic stage; they are constructible only under
  stage separation, and that asymmetry is itself a reported claim). AUQ
  full-retention exists as a shelved optional arm (REACT_HISTORY_MODE=full),
  run only if a result or reviewer demands the retention regime; the smoke-run
  self-conditioning collapse is reported as anecdote, not experiment.
- **Post-hoc probes** (P(True), numeric; verbal-scale in robustness arm): fresh T=0
  calls on frozen stages; contexts **value-excised** (strip ĉ AND `<explanation>` in
  the entangled condition); fully offline-able.
- **Post-transition re-elicitation (E3/perturbations, contract per A19):** u_t⁺ is
  a **probe-style, value-excised call** — same template family as the post-hoc
  targeted probe: environment history through S_{t+1}, then the *declared* q_t
  claim posed as a standalone confidence-that-this-claim-is-true question. NEVER a
  continuation of agent context (smoke showed agent-voice contamination). Field
  `U_T_targeted_uplus`. Read-only; never fed back. Provenance naming: in-gen
  declared reading = `U_T_targeted_ingen`; extracted-target post-hoc probe =
  `U_T_targeted_posthoc`.

### 0.6 Frozen metric roster (A6)
| # | Metric | Family | Thought | Action | Cost |
|---|---|---|---|---|---|
| 1 | MTE | token-intrinsic | ✓ | ✓ | free |
| 2 | MaxTE | token-intrinsic | ✓ | ✓ | free |
| 3 | PPL ≡ LN-NLL (aliased, one row) | token-intrinsic | ✓ | ✓ | free |
| 4 | SP | token-intrinsic | ✓ | ✓ | free |
| 5 | Verbalized (in-gen, generic) | elicited | ent ĉ only | ent ĉ (joint) | free |
| 6 | Targeted in-gen: u(q_t) / u_A(g_t) | elicited | ✓ dec only | ✓ dec only | free |
| 7 | P(True) (Kadavath) | post-hoc | ✓ | ✓ | +1 call/stage, offline |
| 8 | Post-hoc numeric | post-hoc | ✓ | ✓ | +1 call/stage, offline |
| G | Progress advantage | contrastive-logits | gate | gate | teacher-forced ref pass |
| Δ | Deltas of 1–8 + TEPO ΔH_k | delta (E3) | — | — | derived |

Gate for PA: reference checkpoint for Qwen3.6-35B-A3B publicly available + ≤2 days
integration (use authors' repo; contact them first — same department). Excluded:
sampling/consistency families (survey §4.1 cost argument, citable); post-hoc
verbal-scale (E1b robustness arm only). Action-stage token metrics computed over the
**pre-tag action span**; short-sequence caveat reported. U in [0,1], 1 = uncertain,
for probability-native metrics; token-intrinsic metrics used as raw scores
(discrimination only).

### 0.7 Logging (ground truth = raw text + logprobs + spans; parsed fields are conveniences)
Per generation call: full prompt (post-template) + token count; full raw completion;
per-token logprobs + top-20 alternatives + aligned token ids; config (model+revision,
T, top_p, seed, max_tokens, stop reason); latency + token counts.
Span offsets: thought span; pre-tag action span; every tag span (q_t, confidences,
AUQ ĉ/explanation).
Parsed per step: thought_text (stripped), q_t_text, g_t/effect text, action raw +
parsed(verb,args), U_T_verbalized/targeted, U_A_verbalized/targeted, parse-ok flags,
τ, observation text + observation-changed flag, admissible commands.
Post-hoc calls: prompt + completion + first-token top-20 (P(True) mass summed over
Yes/No token variants) + prompt version.
Bookkeeping per step: run_id, condition, task_id, step_idx, seed used, state hash,
**loop_flag** (repeated (action, observation) pair within episode).
Per episode: success, terminal reason, steps, **loop-collapse fraction**.
Regeneration rule: missing logprobs/alternatives or wrong spans ⇒ regenerate; no
imputation of raw signals. Elicitation parse failure ⇒ metric `null`, raw kept,
exclusion rate reported per condition.

### 0.8 Analysis conventions
AUROC + PRR primary (step-level, `incorrect` = positive); ECE (15 equal-mass bins)
only for probability-native metrics (5–8), never headline. **Bootstrap CIs resampled
at trajectory level**, 10k; paired comparisons bootstrap the difference. Kendall τ-b
for rank agreement. **Within-protocol comparisons only** — raw values never compared
across conditions (Kim & Kang rule, stated as policy). Loop handling (A3): headline
pooled + loop-stratified; loop-collapse fraction as covariate; sensitivity with loop
steps deduplicated to one representative per repeated state. Protocol card per probe
(elicitation provenance, scored span, readout, conditioning context — C1–C4 adapted).
Round-number histograms for elicited probes. Trajectory-comparability suite
(Φ_last/min/avg, T-ECE, T-BS) supplementary only.

---

## Hypotheses (pre-registered; freeze at git tag before full generation)

- **H1 (stage):** rank_m[AUROC(U_T^(m))] ≠ rank_m[AUROC(U_A^(m))] — metric rankings
  differ across stages (test: rank correlation with CI; per-family movement).
- **H2 (type):** h_m(U_T,U_A,τ) beats g_m(U_T,U_A) out-of-sample for ≥2 metric
  families (grouped 5-fold CV by trajectory; held-out log-loss + AUROC).
- **H3 (transition):** for τ.I=1 steps, some delta-family predictor beats its level
  counterpart at predicting downstream error (step t+1 and windowed t+1..t+3).
- **H4 (contract, sharpened per A15):** with history content identical across arms
  (act/obs-only both), the only cross-arm difference is the generation contract
  (joint vs split). Prediction: token-intrinsic metrics (1–4) on the thought span
  are **near-identical** per-step where trajectories have not yet diverged;
  elicited readings differ, and the difference is contract-attributed by
  construction. (The retention-regime entropy-direction prediction is withdrawn
  from the freeze — its regime is no longer in the primary design.)

**Kill switch:** stop only if ¬H1 ∧ ¬H2 ∧ ¬H3 ∧ ¬H4.

---

## E0 (v3, A14) — Label Production: Adjudicated Three-Judge Ensemble (BLOCKING)

Replaces the v2 triangle (which never executed). Protocol decided by Taehyun:
human effort goes to adjudicating disagreements only; no separate audit arm.

1. **Judges:** three API judges from three model families, all disjoint from the
   Qwen agent family; versions pinned in config and reported in the paper. All three
   use the identical Fig-9 v2 rendering (actions + observations, **no thoughts**, A7)
   and the same rubric prompt, T=0.
2. **Every step in every labeled corpus** (E0 sample first, then all E1/E1b/E4
   steps) is labeled by all three judges. Per-judge votes stored in the corpus —
   released with the dataset so others can re-derive labels under different rules.
3. **Disagreement → human.** Any non-unanimous step (2–1 included) is adjudicated
   by one human annotator using the same rendering, blind to the votes. The human
   may mark `uncertain` → step excluded from metrics; exclusion rate reported.
4. **Final annotation semantics (stated in the paper):** unanimous → ensemble
   label; disagreement → human label; uncertain → excluded. This human-validated
   version is the final annotation for all experiments.
5. **Escalation rule (pre-committed):** if the disagreement rate exceeds ~40%,
   that is a rubric problem — fix the judge prompt once, re-run all three judges,
   log the revision. Otherwise proceed.
6. **Reported statistics (free byproducts, no extra annotation):** per-pair judge
   κ; disagreement rate by stratum (τ × loop × architecture); and on 2–1 splits,
   the rate at which the human sides with the majority (majority-vs-human agreement
   on contested steps — the credibility number this protocol yields natively).
7. **Stated limitation (one line in the paper, not extra work):** unanimous labels
   are not human-audited; label validity on the unanimous pool rests on the
   ensemble's cross-family agreement, and the released per-judge votes let readers
   probe it.

Reproducibility note: the frozen-local-judge property is traded for label quality;
the released corpus (pinned judge versions + all votes + adjudications) is the
reproducibility artifact. The local Llama judge is dropped from headline labeling
(optional cheap relabeler for the model sweep only; never mixed into headline
labels).

Budget: judge calls scale with corpus size (cheap, batched); human time scales with
the disagreement rate only.

## E-P — Perturbation Battery (the causal validity column; runs on E1's frozen data)

For sampled τ.I=1 steps: hold prefix + q_t fixed; swap the observation across five
conditions — informative (original) / irrelevant (other-step obs) / corrupted (error
string) / contradictory (negates the resolving fact; templated per task type) /
absent. Regenerate only the following thought + all Thought-stage probes (and u_t⁺).
Score **every estimator** on: resolution tracking (drop on informative), persistence
(no drop on irrelevant/corrupted/absent), contradiction response, and false-fire rate
on clean twins (vPGM's 22% precedent: report over-firing).
Output: the validity column of the map — "predicts labels" vs "responds to evidence,"
per metric. ~300 perturbed steps; ~1 day; label-free.

## E1 — Stage-Wise Metric Map (primary)

One decoupled generation run (140 tasks, per-step seeds, primary model); every roster
metric computed on both stages of every step; every step judge-labeled.
**Deliverable:** the metric-by-stage performance map — AUROC/PRR (+ECE where native)
per (metric × stage), with trajectory-clustered CIs, loop-stratified variants, and
scale robustness (sweep models on winning contrasts only, staged after primary).
Tests **H1**. Anchor: token-metric AUROCs cited against ReDAct's band as
**pipeline-sanity context, not a validity gate** (protocol differences expected per
Kim & Kang; debug on pathology, don't chase the number).
Pilot: 30-task Cell-A-style sanity run precedes the freeze (token metrics in a
plausible band; parse rates; 20 τ tags eyeballed).

## E1b — Entanglement Ablation (theory-loaded)

One entangled-AUQ run, same tasks/seeds. Same metrics where applicable (AUQ ĉ = the
entangled verbalized row, verbatim template; + post-hoc probes on excised contexts).
Tests **H4**: family-wise invariance (1–4) vs shift (5–6) across architectures —
distributional (per-step paired where states align) and discrimination-level.
Plus: in-gen vs post-hoc rank agreement per architecture (the two-horns divergence,
publishable either way); temperature arm (numeric, T=0.7, 3 samples, mean);
contamination ablation (30 tasks, thought prompt with vs without confidence
instruction, same seeds: length, MTE, action distribution); round-number clustering
for all elicited rows. Self-conditioning collapse figure (entropy vs step index,
loop-marked) comes from this run.

## E2 — Typing Value, Per Family

All labeled decoupled steps. For each metric family m: pooled
`error ~ U_T + U_A + U_T:U_A` vs typed (same formula per τ stratum: I=1/W=0, I=0/W=0,
I=0/W=1/R=1, I=0/W=1/R=0; merge R strata if <100 steps, report the merge). Grouped
5-fold CV by trajectory; bootstrap the pooled-vs-typed log-loss difference.
Tests **H2** (typing helps across ≥2 families ⇒ semantics claim probe-independent).
Descriptive: sign of corr(U_T, U_A) per stratum (predicted negative for I=1/W=0).
Thin-cell rule pre-committed. Analysis-only, ~1 day.

## E3 — Transition / Promise Comparison (the delta column)

For τ.I=1 steps (t+1 defined): per metric family, ΔU^(m)(t) = U^(m)(t+1) − U^(m)(t);
the targeted delta is reported in **two provenances (A19)**: mixed
(`U_T_targeted_ingen` at t → `U_T_targeted_uplus` at t+1) and same-provenance
(`U_T_targeted_posthoc` at t → `U_T_targeted_uplus` at t+1; the t-side probe already
exists in the suite — zero new calls). Systematic disagreement between the two
deltas is reported as a finding (provenance effect on the promise check), not
treated as noise.
V_m(t) = 𝟙[ΔU^(m) ≥ −ε_m], ε_m sensitivity over {0, .05, .1} (ΔH_k thresholds per
TEPO's convention).
**Predictor comparison, same steps, trajectory-clustered bootstrap on differences:**
levels (each m) · **deltas (each m, incl. TEPO ΔH_k as champion baseline)** ·
V_m indicators · u_A(g_t) as the **elicited transition prior** (does the agent's own
expectation predict violation? high-u_A(g_t)+violation = Delusion Gap with a
receipt) · AUQ level-threshold 𝟙[ĉ<τ], τ∈{0.8,…,0.95}, best-of-sweep ·
Σ/mean accumulation (UProp's feasible proxy — full UProp's Z×N rollouts out of
budget by construction, stated) · PA-drop if gated in.
Targets: judge label at t+1; windowed t+1..t+3.
Tests **H3**. Exploratory (flagged): **unearned resolution** D(t) = 𝟙[ΔU ≤ −δ under
non-informative transition], δ∈{.1,.15,.2} — the Delusion Gap inverted; if predictive,
promise-checking catches unresolved uncertainty AND unearned certainty.
Mostly re-analysis of E1 data + the u_t⁺ re-elicitation pass; ~1–2 days.

## E4 — Dangerous-Quadrant Existence (WebShop)

140 Dev episodes, 50-step cap, decoupled + winning probes; judge-labeled
(judge_webshop_v1, same rendering rule). Deliverables: occupancy of
(U_T tercile × U_A tercile × τ); the {high U_T, low U_A, I=0, W=1, R=0} cell with
labels and error rate vs complement; `buy now` steps feed E3 as the highest-stakes
promise population. High-observation-noise caveat stated (harder test — say so).
Fallback: τ-instrumented ToolBench slice if integration >2 days. 2–4 days.

## E5 — Instrument Cost

From E1/E1b runs, no new compute: success rate decoupled vs entangled
(trajectory-clustered CI); calls/tokens/latency per step, with and without offline
probes (in-gen rows add **zero** calls — report it); episode-length distributions.
Overhead accounting, not hypothesis; degradation reported, doesn't gate. Half a day.

---

## Sequencing, Kill-Switch, Budget

```
E0 (triangle; A4 seeds; A7 stratification)          ← BLOCKING
 └─► E1 pilot (30 tasks, sanity) ─► GIT-TAG FREEZE (H1–H4 + rules)
      └─► E1 (decoupled, full) ─► E1b (entangled)
           ├─► E-P (perturbations, frozen data)
           ├─► E3 (deltas; before E2 — differentiating claim first)
           └─► E2 ─► E4 ─► E5 ─► staged model sweep (winning contrasts only)
STOP only if ¬H1 ∧ ¬H2 ∧ ¬H3 ∧ ¬H4.
```

Budget: E0 (1d+annotation) · pilot (1d) · E1+E1b generation+judging (~6–8d, GPU-side)
· E-P (1d) · E3 (1–2d) · E2 (1d) · E4 (2–4d) · E5 (0.5d) ≈ **2.5–3 weeks**, dominated
by generation + judging. Sweep extends afterward.

Non-negotiables carried from v1: strip-before-pass; τ never from the model; raw
logprobs + top-20 + spans or regenerate; every table script-generated; prompts
versioned; frozen interpretations amended only by dated deviation notes.