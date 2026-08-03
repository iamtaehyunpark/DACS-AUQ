# HANDOFF — Agentic UQ via a Characterized-Once LLM Judge
## Complete orientation: concept, logical chain, experiments, data, gates, project state

**Taehyun Park · UW–Madison CS · Handoff v1, 2026-08-03**
Companion documents: `paper_B_proposal_v3.md` (working proposal, amortized-metrology
framing), `paper_A_proposal_v1.md` (fallback). This document is self-contained:
a reader starting here needs no prior context.

---

# PART I — THE PAPER CONCEPT

## 1. The problem in plain language

LLM agents fail *in the middle* of doing things — they loop, act on wrong
beliefs, take irreversible wrong actions. Safe deployment needs a per-step,
online answer to: *should this next action be trusted?* This is uncertainty
quantification (UQ) at the agent-step level.

The field's toolbox for this is inherited from single-turn QA: intrinsic
signals (token entropy, sequence probability, verbalized confidence,
P(True)-style self-probes) and trained meta-models. Both quietly assume that
some signal, once validated, transfers to new models and new tasks.

## 2. The two findings that break the inherited approach

1. **Step-judging is environment-relational.** An agent's action, scored in
   isolation, carries no signal (≈ coin-flip AUROC). Quality is a relation
   between the action and the environment state/history — and the biggest
   single evidence gain is *what the environment did in response*. QA
   judging, where the answer text suffices, does not port.
2. **No universal best signal exists — but signal-preference is a stable
   model trait.** Across a full metric × model × dataset grid, the winning
   signal and its scope flip cell to cell. Crucially, the flipping is not
   noise: it clusters by model family / size / architecture. The best metric
   is a *property of the model*, discoverable per model, generalizable never.

## 3. The thesis (amortized metrology)

> **Fix one capable judge model. Characterize its UQ behavior completely,
> once — its best elicitation recipe, its evidence requirements, its biases,
> its calibration. Then deploy it as a measurement instrument across
> arbitrary agent models.**

The metaphor: a thermometer does not need to be a different kind of thing
from what it measures — it needs to be *known*. Finding 2 says agent-side
characterization never amortizes (every new agent restarts the search) and
is impossible for closed models (no internals). Judge-side characterization
amortizes perfectly: invest once, apply everywhere.

Two properties follow:
- **White-box judge, black-box agent.** The judge uses its own logprobs (any
  open-weight model); the *agent* needs no internal access — so this is the
  only UQ route that works on closed frontier agents.
- **Independence is NOT the thesis.** Whether the instrument should be
  external rather than the agent's own self-probe is a subordinate empirical
  selection question (it turns out external wins — see Argument 4) — but the
  thesis would survive even if a well-characterized self-probe were
  admissible at some scales.

## 4. What the paper claims as contributions (exactly three)

1. **The judge protocol** — the specified, training-free methodology:
   an *evidence grid* (what the judge reads: prior rules / process history /
   realized environment response) + a *τ-indexed invocation policy* (when to
   invoke, keyed to action type: irreversible → check before acting;
   reversible/cheap → check after, or skip). Action-typing used as
   *estimator policy* is unclaimed in prior work.
2. **Amortized characterization, validated** — the judge's recipe is
   invariant across judged agents (the thesis result) while agent-side best
   signals scatter; and the instrument should be external (beats
   self-assessment against environment-verified and human targets).
3. **The instrument's documentation** — measured evidence hierarchy, bias
   battery (rule false-positives with decoy controls, perturbation
   sensitivity), human-alignment verification, cost card.

The step-labeled corpus + harness ship as supporting artifacts, not claimed
contributions.

---

# PART II — THE LOGICAL CHAIN

## 5. The spine (memorize this)

> **(1) steps are judged by environment context, not content
> → (2) no universal signal exists, but signal-preference is a stable model
> trait
> → (3) THEREFORE: invest in knowing one judge's traits completely and reuse
> it everywhere [THESIS]
> → (4) that instrument should be external
> → (5) it agrees with humans
> → (6) and it ships with an operating manual.**

Each node licenses the next: (1) opens the question (QA answers don't
apply); (2) closes the agent-side road AND establishes trait-stability —
which is exactly what makes (3) sensible (traits are knowable); (3) is
proven by recipe invariance; (4) is an instrument-selection result
subordinate to (3); (5) anchors the whole chain to human truth; (6) makes it
deployable.

## 6. The self-defeat trap and its answer (the paper's key argumentative move)

The obvious review: *"You claim no signal generalizes, then rely on the
judge's signal generalizing. Why is the judge exempt?"*
Answer: the judge is exempt **iff its characteristics are stable across
judged targets** — an empirical claim, tested head-on as the paper's central
result (the invariance test, E3). If the judge's best recipe flipped per
target, the thesis would be falsified and the paper collapses to the
fallback. This is by design: the thesis is maximally falsifiable, and the
invariance table is its verdict.

## 7. Claim-strength discipline (pre-registered, non-negotiable)

- The word "impossible" appears nowhere; all negative claims are quantified
  results over the tested space.
- Argument 4 has a pre-registered ladder: (a) strong judge beats weak
  agents' self-best → (b) the margin survives after removing trivial
  loop-detection → (c) external wins at matched capability (peer cells,
  self-diagonal contrast). Rung (b) is required (instrument credibility);
  rung (c) failing narrows only the *recommendation's* scope, never the
  thesis.
- Trait claims (size/architecture correlations, judge-capability knee) are
  characterizations with n=small; stated as existence/clustering results,
  never laws.

---

# PART III — EXPERIMENTS (from-scratch design, E0–E6)

Design principle throughout: every experiment answers a **general**
question — a pattern across the whole model × environment space — and its
output is one legible picture. No case studies.

## E0. The measurement bed (infrastructure; everything runs on it)

- **Agent pool**: 6–8 models crossing three independent axes — size (~4B /
  ~8B / ~30B / ~70B), family (≥3 lineages), plus ≥1 closed frontier model
  (the black-box demonstration arm).
- **Environment pool**: 3–4 environments crossing task character — embodied
  (ALFWorld-like), knowledge/retrieval (HotpotQA-like), tool-use/API,
  ideally web.
- **Volume**: ≥3–5k steps and ≥1k failure steps per agent × environment
  cell; balanced success/failure episode sampling.
- **Pre-registration before any scoring**: metric list, recipe search
  space, invariance threshold ε, all pass criteria.

## E1. The unit of measurement → scoring must be per step, not per trajectory

**What it establishes**: the instrument has to read steps, because rolling
step scores up to a trajectory verdict is either confounded or empty. This
removes the alternative that would make a per-step online instrument
unnecessary — if whole-run scoring worked, you would simply score whole runs,
which is what the existing trajectory-verdict methods do, and they are offline
by construction and so cannot inform the next action.

Two measurements, both over the existing corpus, no new generation:

(a) **Length swamps trajectory-level scoring.** Episode length alone, used as
the only predictor of episode failure, on cap-dominated benchmarks. Any
trajectory-level AUROC that does not beat this baseline is measuring run
duration, not quality.
(b) **Aggregation destroys the signal.** The same step scores that discriminate
at step level, pooled per episode (mean / max / final / slope / Δ), scored
against episode outcome.

**Pass**: (a) length-only trajectory AUROC ≈ 1.0 where failures are
cap-dominated; (b) every aggregation at or near chance while the step-level
score on the same data is well above it — the information is present per step
and gone once pooled.
**Picture**: step-level AUROC beside every trajectory-level aggregate, with
the length-only baseline drawn across the top.
**Reporting requirement this creates, which we then follow ourselves**: any
trajectory-level claim ships with a length-only baseline.

Secondary: failure-mode census (loops / stale-belief / irreversible errors
carry majority failure mass in every environment).

**Note on the former E1.** This slot previously held the evidence ladder
({action only} → {+history} → {+reasoning} → {+realized response}), framed as
proving that step quality is relational to the environment. That framing is
retired: no reviewer disputes that an action string cannot be judged without
the task and state, and the claim says nothing about instrument stability,
which is the thesis. What survives is operational, not argumentative — the
judge must be fed *something*, so evidence configuration becomes a search
dimension inside E3, and whatever the search selects becomes a line in the
instrument's documentation (E6b): this is what it needs to read. The decoy and
wrong-episode controls move with it.

## E2. The metric map → proves Argument 2

Every intrinsic metric (+1–2 trained meta-model baselines) × every agent ×
every environment; step-level AUROC vs environment-verified labels.
Analysis in two mandatory halves:
(a) **no universal**: winner per cell; bootstrap test that no metric's win
rate is compatible with "best everywhere";
(b) **but lawful**: variance decomposition of winner identity over model
family / size / environment / architecture — the trait-stability half that
makes (3) sensible.
**Pass**: no metric wins >60% of cells; model-side factors explain majority
of winner variance.
**Picture**: the winner-colored grid — no dominant color, but colors in
blocks.

## E3. The invariance test → proves the THESIS (Argument 3)

Two judge models (one mid, one large — proves the methodology, not one
lucky model). Per judge: full recipe search (probe format × evidence
combination × calibration) run *independently per judged agent ×
environment*; search on subsamples (~300–500 steps/cell), full-corpus
scoring only at the winning and globally-fixed recipes.
**Pass (pre-registered)**: fixing the judge's single globally-best recipe
costs ≤ε AUROC (ε ≈ 0.02) vs per-target best in ≥90% of columns. Plus
adaptation-cost curve on a **held-out agent** excluded from all search
(calibration saturates at deployably small n — expected ~200 steps).
**Picture**: E2's scattered grid beside E3's constant column — the thesis in
two panels. **This is the paper's Figure/Table 1.**

## E4. The reading matrix → proves Argument 4

Complete assessor × target matrix, every model reads every model's frozen
trajectories including itself. Three built-in disentanglements:
(i) *independence vs capability*: peer cells vs self-diagonal;
(ii) *judge scaling*: AUROC vs judge size per fixed target (locates the
"good-enough" knee if it exists);
(iii) *non-triviality*: all gains decomposed into degenerate steps
(mechanically flagged loops/stagnation) vs substantive steps — advantage
must survive on substantive steps alone.
**Pass**: external > self on majority of cells vs environment-verified
labels, surviving (iii); result of (i) sets the wording rung.
**Picture**: the matrix with the self-diagonal as the visible weak stripe.

## E5. The human alignment check → proves Argument 5

On the human gold subset: judge-vs-human agreement vs
self-assessment-vs-human agreement, identical steps, all arms; reported
against the human–human agreement ceiling. Plus: every E3/E4 headline
number re-verified on gold.
**Pass**: judge-human > self-human, approaching the inter-annotator
ceiling.
**Picture**: paired bars per arm, both measured against humans.

## E6. The operating manual → delivers Argument 6

(a) **Invocation policy**: τ-typed gating vs uniform-random inspection at
matched budgets; full budget-vs-detection curves, all environments.
Pass: gated dominates uniform at every budget on ≥2 environments.
(b) **Bias documentation**: decoy-controlled rule injection (relevant vs
irrelevant vs none; quantify the help AND the specific false-alarm mode —
flagging legitimate revisits); perturbation battery (order, format, length,
position). Pass = quantified with CIs, not victory.
(c) **Cost card**: tokens/latency per check across judge sizes; adaptation
cost from E3; end-to-end closed-frontier-agent demonstration.

**Proof topology**: E1 → E2 → E3 → E4 → E5 → E6.
**Kill-order under resource pressure**: survivable without E6b's full
battery and with 3 environments; NOT survivable without E3, E4(iii), or
E5's re-verification.

---

# PART IV — DATA (D1–D9, deduplicated; every experiment is a slice)

## In plain terms, before the numbering

Seven things, and only the first requires running an agent:

1. **Trajectories** from many models over a few environments. Logged while
   running: state, action, reasoning, observation, the agent's token logprobs,
   its in-generation stated confidence. The last two cannot be recovered
   afterward. The corpus must *span generators* — variation across the models
   being read is the independent variable E3 tests against, not a robustness
   check on a deep single-model corpus.
2. **Mechanical step facts** derived from (1) with no model in the loop:
   repeats and loops, rejected/no-op actions, cap hits, episode length,
   outcome, action type.
3. **Environment labels** from (2) — the agent looped, the action did nothing,
   the task failed. Primary truth for every headline number, and the reason
   the argument is not a judge validating judges.
4. **Human labels on a subset**, for steps the environment cannot settle and
   as the outside anchor.
5. **Agent self-scores** — every intrinsic signal and self-probe per step.
   What E4 compares against.
6. **Judge scores** — every judge × every generator × every evidence setup.
   One table; E3, E4, E5 and E6 are slices of it, not separate runs.
7. **Cost and latency**, a free byproduct of (6).

**Order of work follows directly**: generation is first and is the only
irreversible stage. Everything downstream is either derived mechanically or is
a scoring pass over frozen trajectories, so it can be redone at will. An arm
generated without logprobs or in-generation confidence is simply lost. The
logging spec is therefore frozen *before the first episode*, not adjusted
during the run.

## Tier 0 — generation (the only stage that runs agents)

- **D1. Trajectory corpus** — ~80–120k steps (6–8 agents × 3–4 environments
  × volume targets). Logged AT GENERATION TIME per step: state, action,
  reasoning, observation, **agent token logprobs**, **in-generation
  verbalized confidence**. These two are unrecoverable afterward — D1's
  logging spec is the suite's one irreversible decision. Includes the
  closed-frontier cell (trajectories only, no internals — by design).
- **D2. Step metadata layer** (mechanical, no LLM): τ types, loop/stagnation
  flags, state predicates, cap events, outcomes. Feeds labels, gating
  simulation, non-triviality splits, failure census.

## Tier 1 — labels (three layers, strictly ordered)

- **D3. Environment-verified labels** — mechanical function of D2. PRIMARY
  target for every headline number.
- **D4. Human gold set** — stratified ~1.5–3k steps (power-analyzed), ≥2
  annotators + adjudication + published IAA. One annotation effort, three
  uses: E5, headline re-verification, calibration ground truth.
- **D5. Ensemble fill labels** — only where D3/D4 can't reach; provenance-
  flagged; NEVER validates any judge.

## Tier 2 — scoring

- **D6. Intrinsic metric table** — every intrinsic signal per step per
  open-weight agent from D1's logged internals + self-probe passes.
  Dedup: the self-probe rows ARE E4's self-diagonal.
- **D7. Master probe tensor** — (assessor × target × environment × step ×
  evidence-condition × recipe [× perturbation]) → score. E3/E4/E6b are named
  slices; E5 = D7∩D4 analysis; E6a = policy simulation over D7+D2; E1(b) =
  D7 step scores pooled per episode against D2 outcomes (zero new scoring for
  all of these). Held-out-agent = exclusion rule, not extra data. Volume:
  ~1.5–3M single-token probe calls (GPU-days, not months).
- **D8. Meta-model baselines** — trained predictors for E2, with leak-proof
  split protocol over D3.

## Tier 3 — byproduct

- **D9. Cost/latency logs** — captured during D7 runs; E6c is a report.

**Dependency chain**: D1 → D2 → D3/D5 → D6, D7 → all analyses; D4 parallel
after D1.
**Schedule-critical**: (1) D1 logging spec complete before first episode;
(2) D7's search-sampling rule and E3's ε pre-registered before scoring.

---

# PART V — VALIDITY RULES (apply everywhere, no exceptions)

1. **Circularity firewall**: the paper proposes an LLM judge → no
   LLM-derived label validates it. Headline numbers vs D3; re-verified vs
   D4; D5 never in the loop. Label-ensemble families disjoint from all
   evaluated judges and agents.
2. **Prefix-only asymmetry** for all pre-execution claims (the online
   estimator sees only what was knowable at time t). One hindsight-ceiling
   figure (same judge, prefix vs full trajectory) bounds any online
   estimator and quantifies the online-vs-hindsight knowledge gap named in
   the intro.
3. **Step-level everything**: trajectory-level AUROC is length-confounded
   (length alone ≈ 1.0 on cap-dominated benchmarks) — a methodological
   floor stated once in §2, then enforced silently.
4. **Fixed-scope primary reporting**; cross-corpus AUROCs compared as
   problems, not judges.
5. **Pre-registration** of thresholds and pass criteria before runs; claim
   wording set mechanically by the pre-registered ladder.

---

# PART VI — GATES AND DECISION FRAMEWORK

| Gate | Tests | Criterion | On fail |
|---|---|---|---|
| **1 — circularity** | E4/E3 headlines vs D3+D4 | margins survive non-LLM targets | fallback A |
| **2′ — invariance (THESIS GATE)** | E3 | fixed recipe ≤ε cost in ≥90% columns | thesis falsified → fallback A |
| **2 — instrument credibility** | E4(iii) | advantage survives on substantive steps | fallback A |
| — | E4(i) rung (c) | matched-capability win | NO fail state — narrows recommendation wording only (pre-registered) |
| **3 (soft) — τ** | E6a | gated dominates uniform | τ demotes to pre/post split; grid headlines |

**Fallback: Paper A** (`paper_A_proposal_v1.md`) — analysis/benchmark paper
(transfer study + length confound + estimator-dependence + corpus), venue-
adjusted to a datasets-and-benchmarks track, headline = confound + corpus.
Nearly all B data reuses into A; fallback cost ≈ 0.

---

# PART VII — POSITIONING (nearest neighbor per clause)

- **Kapoor et al.** — direct precedent (one strong model estimates others'
  uncertainty, QA, fine-tuned); we extend to agentic, training-free,
  prompted.
- **CEB** — shared problem formulation (pre-execution productivity
  estimation given task/state/history); we depart on estimator and extend
  the assessment point via τ.
- **MT-Bench / LLM-as-judge** — structural precedent for the
  bias-taxonomy-and-mitigation section; structural departure: preference
  agreement vs consequence-anchored correctness; answer-sufficient vs
  environment-relational judged object.
- **Agentic-UQ survey (Oh et al., in-department)** — documents the field's
  problems and the benchmark gap (4/44 step labels); their action typing
  models uncertainty reduction (information gain) — ours gates estimator
  invocation. Cited as one systematization among several (with ReDAct,
  Kapoor et al.), not as the paper's foil.
- **UALA/SAUP/MATU** — trajectory-level, offline by construction; we are
  step-level, online.
- **[2511.07364]** — independently supports step granularity; remains
  self-evaluation.
- **Guideline-grounded verification** — occupies one cell of our evidence
  grid (the prior row).
- **Tian et al.** — apparent conflict (RLHF verbalized confidence is
  calibrated in QA) reconciled explicitly on three axes: post-hoc vs
  in-generation; factual recall vs relational step quality; frontier RLHF
  vs deployed open-weight range.
- **LM-Polygraph** — intrinsic-UQ benchmarking for single-turn generation;
  no agents, no steps — the genre neighbor our from-scratch bed supersedes
  in the agentic setting.

---

# PART VIII — PROJECT STATE AND OPEN ITEMS (as of 2026-08-03)

## Banked (existing runs; the from-scratch design's partial instantiation)

~30k judge-labeled steps over 8+ arms (4 families 4B–70B × ALFWorld +
HotpotQA × 2 generation architectures): transfer matrix with clustering
analysis (E2's core at 2 environments); length-confound result; evidence-
ladder prototype (self-probe, one arm) with the +0.070 realized-response
gain and rule/decoy effects (+0.072 relevant rule, +0.155 revisit false
positives); self-assessment floor (sub-7B ≈ 0.53–0.64); external go/no-go
4/4 (Qwen-35B over 4B agents, +0.02..+0.28, but vs ensemble labels —
pending gate-1 recomputation); sample-efficiency curves (~200-step
saturation); cost timings (3,300 probes ≈ 5 min / A100).

## Delta: from-scratch design vs banked

Adds: 3rd+ environment (tool-use/web); closed-frontier agent arm; second
judge in E3; held-out-agent adaptation test; wrong-episode controls in E1;
powered human-label sizing; E4 peer/upward cells; E6a curves; battery.
The delta list is the scoping decision pending: which additions fit the
window vs move to camera-ready/follow-up.

## Immediate task order (current plan)

**Under the from-scratch design, generation comes first** — it is the only
irreversible stage, and the corpus must span generators because that spread is
what E3 measures against. Freeze the D1 logging spec (logprobs, in-generation
confidence, per-step fields) before the first episode; an arm generated without
them is lost and must be regenerated in full. Everything below is derived data
or a scoring pass over frozen trajectories and can be redone at will.

The order below is the *banked-corpus* plan, which stands until the delta-list
scoping decision settles how much new generation is in scope:

1. Gate-1 recomputation (blocks everything's interpretation).
2. Reading matrix completion (yields E3 invariance table + E4 + size
   curve) — **blocked on pre-registering the invariance threshold ε**.
3. Loop stratification (gate 2).
Checkpoint **2026-08-14**: gates 1, 2, 2′ decidable on passes 1–3 alone.
Then: external-judge grid, τ curves, veridicality, hindsight ceiling,
battery, writing.

## Open items (critical path)

- **Changdae Oh conversation** (in-department overlap; typed-aggregation
  appendix scope) — blocks τ and out-of-scope claim freezes in BOTH papers.
  Overdue; flagged deadline-critical for weeks.
- **Invariance threshold ε pre-registration** — blocks pass 2; the thesis
  gate has no criterion without it.
- **Scoping decision on the from-scratch delta list** (above).
- **Consequence of the E1 reframe on the spine, unresolved.** Node (1) of
  §5's chain reads "steps are judged by environment context, not content" —
  which was E1's old content. E1 now establishes the unit of measurement
  (per-step, not per-trajectory) instead. Either node (1) is restated as
  "trajectory-level scoring is confounded and empty, so measurement is
  per-step" — which arguably opens the paper better, since it is the node
  that makes an online per-step instrument necessary at all — or Argument 1
  keeps its old wording and loses its dedicated experiment, becoming a
  paragraph in the setting section. Not resolved here: it changes the
  paper's opening move and is Taehyun's call.
- Hindsight-ceiling protection level: current status (b) — promoted into
  must-run (cheap; insures §1's framing) — per discussion 2026-08-03.

## Decision log pointers (project amendment convention A1–A24)

A20 fork resolution (B primary, A fallback) · A21 problem-statement
rationalization + invariance promoted with hard gate · A22 human-alignment
check adopted via gold subset (partial reversal of human-audit drop) · A23
control loop out of scope + theory floor fixed (coupling one-liner + τ
decision-theoretic line only) · A24 amortized-metrology reframe (thesis =
characterize-once instrument; independence demoted to instrument
selection). Earlier arc: theory diet, architecture-argument de-scope,
6→4→3 contribution cuts — all logged in prior proposal changelogs.

**A25 (2026-08-03) — E1 reframed to the unit of measurement.** E1 was the
evidence ladder, framed as proving step quality is relational to the
environment. Retired: the claim is undisputed (an action string cannot be
judged without task and state), and it says nothing about instrument
stability, which is the thesis. E1 now shows that scoring must be per step —
length alone swamps trajectory-level AUROC on cap-dominated benchmarks, and
step scores pooled to the episode collapse to chance — which is what makes an
online per-step instrument necessary rather than assumed. The evidence ladder
survives operationally, as a search dimension inside E3 and a line in the
instrument's documentation. Spine consequence flagged as an open item.

## Working conventions (for any collaborator or future session)

Terse, structured, no flattery; final calls are Taehyun's — push back once
with reasons, then execute; every decision logged as a dated amendment;
pre-registration before runs; specs committed to repo before freezes.
