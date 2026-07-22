# Stage-Separated, Action-Typed Uncertainty Measurement in LLM Agents
## Theoretical Framework & Positioning — **V2 (post-pivot)**

**Version:** 2.0 · 2026-07-21 · supersedes `uq_theory.md` (v1 retained for provenance)
**Companion:** `uq_experiments_v2.md`

**What changed in V2 (the pivot):** the paper no longer bets on one probe ("elicited
U_T beats entropy"). It is now a **systematic study and framework**: decoupling is the
coordinate system (prior art: ReDAct), and the contribution is the first
stage-separated, action-typed, perturbation-validated **map** of where existing
uncertainty estimators work, fail, and change meaning inside an agent — with
transition deltas (the promise check) as the map's final column. No single metric is
privileged a priori; four structural hypotheses (H1–H4, §3) are pre-registered instead.

**Central claim:**
> No uncertainty estimator is intrinsically "agentic." Its meaning and utility depend
> on which stage it measures, what transition the selected action induces, and whether
> that transition fulfills its expected uncertainty effect.

Empirical form (abstract's last line): *we provide the first stage-separated,
action-typed, perturbation-validated map of where existing uncertainty estimators
work, fail, and change meaning inside an LLM agent.*

---

## 1. The Mental Model

An LLM agent does not produce one answer whose uncertainty accumulates. It traverses a
sequence of **locally posed decision problems**. At each step it holds an epistemic
state, selects a policy, and proposes a transition whose informational and external
consequences determine how those uncertainties should be read.

Three commitments:

1. **Uncertainty is a per-step primitive.** History enters only through S_t. Steps are
   *conditionally posed*, not independent (never say "independent" — the independence
   claim conflicts with error propagation and a reviewer will find it).
2. **Thought and Action are different kinds of quantities.** U_T ≈ epistemic ("do I
   know?"), U_A ≈ policy ("do I know what to do?"). Anti-correlation between them is
   the agent working correctly.
3. **The criterion is control, not diagnosis.** A measurement is accurate if it is
   readable at the current prefix, early enough to act. A calibrated terminal score
   fails this criterion by construction. (Criterion — not this paper's deliverable;
   the controller is the follow-up paper.)

Trajectory-level uncertainty is not universally invalid; it is the wrong *primitive*
for online reading and should be **derived** from typed local states.

---

## 2. The Framework (the argument chain)

Each claim forces the next. This section is unchanged in substance from v1; its role
changed — it is now the **coordinate system that justifies the benchmark's axes**, not
a list of claims each defended by one experiment.

### 2.1 What a trajectory is
A chain of locally posed problems; the sub-goal at t is not the global task. History
matters but enters only through S_t. Consequence: uncertainty about a local decision
is a local quantity; reading it off the whole trajectory measures an object no
decision corresponds to.
**Known weakness, stated:** for an LLM agent S_t is operationally the context window,
so the Markov language is nearly tautological. It earns its keep only through what it
licenses — the reset rule (§2.6). One paragraph in the paper; ground it in published
formalism (Progress Advantage's stochastic-MDP Prop. 1; contrast UProp §2.2's
deterministic-transition assumption, which marginalizes away the observation the reset
rule centers).

### 2.2 Two quantities inside one step
U_T (do I know?) vs U_A (do I know what to do?). Not knowing a fact is exactly what
makes searching for it the confident move — so a single blended emission mixes two
signals that structurally oppose each other. **This motivates stage separation as a
methodological prerequisite**, not as a novelty claim (ReDAct occupies the
architecture; see §8).

### 2.3 The contract caveat (load-bearing; source of H4)
Autoregression factorizes P(T,A|S) = P(T|S)·P(A|S,T): a naive stop-append-resume
samples the identical distribution. Separation means something only via a different
**inference contract**. Two consequences:
- Token-intrinsic metrics (entropy family) should be **invariant** under
  entangled-vs-decoupled measurement absent contract change.
- Contract-carrying metrics (in-generation verbalized) should **shift**, because
  their contract is part of the generation.
This is pre-registered as **H4** — the sharpest single, theory-derived, falsifiable
prediction in the study, testable family-wise in the entanglement ablation (E1b).

### 2.4 Probes measure different objects (shared premise + our stipulations)
Thought-token entropy ≠ epistemic uncertainty: a model can fluently verbalize
ignorance at low entropy. **Provenance: shared background, not our insight** — AUQ
App. A.5.4 (token confidence vs content uncertainty; CoT length bias), Lin et al.,
Tian et al.; STAPO independently argues raw entropy conflates state complexity with
decision confidence. The smoke run adds a mechanism: under entangled
thoughts-in-history, entropy collapses via **self-conditioning** (0.44 → 0.009 nats
across a belief-locked loop) — measuring copy-predictability, not confidence. This is
the candidate mechanistic explanation for ReDAct's reasoning-entropy failure (0.596),
reported loop-stratified.

Two definitional stipulations (stated once, enforced everywhere):
- **Verbalized confidence := in-generation** — emitted in the same response as the
  content it qualifies (canonical form: Lin, Tian, AUQ). Two-stage variants exist in
  the taxonomy (Xiong, Tian) but are a different probe class here: **post-hoc
  self-evaluation** — Kim & Kang's supplied-answer result shows post-hoc readings
  drift toward plausibility/provenance (+0.021 plausible-wrong gap; +0.055
  self-preference).
- **Targeted elicitation**: u(q_t) — confidence about an explicitly named epistemic
  target q_t declared in the thought; and u_A(g_t) — confidence the action will
  achieve its stated intended effect. Targeting operationalizes what the reset rule
  always presupposed ("the uncertainty that motivated the action") and is what
  distinguishes the elicited rows from AUQ's generic ĉ.

The two-horns problem is instrumented, not argued: in-generation contaminates the
thought (self-grading changes generation); post-hoc contaminates the reading
(plausibility drift). E1b measures the divergence and bounds the contamination.

**Post-pivot status:** none of this crowns a winner. It defines the probe *families*
whose behavior the map compares. Under the pivot, "which probe reads epistemic state"
is a result, not an assumption.

### 2.5 Action semantics: the interpretation layer
The primitive is 𝒰_t = (U_T, U_A, τ_t), τ_t = (I, W, R, C) — information-acquiring,
world-modifying, reversible, cost class. Same numbers, reversed readings:

| Pattern | Reading |
|---|---|
| high U_T, low U_A, I=1, W=0 | healthy epistemic recovery → proceed |
| high U_T, low U_A, I=0, W=0 | ungrounded continuation → retrieve/verify |
| high U_T, low U_A, I=0, W=1, R=0 | dangerous commitment → block |
| low U_T, high U_A | planning/tool-selection problem, not epistemic |

**Hard constraint:** τ from environment spec, never LLM self-classification
(uncertain model → uncertain classification → uncertain interpretation).
Two published foils sharpen this: the Algoverse SAUP adaptation **bakes** risk
semantics into the confidence number as additive heuristics (τ stirred in — the
anti-pattern); the agentic-UQ survey's Appendix E types actions by **LLM-judge
classification** and applies reduction **by fiat** when the type qualifies. Ours keeps
τ outside the number as the interpretation layer, and checks rather than assumes.
Smoke-run corollary: in the belief-locked loop, *no scalar probe* fired (entropy and
verbalized both read "certain") while the **typed trace** flags it trivially
(repeated I=1 actions, identical observations, static U) — the interpretation-layer
thesis demonstrated by accident.

### 2.6 Propagation as reset + promise check (not accumulation)
A successful epistemic action **resolves** the uncertainty that motivated it:
U(q_t | S_{t+1}) is generated fresh from a state already containing the observation.
Prior uncertainty is either resolved (drops) or not (persists — and persistence is the
signal). Propagation is not summing; it is asking **did the transition deliver what
its type promised?** Formally: u_t⁻ = U(q_t|S_t), u_t⁺ = U(q_t|S_{t+1}),
G_t = u_t⁻ − u_t⁺; violation V(t) = 𝟙[G_t ≤ ε] for τ.I = 1.

Named interlocutors:
- **UProp** (the principled opponent): decomposes step uncertainty into intrinsic +
  extrinsic (cumulative MI inherited from preceding decisions). Resolution: different
  random variables. UProp's EU marginalizes over *counterfactual* prior decisions —
  branching variance of the trajectory-generating process. The reset rule reads the
  epistemic state at the **realized prefix** — the only prefix a running agent
  occupies. Both can be true; only the second is readable online (their estimator
  needs Z×N ≈ 100 rollouts/task — disqualifying for online control by construction).
- **TEPO** (convergent evidence, entropy form): segment-entropy delta ΔH_k after tool
  calls tracks judge-scored call quality. Validates the reset intuition with an
  untargeted token probe; the map tests whether targeted elicited deltas read what the
  entropy delta cannot. ΔH_k is E3's champion baseline.
- **InfoReasoner** (theoretical contrast): IG rewards with a non-negativity guarantee
  ("information gathering never hurts") — exactly what the promise check denies at the
  realized step: a failed search delivers nothing, and AUQ's **Delusional
  Confirmation** (reflection inflates confidence most in failures) is negative
  progress that level-based readings cannot distinguish from resolution. The
  exploratory "unearned resolution" arm (large U_T drop under non-informative
  transition) targets both failure modes.
- **AUQ's level-threshold trigger** (ĉ < τ): the deployed mechanism the promise check
  is measured against.

### 2.7 Why measurement and propagation are one paper
They are the same object viewed at t and t+1. Under the pivot this becomes literal
structure: the map's level columns (E1) and delta columns (E3) are the same estimators
read at the two views, and no metric-comparison paper could define the delta column
without §2.5–2.6 — the theory dictates the instrument's shape.

---

## 3. The Pivot: Hypotheses and Kill Switch

The paper's questions (pre-registered, replacing the v1 outcome table):

- **H1 (stage):** metric rankings differ between Thought and Action stages — the
  choice of UQ metric cannot be separated from the agentic object measured.
- **H2 (type):** typed models h(U_T, U_A, τ) beat pooled g(U_T, U_A) out-of-sample
  across **multiple metric families**, not just one probe.
- **H3 (transition):** for epistemic actions, transition deltas beat levels at
  detecting failed information acquisition, for at least one estimator family.
- **H4 (contract):** under the entanglement ablation, token-intrinsic metrics are
  invariant; contract-carrying metrics shift. (Derived from §2.3; family-wise split.)

**Kill switch (replaces "verbalized must beat entropy"):** the study stops only if
ALL fail jointly — no meaningful stage differences (¬H1), typing adds nothing (¬H2),
deltas add nothing over levels (¬H3), and entangled ≡ decoupled for every family
(¬H4). Any single Hᵢ landing is a paper; the conjunction failing is the honest death.
Pre-registered interpretations are frozen at the git tag; post-data changes are
deviation notes, never silent edits.

**Relocated risk, named:** the old bad outcome was "verbalized ≈ entropy." The new
bad outcome is "one metric wins everywhere; rankings stable; map boring" — less bad
(a stable ranking is a result; H2/H3 can still land independently), but real.

**Label framing (conservative, chosen):** quantities are "Thought-stage /
Action-stage uncertainty estimators," not validated epistemic measures. Epistemic
validity is carried by the **perturbation battery** (§6), not by a second annotation
protocol. Strong epistemic labels: future work.

---

## 4. Probe Taxonomy and Metric Roster (rationale)

Four probe classes: **token-intrinsic** (MTE, MaxTE, PPL≡LN-NLL, SP) ·
**contrastive-logits** (progress advantage; feasibility-gated) · **verbalized,
in-generation** (generic; targeted u(q_t), u_A(g_t)) · **post-hoc self-evaluation**
(P(True) — canonical name for the yes/no logprob probe, Kadavath; post-hoc numeric;
verbal-scale in the robustness arm only). Delta family (E3): Δ of any level metric,
plus TEPO's ΔH_k. Adjacent position noted for completeness: UALA's
`MeasureUncertainty`-as-action (uncertainty measurement as an explicit agent step)
— inherits the post-hoc contamination profile.

Notes: PPL and length-normalized NLL are monotone transforms — one row, aliased.
MaxTE catches the single peaked token MTE dilutes (and gives a second lens on
self-conditioning collapse). u_A(g_t) is the **first-person counterpart to CEB's**
P(action productive | pre-execution) — introspective vs critic-estimated, and an
elicited transition prior for E3 (the agent's own Ĝ before the observation).
Sampling/consistency families deferred **with the survey's own §4.1 cost argument**
(prohibitive in long-horizon agentic settings) — a citable boundary, not an excuse.

---

## 5. The Control-on-Unvalidated-Measurement Lineage (motivation)

The field's control stack now rests on instruments nobody has validated at the
granularity the mechanisms assume:

KnowNo (conformal action-set gating) → UALA (answer-level tool switch) → ProbeCal /
SAUP (tool calibration; learned trajectory propagation) → UProp (MI inheritance) →
AUQ (verbalized level-threshold reflection) → reward-shaping family (InfoReasoner,
TEPO, IG-Search, SELAUR — **optimizing agents against uncertainty meters no one has
calibrated**) → Algoverse (heuristic SAUP: **+12–16pp pass@1 at AUROC ≈ 0.5** — the
published proof that task-success gains cannot substitute for measurement validity;
gains are variance exploitation, and every item on their own future-work list needs
the step-level validity their instrument lacks).

The SAUP critique, stated fairly: aggregation is not invalid; learning weights over
**untyped** scalars against the very terminal signal claimed uninformative — that is
the problem. Order reversed here: separate the semantic objects → type the transition
→ check the promise → derive trajectory risk only if needed (the AUQ-comparable
Φ_last/min/avg suite is a supplementary table, never a headline).

---

## 6. Labels, Circularity, and Validity

**Lineage (cite plainly):** PRM step labels (Uesato 2022; Lightman "Let's Verify Step
by Step") → LLM-judge step labels for agents (ReDAct: 2,411 ALFWorld steps, Fig. 9
protocol; TEPO independently judge-scores tool calls) → **judge-validated,
perturbation-backed, typed step labels (ours)**. Only the validation layer is claimed.

Circularity: step claims need step labels; 4/44 benchmarks have them (survey);
prefix-vs-terminal shares one bit across all t. Escape = manufactured labels;
precondition, not downstream, of the claims.

Three validity instruments:
1. **E0 triangle:** local disjoint-family judge (Llama vs Qwen agents — kills
   correlated-plausibility failure) + one frontier pass + two humans on 150 steps
   stratified by τ × loop × architecture; κ enters the paper as the label-noise bound;
   judge rendering is architecture-invariant (actions + observations, no thoughts) so
   label distributions cannot differ by condition.
2. **Perturbation battery (the causal column):** manipulate the observation at I=1
   steps on frozen trajectories — informative / irrelevant / corrupted /
   contradictory / absent — and score every estimator on whether it tracks resolution.
   Label-free construct validity; separates "predicts judge labels" from "responds to
   epistemic evidence" per metric (the built-in Kim & Kang defense: an estimator that
   predicts labels but fails perturbations is exposed as a plausibility meter).
   Design debt to BayesAgent/vPGM's negative control; their 22% clean-set false-flag
   rate is the precedent for reporting over-firing.
3. **Loop handling:** loops are phenomenon and artifact both. Environment-side loop
   definition (repeated (action, observation) pair); loop-collapse fraction as
   covariate; loop-stratified reporting; dedup sensitivity; per-step seeds so
   byte-exact lock (a per-episode-seed artifact) yields to the natural drift-and-fork
   regime. ReDAct's judge rubric explicitly targets cyclic behavior — labels were
   built for this regime.

Kim & Kang hygiene throughout: protocol cards per probe; raw values never compared
across protocols — cells are compared on **within-protocol discrimination**;
parse-rate reporting with fixed imputation; round-number clustering shown, ranking
robustness demonstrated.

---

## 7. Risk Assessment (V2)

1. **Boring-map risk** (new headline risk): rankings stable everywhere → collapses
   toward a single-winner paper. Mitigation: H2/H3/H4 are independent landing zones;
   the released corpus + harness is a durable artifact regardless.
2. **Elicitation pathologies** (unchanged, demoted from existential to row-level):
   rounding, prompt sensitivity, <7B degradation (AUQ limitation; the 4B floor model
   measures the boundary). E1b robustness arm; discrimination and calibration
   reported separately, discrimination leads; ECE only for natively-probabilistic
   metrics.
3. **Plausibility circularity** (probe × judge both plausibility meters): E0
   human-vs-judge discrimination check + perturbation battery.
4. **Thin dangerous quadrant:** ALFWorld's W=1/R=0 cell is thin; WebShop existence
   proof carries it; intro must not outrun the evidence.
5. **Contamination trade (two horns):** instrumented (E1b divergence + the 30-task
   with/without-instruction ablation), not argued.
6. **Window:** Sharon Li's group holds the survey (field agenda), Appendix E (the
   framework sketch, likely being implemented), Progress Advantage (strongest rival
   probe), and τ²-bench infrastructure — one group, one building. The conversation
   with Changdae Oh sets the real deadline. CEB (2607.12397, 2 days old at triage) is
   the one load-bearing citation not yet fully read — internals provisional.

---

## 8. Positioning

### 8.1 Organize related work by the object each method estimates

| Family | Object estimated |
|---|---|
| SAUP / UProp | trajectory risk; inherited (counterfactual-branching) uncertainty |
| ReDAct / CEB / Progress Advantage | action quality / step productivity |
| AUQ / Matsnev / TrustEHRAgent | verbalized or decomposed step confidence |
| InfoReasoner / TEPO / IG-Search / SELAUR | uncertainty-reduction as training reward |
| Survey App. E / SAGE-Agent / clarification work | action-conditional gating (sketch / user-goal setting) |
| Kim & Kang / STAPO / ProbeCal | probe/protocol validity critiques |
| **This work** | **typed epistemic transition fulfillment, measured stage-wise** |

### 8.2 What each near neighbor did and didn't
- **ReDAct**: the coordinate system's prior art — two-call split, stage contracts,
  step judge labels; probed with format-blind token metrics only; concluded
  reasoning-level UQ uninformative. We generalize (cross-metric, typed, delta) rather
  than defeat one number; anchor demoted to pipeline-sanity signal.
- **AUQ**: in-generation verbalized in agents, entangled, trajectory-validated;
  level-threshold System 2; Delusion Gap. Their probe = our entangled verbalized row,
  verbatim template.
- **Survey (ACL 2026, Li group)**: names theoretically-grounded verbalized confidence
  as *the* promising direction (§4.1 — gift quote); Appendix E = unevaluated
  conditional-reduction sketch with LLM-classified types and by-fiat gating; their
  Table 2 = one more aggregated-verbalized-near-chance datapoint; "evaluation beyond
  task failure" open problem = our protocol's answer.
- **UProp / TEPO / InfoReasoner / PA / Kim & Kang / UALA / Algoverse / vPGM / STAPO /
  CEB**: as placed in §§2.4–2.6, 4–6.

### 8.3 The gap that survives (conjunction; claim no component)
> Prior work estimates whether an action will succeed or whether uncertainty changed.
> **We test, stage-separated and per estimator, whether a typed action resolved the
> specific uncertainty that justified taking it** — validated against step labels and
> causal perturbations. No prior framework combines stage-separated measurement,
> cross-metric comparison, environment-derived transition typing, and same-target
> promise checking; and no prior work provides the judge-validated,
> perturbation-backed, typed step-label corpus this requires.

### 8.4 Deliverables
(1) the framework (typed 𝒰_t, promise check); (2) the metric-by-stage-by-type map
with the perturbation-validity column; (3) H1–H4 verdicts; (4) the released harness +
labeled corpus (durable against scooping); (5) mechanistic account of
reasoning-entropy failure (self-conditioning collapse).

---

## 9. Framework → Experiment Map

| Framework element | Where tested | Pre-registration |
|---|---|---|
| Stage separation matters (§2.2) | E1 map | H1 |
| Contract, not split, does the work (§2.3) | E1b ablation | **H4 (invariance/shift)** |
| τ as interpretation layer (§2.5) | E2 typed-vs-pooled, per family | H2 |
| Reset / promise check (§2.6) | E3 delta comparison + perturbation battery | H3 |
| Probe-class distinctions (§2.4) | rows of every table | descriptive |
| Validity (§6) | E0 triangle + perturbation battery + loop stratification | decision rules frozen |

Controller (E4-class closed-loop) is explicitly **out of scope** — one future-work
paragraph; it is the follow-up paper this instrument exists to enable.
