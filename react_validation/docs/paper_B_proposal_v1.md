# Conference Paper Proposal — Paper B
## Judging the Step, Not the Answer: A Training-Free LLM-Judge Protocol for Uncertainty Quantification in Agentic Systems

**Taehyun Park · UW–Madison CS · Paper-B v3 (amortized-metrology reframe), 2026-08-03** (v3 changes in §12; v2 changes in §13)

---

## 0. Shape of the paper

A methods paper built on one argumentative spine:

> **distinct setting (P1) → agent-side characterization never amortizes (P2) →
> so fix the instrument: one known, characterized-once judge (P3) — specified
> concretely (P4) → the instrument should be external (P5, empirical
> selection), its characterization transfers (P6, thesis validation), it's
> veridical (P7), its biases are known (P8) → deployable (P9).**

The thesis is **amortized metrology**: a measurement device does not need to
be different from the object it measures — it needs to be *known*. One method
(**the judge protocol**), three validations (**recipe-invariance as thesis
validation / instrument selection / veridicality**), one adversarial
characterization (**the bias battery**), one compressed motivation
(**non-transfer**, one section, one figure). The corpus ships as supporting infrastructure. Every validation
number is computed against environment-anchored or human-adjudicated targets;
judge-ensemble labels are an adjudication layer only and never validate the
proposed judge.

## 1. Problem [P0 + P1]

LLM agents fail mid-trajectory — looping, acting on wrong beliefs, committing
irreversible mistakes — and reliable deployment requires knowing, per step and
online, whether the next action should be trusted. Object of study: step-level
online UQ per CEB's formulation (pre-execution estimation of whether a
proposed action will be productive given task information, state, and
history), extended by τ typing beyond the pre-execution point. Step
correctness is far easier to verify in hindsight than online; good step-level
UQ closes that knowledge gap, which we measure directly (hindsight ceiling,
§8.vi).

**Agentic UQ is structurally distinct from QA UQ** — six measured receipts:

1. The judged object has no intrinsic truth value: an action string scored
   alone is chance (AUROC 0.512); step quality is relational to state.
2. Evidence is environmental and temporal, with a measured hierarchy: history
   buys 0.512→0.697; the realized observation is the largest single gain
   (+0.070 paired ΔAUROC); the agent's own reasoning adds least and is
   dispensable.
3. The environment supplies typed structure (τ = information /
   world-modifying / reversible / cost) — an invocation and evidence policy
   no QA judge has.
4. Assessment is online and per-step, making cost first-class (prefill +
   1 token; 3,300 assessments ≈ 5 min on one A100).
5. The detected failures are agentic: loops, stagnation, cap-failures carry
   40–87% of error mass, no QA analog.
6. Ground truth is consequence-anchored, not preference-anchored.

Consequence: QA-validated metrics and QA judging results cannot be assumed to
port. The question "what works here?" is open.

## 2. Motivation: no self-derived signal is configuration-independent [P2]

Across ~30k labeled steps (4 families, 4B–70B, ALFWorld + HotpotQA, entangled
+ decoupled generation): the best self-derived metric and its winning scope
are a function of (model, dataset, architecture) — flips across every axis,
recipe transfer costs up to −0.10 AUROC, trained meta-models equally
irregular. **P(True) is reported as the strongest surviving candidate that
still fails the bar**: best or tied in 7/8 arms, recipes transfer at −0.016 —
yet its winning scope flips by model family and it requires agent logprob
access many deployments lack. Variation is lawful (rankings cluster by
architecture × capability tier) but no configuration-independent winner
exists in the tested space. Claims are bounded to that space; the word
"impossible" appears nowhere.

Methodological floor, not headline: trajectory-level evaluation is
length-confounded (length-only AUROC ≈ 1.0 on cap-dominated benchmarks), so
every measurement in this paper is step-level.

Consequence: the metric search restarts with every deployment. The metric is
not the fixable variable.

## 3. Diagnosis and thesis [P3]

**Diagnosis: characterization cost never amortizes on the agent side.** The
non-transfer result (§2) means every new agent × task deployment restarts the
metric search: the best signal, its recipe, and its scope must be
re-discovered per configuration. Worse, the agent side is the wrong place to
invest characterization even when affordable — agents churn (new releases,
fine-tunes, swapped backbones), and closed frontier agents cannot be
intrinsically characterized at all (no logprob access). The fixable variable
is not the metric but the **instrument**.

> **Thesis: agent-step uncertainty should be estimated with a fixed,
> well-characterized measurement instrument — one capable LLM judge whose UQ
> behavior (elicitation recipe, evidence policy, biases, calibration) is
> characterized once and then deployed across arbitrary generation models,
> under a specified protocol: reading environment-grounded evidence, scoring
> prompted P(True)-style trust per step, invoked selectively via
> environment-derived action typing.**

This is a metrology argument, not an independence argument: a thermometer
need not differ in kind from what it measures — it must be *known*. Fixing
the judge collapses the variability space from (agent × task × metric) to
(task-type), and the characterization investment amortizes across every
generator the judge is pointed at. The amortization premise is not asserted —
it is the paper's central validation target (**judge-recipe invariance**,
§7). Whether the instrument should be *external* rather than the agent's own
self-probe is a separate, empirical instrument-selection question (§6), not
part of the thesis.

Deployment asymmetry made explicit: **white-box judge, black-box agent.** The
judge uses its own logprobs (prompted P(True) on its own forward pass — any
open-weight model suffices); the *agent* requires no internal access, so the
methodology applies to closed frontier agents, which no intrinsic method can
serve — and which no agent-side characterization program can even begin on.

## 4. The judge protocol [P4] (the method — one methodology, two components)

Without a specified estimator, "use a judge" is unfalsifiable advice.
Internal hierarchy resolved by data: the **evidence grid** specifies *what
the judge reads*; the **τ policy** specifies *when it is invoked and with
which grid rows*. If gating curves confirm τ's value, τ headlines and the
grid is its substrate; if not, the grid headlines and τ reduces to the
pre/post-execution split. The proposal commits to the conditionality.

**(a) Evidence grid.** The judge's prompt is a policy over evidence classes —
*prior* (task rules), *process* (history, reasoning, action), *realized* (the
produced observation) — characterized by paired, decoy-controlled ablation
(n=300 × 11 conditions, scaling to full corpora). Established: history is the
signal carrier; a **relevant** rule adds discrimination (+0.072, beating a
decoy floor by +0.086) while a merely-stated rule only shifts level; rules
manufacture false positives on rule-adjacent correct steps (+0.155 on
legitimate revisits). Rule-augmented judges are reported against a decoy
floor with their false-positive rate.

**(b) τ-indexed evidence & invocation policy.** Reversible (R=1): assess
post-observation with realized evidence (one-step latency, near-zero cost in
loop-dominated regimes). Irreversible (R=0): assess pre-execution,
substituting prior evidence (targeted rules); the measured gap on matched
steps is the **cost of irreversibility** (~0.07 AUROC upper bound;
rule-recoverable fraction to be measured). Invocation gated by τ and budget:
always on irreversible/costly steps, never on cheap reads — evaluated as
budget-vs-detection curves against uniform gating. Decision-theoretic
one-liner (theory floor): invoke when expected loss of an unassessed error
exceeds assessment cost.

**Cost properties (design property, not contribution).** Prefill + 1 token;
KV-shared self-probing near-free; external judging amortized by τ-gating;
local recipe calibration saturates at ~200 labeled steps (96–99.9%
retention). One paragraph plus a cost column in the results table.

## 5. Ground truth (circularity firewall)

The paper proposes an LLM judge; no LLM-judge-derived label validates it.

1. **Primary validation targets are environment-anchored**: task success,
   state predicates, loop/stagnation detection, cap events. All headline
   numbers are computed against these.
2. **A human-adjudicated gold subset** covers steps without environment
   anchors, is reported separately, and doubles as the veridicality target
   (P7, §8.v).
3. **The 3-judge ensemble** (families disjoint from the proposed judge and
   all agents) exists only as a corpus-construction adjudication layer.
4. **Prefix-only information asymmetry** enforced for all pre-execution
   claims; hindsight ceiling reported as one figure.

Any unified-v3 headline number computed against ensemble labels is recomputed
under (1)–(2) before submission — gate 1, the first scheduled task (§10).

## 6. Validation I — instrument selection: the instrument should be external
[P5; gates 1–2]

Given the thesis "fix a known instrument," the empirical question this
section answers is *which* instrument: the agent itself (self-probe, KV-free,
cheapest) or an external capable model. It is a selection result subordinate
to the thesis, not the thesis itself.

**Banked**: a Qwen-35B judge probing frozen trajectories of 4B-class agents
beats their best self-assessment in 4/4 arms, +0.02 to **+0.28** AUROC
(0.82–0.91 vs self at 0.53–0.64) — pending gate-1 recomputation. Extends
Kapoor et al.'s QA finding to the agentic setting, training-free and
prompted. The one-line explanation (theory floor): the self-assessor
conditions on the same posterior that produced the error — an explanation of
the empirical finding, not a premise of the argument.

**Pre-registered claim-strength ladder** (sets the scope of the
instrument-selection *recommendation*; the thesis does not ride on it):

- **(a) Weak**: strong judge beats weak agents' self-best. Licensed by the
  banked 4/4 arms surviving gate 1.
- **(b) Non-degenerate**: the margin is not purely loop/stagnation detection.
  Licensed by loop-stratified decomposition. A purely degenerate-regime
  instrument is not a credible instrument — this rung remains required.
- **(c) Strong**: the external instrument wins even at matched/superior
  agent capability. Licensed by peer arms (4B judging 4B) and the strong
  model's self-diagonal vs its own external reading.

Failure modes, re-graded under the metrology framing: below (b) → the
selected instrument isn't credible → fallback to Paper A. (c) failing changes
only the recommendation's scope — "prefer the external instrument for the
deployed capability range; at frontier-judge-equals-agent scale, a
well-characterized self-probe is admissible" — with **no consequence for the
thesis**, since amortized characterization never claimed independence as
necessary. This wording contingency is pre-registered here.

## 7. Validation II — the thesis itself: characterization transfers
[P6; judge-recipe invariance — the paper's central result]

The thesis claims characterization amortizes: invest once in knowing the
judge, apply everywhere. That is exactly what this section tests, and it
simultaneously closes the self-defeat trap (*"you claim no metric
generalizes, then rely on the judge's recipe generalizing — why is the judge
exempt?"*): the judge is exempt iff its characteristics are stable across
probed agents — an empirical claim, tested as the paper's headline result.

**Judge-recipe invariance**: within the prober × agent matrix, does the fixed
judge's best elicited recipe (probe format, evidence rows, calibration) stay
stable across all probed agents, with local calibration saturating at ~200
steps? Reported as its own table — the paper's Table 1. The contrast figure
is the thesis in one image: agent-side best-metric assignments scattered
across the matrix (§2) vs judge-side recipe constancy down a column. Plus
trait characterization: clustering of agent-side variation by architecture ×
capability tier; judge-size curve (4B → 70B → frontier) testing *whether* a
capability knee exists — characterization, not law, at n=4 families.

Failure mode: recipes flip per probed agent → the thesis is falsified as
stated; the paper survives only as A. Gate 2′ is therefore the **thesis
gate** — the single most load-bearing result in the paper.

## 8. Evaluation plan [P5–P8 consolidated]

Frozen-corpus probe passes only (no agent regeneration):
(i) **prober × agent matrix** — self-diagonals, peer, upward probing,
judge-size curve; yields §6's ladder and §7's invariance table;
(ii) **evidence grid under external judges**, both benchmarks;
(iii) **loop-stratified decomposition** of all gains;
(iv) **τ-gating budget-vs-detection curves** vs uniform gating;
(v) **veridicality** [P7]: judge-vs-gold agreement against
self-assessment-vs-gold on the same human-adjudicated steps — answers "is the
judge right, not just discriminative?" independently of environment anchors;
(vi) **hindsight ceiling** — same judge, prefix-only vs full-trajectory
context, one figure bounding any online estimator;
(vii) **bias battery** [P8]: perturbation battery; rule-induced false
positives with decoy floors; the judge's own length/format/position
sensitivity — the construct-validity analysis agentic judging lacks;
(viii) **punchline table**: best-intrinsic vs judge at the empirically chosen
size, AUROC × cost per step.

Validity rules: judge families disjoint from label trio and agent set;
prefix-only asymmetry for pre-execution claims; fixed-scope primary
reporting; cross-corpus AUROCs compared as problems, not judges.

## 9. Paper structure (printable skeleton; P-nodes in brackets)

1. **Introduction** [P0–P3 compressed] — problem; transfer-matrix inset
   figure; diagnosis; thesis; contributions.
2. **Related work / positioning** — LLM-as-judge for text (MT-Bench lineage:
   bias-taxonomy structure as precedent; §1's receipts as the structural
   departure); Kapoor et al. (direct precedent, extended training-free);
   CEB (shared formulation, departed estimator); guideline-grounded
   verification (one grid cell); UALA/SAUP/MATU (trajectory-level, offline);
   [2511.07364] (step-level, self-evaluation); agentic-UQ survey (typing as
   uncertainty model vs our estimator policy); Tian et al. reconciliation
   (three axes, explicit).
3. **Setting and motivation** [P1–P2] — six receipts; non-transfer section
   with P(True)-as-best-witness framing; length-confound floor.
4. **Diagnosis and method** [P3–P4] — amortization argument (fix the
   instrument, characterize once); the protocol (grid, τ, cost);
   conditioning-posterior one-liner deferred to the §6 selection result.
5. **Experimental setup** [P0, §5] — corpus/harness (supporting); firewall;
   arm space; validity rules.
6. **Results** [P5–P7] — invariance table (Table 1) + scatter-vs-constancy
   contrast figure + trait characterization; instrument-selection ladder;
   grid results; gating curves; veridicality; hindsight ceiling; punchline
   table.
7. **Judge bias and construct validity** [P8] — battery, decoy floors,
   sensitivity analyses.
8. **Discussion** [P9] — white-box-judge/black-box-agent deployment argument
   (the only UQ route for closed frontier agents); tiering takeaway; τ
   decision-theoretic framing; limitations (two benchmarks, open-weight
   range, ladder-dependent claim scope); control loop as future work
   (taxonomy paragraph + budget curves as the deployment-readiness answer).
9. **Conclusion + artifact statement** [P10] — protocol spec, harness, corpus.

## 10. Contributions (exactly three)

1. **The judge protocol**: evidence-grid + τ-indexed invocation as one
   specified, training-free methodology for agent-step UQ, with
   typing-as-estimator-policy as the unclaimed core (§4).
2. **Amortized characterization, validated**: the fixed judge's recipe is
   invariant across probed agents while agent-side best metrics scatter
   (judge-recipe invariance, §7 — the thesis result), and the instrument
   should be external — an external prompted judge beats self-assessment
   against environment-anchored and human-adjudicated targets (ladder §6),
   reinterpreting the capability floor as an instrument property.
3. **Characterization**: the measured evidence hierarchy, rule
   false-positive/decoy-floor analysis, veridicality result, and judge bias
   battery — the construct-validity analysis agentic judging lacks (§4a,
   §8.v, §8.vii).

Corpus and harness released as supporting artifacts, not claimed.

Out of scope (follow-up): closing the control loop (continue / verify /
replan / defer / block beyond a taxonomy paragraph); promise-check
propagation; trained judge variants; trajectory-level aggregation
(length-confounded; overlaps typed-aggregation work); deployment-validated
tiering; theory beyond the stated floor.

## 11. Status, timeline, and gates

Banked: motivation corpus and map; transfer matrix; sample-efficiency
curves; evidence-ladder prototype (self-probe, one arm); independence
go/no-go (4/4, vs ensemble labels). Remaining (~3–4 weeks, offline):
**[gate 1, first task] environment-anchored + gold recomputation of headline
numbers**; prober × agent matrix (peer, upward, size curve, **invariance
table**); external-judge evidence grid; loop stratification; gating curves;
veridicality pass; hindsight ceiling; adjudication pass; bias battery;
writing.

**Gates (checkpoint 2026-08-14), re-graded under the metrology framing:**
- **Gate 1 — circularity**: headline margins survive environment-anchored
  recomputation. Fail → fallback A.
- **Gate 2′ — invariance (THE THESIS GATE)**: judge recipes stable across
  probed agents. Fail → thesis falsified as stated → fallback A.
- **Gate 2 — instrument credibility**: ladder reaches rung (b) at minimum,
  with (c) probed. Fail below (b) → the selected instrument isn't credible →
  fallback A. (c) fails, (b) holds → pre-registered scope narrowing of the
  instrument-selection recommendation only; **no thesis consequence**; paper
  proceeds.
- **Gate 3 (soft) — τ**: gating curves show a knee vs uniform. Fail → τ
  demotes to the pre/post split; grid headlines.

External dependency (critical path): typed-aggregation appendix scope in
adjacent in-department work must be confirmed before τ and out-of-scope
claims freeze — conversation due this week.

## 12. Changelog (Paper-B v3, 2026-08-03) — amortized-metrology reframe [A24]

- **Diagnosis reframed** (§3): from "self-assessment is epistemically
  defective (independence essential)" to "agent-side characterization never
  amortizes (knownness essential)" — the thesis is amortized metrology; a
  measurement instrument must be known, not necessarily different from what
  it measures. Correction of a framing divergence between drafts, per
  Taehyun's original intent.
- **Judge-recipe invariance promoted to thesis validation** (§7, Table 1);
  gate 2′ renamed the thesis gate. Contrast figure specified: agent-side
  metric scatter vs judge-side recipe constancy.
- **Independence demoted to instrument selection** (§6): an empirical result
  answering *which* instrument, subordinate to the thesis. The
  conditioning-posterior argument demoted from diagnosis to one-line
  explanation of the selection finding.
- **Gate 2 re-graded**: rung (b) still hard-required (instrument
  credibility); rung (c) failure now carries no thesis consequence — scope
  narrowing of the recommendation only, pre-registered wording in §6.
- Contribution 2 reworded: "amortized characterization, validated"
  (invariance headlining, selection supporting).
- §0 spine updated accordingly.

## 13. Changelog (Paper-B v2, 2026-08-03) — logical-chain restructure

- Restructured around the P0–P10 spine; §0 states it; §9 maps sections to
  P-nodes.
- **Judge-recipe invariance** promoted to a named result with its own table
  and hard gate (2′) — closes the self-defeat trap; no new compute (lives in
  the prober × agent matrix).
- **White-box judge / black-box agent** correction: judge may use its own
  intrinsic signals; "elicited-only" framing removed; deployment argument
  sharpened to "only UQ route for closed frontier agents."
- **Veridicality** (judge-vs-gold vs self-vs-gold) added as §8.v via the
  existing gold subset — zero marginal annotation; partial reversal of the
  human-audit drop, logged as amendment.
- **Claim-strength ladder** for independence pre-registered (§6) with fixed
  licensing comparisons and wording contingencies.
- P(True) reframed as prosecution's-best-witness in §2 — reported honestly,
  never a contribution.
- Theory floor fixed: coupling paragraph + τ decision-theoretic one-liner;
  nothing more (theory-diet preserved).
- Control loop confirmed out of scope; downstream-utility question answered
  by budget curves + taxonomy paragraph in discussion.
- Contribution 2 widened to include the invariance result (independence +
  decoupling as one validated claim).



Experiments needed by arguments.
---

**Argument 1. Judging an agent's step is a different problem from judging a QA answer.**
*Plain claim*: you cannot tell if an agent's action is good by looking at the action alone — you need context from the environment; and the ways agents fail (loops, acting on stale beliefs) don't exist in QA.
*What convinces a skeptic*: show it holds for every model and both task types, not one setup.
*Experiment — the evidence law*: for all agents on all datasets, score the same steps while adding evidence one layer at a time: action only → + history → + agent's reasoning → + what the environment actually did in response. **General characteristic sought**: the same ordering everywhere — action-alone ≈ coin flip, environment response = biggest jump, agent's reasoning ≈ negligible. If that ordering holds across every arm, "step quality is relational to environment" is a law of the setting, not an anecdote.
*One picture*: one line per arm, all rising in the same shape.

**Argument 2. There is no best metric — the best metric is a property of the (model, dataset) pair.**
*Plain claim*: whichever uncertainty signal you pick, it's the winner in some cells and mediocre in others; the *pattern of who-wins-where* is the finding.
*What convinces a skeptic*: an exhaustive grid, not a survivor story.
*Experiment — the metric map*: every metric × every model × every dataset, one AUROC per cell; mark the winner per cell; then quantify what the winner-pattern correlates with (model family? size tier? dataset type? generation architecture?). **General characteristic sought**: winners scatter across cells, *but the scattering itself is systematic* — it clusters by model traits, meaning best-metric is a stable *trait of a model*, discoverable per model but not universal.
*One picture*: the grid with winner-colored cells — visibly no single color dominating, but colors clustering in blocks.
This is the hinge to Argument 3: if best-metric is a per-model trait, then knowing a model's UQ traits deeply is valuable — so pick one model and know it completely.

**Argument 3 (THESIS). Characterize one judge model thoroughly, then reuse it on any agent.**
*Plain claim*: instead of re-discovering the best signal for every new agent, learn everything about one judge's UQ behavior once — its best prompt recipe, what evidence it needs, its calibration — and that knowledge keeps working no matter which agent it inspects.
*What convinces a skeptic*: the direct contrast with Argument 2. Agent-side: the best setup changes every time you change the model. Judge-side: the best setup *doesn't* change when you change what's being judged.
*Experiment — the invariance test*: fix the judge; have it assess every agent on every dataset; for each judged agent, independently find the judge's best recipe (probe format, evidence combination, calibration). **General characteristic sought**: the judge's best recipe is (approximately) the same in every column — it's a trait of the judge, invariant to the target. Also: how much labeled data does adapting the judge to a new agent need (already known: saturates ~200 steps — i.e., adaptation is cheap, characterization amortizes).
*One picture*: Argument 2's scattered grid next to the judge's constant column — the entire thesis in two panels.
*Honest failure condition*: if the judge's recipe flips depending on who it judges, the thesis is wrong and we say so.

**Argument 4. The instrument should be an external model, not the agent grading itself.**
*Plain claim*: models are bad at grading their own steps while they act, and this isn't just "small models are dumb" — even holding capability equal, an outside reader does better.
*What convinces a skeptic*: separating two explanations that are usually confounded — "the judge is just smarter" vs "outside perspective itself helps."
*Experiment — the full reading matrix*: every model reads every model's trajectories, including itself — strong-reads-weak, weak-reads-weak (peer), weak-reads-strong (upward), and each model reading itself. **General characteristics sought**: (i) external reading beats self-reading in general, including at equal capability (peer cells vs self-diagonal); (ii) how the advantage scales with judge capability — is there a size where a judge becomes "good enough" (the knee)? (iii) the advantage isn't only from catching trivial loops — split every gain into loop-steps vs genuine-reasoning-steps and require the advantage to survive in the second group.
*One picture*: the reader × target matrix with the self-diagonal visibly the weak stripe.

**Argument 5. The judge isn't just consistent — it's *right*.**
*Plain claim*: high AUROC could still mean "agrees with our automated labels." The real question: when humans look at a step and say it's wrong, does the judge agree with the humans more than the agent's self-assessment does?
*Experiment — the human alignment check*: on the human-adjudicated subset of steps, measure judge-vs-human agreement and self-assessment-vs-human agreement on the *same steps*, for all arms. Additionally, all headline numbers in Arguments 3–4 are computed against environment-verified outcomes (task actually failed, loop actually happened), never against another LLM's opinion — so the whole chain is anchored outside LLM-land.
*One picture*: paired bars per arm, judge vs self, both measured against humans.

**Argument 6. We hand over the judge with its operating manual — general rules for using it.**
*Plain claim*: a measurement instrument is only trustworthy if its error modes and operating conditions are documented. We document them as *general rules*, not incidents.
*Experiments — the manual*:
- *When to invoke*: gate the judge by action type (irreversible/costly → always check, before acting; cheap/reversible → check after seeing the result, or skip). **General characteristic sought**: at any fixed inspection budget, type-aware gating catches more failures than inspecting uniformly at random — shown as a curve over budgets, both datasets.
- *Known biases*: feeding the judge task rules helps only when the rule is actually relevant (an irrelevant decoy rule does nothing) and creates a specific, predictable false alarm (flagging legitimate revisits) — quantified so users can anticipate it. Plus systematic perturbations (reordering, formatting, length) to bound the judge's sensitivities.
- *What it costs*: one prefixed token per check; adapting to a new agent ~200 labeled steps — the practical numbers a deployer needs.
*One picture*: budget-vs-detection curves, gated above uniform.

---

The chain in one breath: **steps are judged by environment context, not content (1) → no universal signal exists, but signal-preference is a stable model trait (2) → so invest in knowing one judge's traits completely and reuse it everywhere (3) → that judge should be external (4) → it agrees with humans (5) → and here's its manual (6).**

Nothing in the previous plan's compute changes — these are the same runs, re-grouped so each experiment answers a general question with a single legible pattern. The gates map: Argument 3's invariance = thesis gate; Argument 4(iii) non-triviality = credibility gate; Argument 5's environment-anchored recomputation = circularity gate.