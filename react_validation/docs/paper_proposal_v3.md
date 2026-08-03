# Conference Paper Proposal
## Judging the Step, Not the Answer: An LLM-as-Judge Methodology for Uncertainty Quantification in Agentic Systems

**Taehyun Park · UW–Madison CS · Draft v3 (conference framing), 2026-08-03** (v3 changes in §11)

---

## 0. Shape of the paper

Four pillars, one line each: a negative result motivates (**impossibility**),
a positive result delivers (**independence**), a method enables (**the judge
protocol**), an artifact remains (**the corpus**). Everything else in this
document is a property, a receipt, or discussion — not a contribution claim.

## 1. Problem

LLM agents fail mid-trajectory — looping, acting on wrong beliefs, committing
irreversible mistakes — and reliable deployment requires knowing, per step and
online, whether the next action should be trusted. The field's instruments for
this are intrinsic uncertainty metrics (token entropy, sequence probability,
verbalized confidence, P(True)) and, increasingly, trained meta-models. Both
presuppose that some signal, once found, transfers across models and tasks.

The online setting has a structural difficulty worth naming plainly: step
correctness is far easier to verify in hindsight than to estimate in the
moment. Given the completed trajectory and outcome, a step's contribution is
nearly evident; at time *t*, with only the prefix, it is not. Good step-level
UQ is the closing of this knowledge gap between the online estimator and the
hindsight verifier — a gap we measure directly with a hindsight-ceiling
comparison (§7.vi). This framing is consistent with the field's reliance on
failure- and consequence-anchored labels, which are hindsight verdicts.

## 2. Motivating result: there is no such signal

Across ~30k judge-labeled agent steps (4 model families from 4B to 70B, ALFWorld
+ HotpotQA, ReAct-style agents), we find:

- **No intrinsic metric transfers.** The best metric and its scope flip across
  models and benchmarks; recipe transfer costs up to −0.10 AUROC; trained
  meta-models show the same irregularity (consistent with published escalation
  predictors). Variation is lawful — rankings cluster by configuration and
  capability tier — but no universal winner exists.
- **Trajectory-level evaluation is confounded.** On cap-dominated benchmarks,
  episode length alone reaches AUROC ≈ 1.0; no aggregated metric beats it. Step-
  level evaluation is the only meaningful granularity — and only 4/44 agent
  benchmarks provide step labels (per the field's own survey).
- **Self-assessment has a capability floor.** Below ~7B, every self-derived
  signal sits near chance (0.53–0.64); in-generation verbalized confidence is
  the worst instrument everywhere.
- **P(True) is the most robust single probe** (best or tied in 7/8 arms; its
  recipes transfer at −0.016 mean loss) — but its winning scope is
  model-dependent, and it requires logprob access many deployments lack.

The search for the ultimate metric fails empirically. We propose to stop
searching and change the estimator instead.

## 3. Thesis

> **Agent-step uncertainty should be estimated by an independent, capable LLM
> judge operating under a specified protocol — reading environment-grounded
> evidence, scoring prompted P(True)-style trust per step, and invoked
> selectively via environment-derived action typing — rather than extracted
> from the acting model's internals.**

The claim is not that the judge is universally calibrated by default (cf.
LLM-as-judge for text), but that a well-specified judge protocol is the
practical, model-agnostic methodology for a setting where no intrinsic signal
transfers.

## 4. Why the agentic setting is the novelty (not a domain swap)

Judging agent steps is structurally different from judging answers, with a
measured receipt per difference:

1. **The judged object has no intrinsic truth value.** An action string scored
   alone is chance (AUROC 0.512). Step quality is relational to state — the QA
   judging problem does not port.
2. **Evidence is environmental and temporal, with a measured hierarchy.**
   Trajectory history buys 0.512→0.697; the environment's realized response to
   the action is the largest single gain (+0.070 paired ΔAUROC); the agent's
   own reasoning adds least and is dispensable — enabling black-box operation.
3. **The environment supplies typed structure (τ = information/world-modifying/
   reversible/cost).** τ gives the judge an invocation policy and an evidence
   policy no QA judge has (Sec. 6). Nearest antecedent: the agentic-UQ survey
   classifies actions (interactive/evidential) to *model* uncertainty reduction
   via an information-gain term. No prior work uses action typing to *gate
   judge invocation and evidence selection* — typing as estimator policy, not
   as uncertainty model, is ours.
4. **Assessment is online and per-step**, making cost a first-class property:
   the probe is prefill + 1 token (measured: 3,300 assessments in ~5 min on one
   A100; near-free with KV prefix sharing when judge = agent).
5. **The detected failures are agentic**: loops, stagnation, cap-failures carry
   40–87% of the error mass and have no QA analog.
6. **Ground truth is consequence-anchored**: 3-judge ensemble labels with human
   adjudication of disagreements, plus environment-anchored targets — and the
   released labeled corpus is the artifact the field lacks. Per-step
   inter-judge agreement rates ship with the corpus as metadata.

## 5. Core empirical result (go/no-go: passed)

**Generation–assessment independence pays.** A Qwen-35B judge probing frozen
trajectories of 4B-class agents beats those agents' best self-assessment in 4/4
arms, by +0.02 to **+0.28** AUROC (reaching 0.82–0.91 where self-reading sits
at 0.53–0.64). This reinterprets the capability floor: small agents are not
unreadable — they are bad self-readers; readability is a property of the
estimator. It extends the published QA finding that one strong model can
estimate others' uncertainty (Kapoor et al.) to the agentic setting,
**training-free and prompted** rather than fine-tuned.

## 6. The judge protocol (one methodology, two components)

The protocol is a single methodological contribution with two components and
an explicit internal hierarchy to be resolved by the data (§10): the
**evidence grid** specifies *what the judge reads*; the **τ policy** specifies
*when the judge is invoked and with which grid rows*. If τ-gating's budget
curves confirm its value, τ headlines and the grid is its evidence-selection
substrate; if not, the grid headlines and τ reduces to the pre/post-execution
split. The proposal commits to the conditionality, not to both at full weight.

**(a) Evidence grid.** The judge's prompt is a policy over evidence classes —
*prior* (task rules), *process* (history, reasoning, action), *realized* (the
observation the action produced) — characterized by a paired, decoy-controlled
ablation (n=300 × 11 conditions, scaling to full corpora). Established so far:
history is the signal carrier; a **relevant** rule adds discrimination (+0.072,
beating a decoy floor by +0.086) while a merely-stated rule only shifts level;
rules manufacture false positives on rule-adjacent correct steps (+0.155 on
legitimate revisits). We therefore recommend reporting rule-augmented judges
against a decoy floor with their false-positive rate, and follow this practice
in all our own reporting.

**(b) τ-indexed evidence & invocation policy.** Reversible steps (R=1): assess
post-observation with realized evidence (one-step detection latency, near-zero
cost in loop-dominated failure regimes). Irreversible steps (R=0): assess
pre-execution, substituting prior evidence (targeted rules). The measured gap
between the two on matched steps is the **cost of irreversibility** (~0.07
AUROC upper bound; rule-recoverable fraction to be measured). Invocation is
gated by τ and budget: always on irreversible/costly steps, never on cheap
reads — evaluated as budget-vs-detection curves against uniform gating.

**Cost properties (not a contribution — a property of the design).** Prefill +
1 token per assessment; KV-shared self-probing near-free; external judging
priced per step and amortized by τ-gating; local recipe calibration saturates
at ~200 labeled steps (96–99.9% retention). These appear as one paragraph and
a cost column in the results table. A practical tiering note — intrinsic
P(True) where logprobs and capability allow, gated external judge where they
don't — belongs in the discussion section as a takeaway, not among the claims.

## 7. Evaluation plan

Frozen-corpus probe passes only (no agent regeneration): (i) full prober ×
agent matrix — self-diagonals, peer and upward probing (does external reading
help equals/superiors or only weaker agents?), and a judge-size curve
(4B → 70B → frontier) testing *whether* a judge-capability knee exists and, if
so, where; (ii) evidence grid under external judges, both benchmarks;
(iii) loop-stratified decomposition of all gains (general signal vs
degenerate-regime detection); (iv) τ-gating budget curves; (v) the punchline
table: best-intrinsic vs external judge (at the empirically chosen size),
AUROC × cost per step; (vi) **hindsight ceiling** — the same judge scoring the
same steps under full-trajectory hindsight context vs prefix-only online
context, measuring the §1 knowledge gap; one figure, reusing the
prefix-asymmetry harness. Validity: judge families disjoint from label-judge
trio and agent set; prefix-only information asymmetry for pre-execution
claims; environment-anchored targets and a human-adjudicated gold subset
against judge-judging-judges circularity; a perturbation battery as the
judge's construct-validity/bias analysis (MT-Bench-style); fixed-scope primary
reporting; cross-corpus AUROCs compared as problems, not judges.

## 8. Positioning (each clause vs its nearest neighbor)

Training-free prompted (vs Kapoor's fine-tuned QA estimator; CEB's
experience-bank critic; supervised escalation predictors) · step-granular
online (vs UALA/SAUP/MATU trajectory verdicts — tensor-decomposition methods
additionally require the full trajectory embedding and are offline by
construction; vs guideline-accumulation's aggregated end-of-trajectory check;
stepwise self-confidence work [2511.07364] independently finds step-level
scoring improves error detection, supporting the granularity claim while
remaining self-evaluation) · evidence-grid characterized (vs single-evidence
guideline grounding — retrieved guidelines occupy one cell of our grid, the
*prior* row; vs QA judging where answer text suffices — here it is chance) ·
independence-tested (vs all self-evaluation including [2511.07364]; MT-Bench
self-enhancement bias as precedent) · τ-gated (nearest antecedent: the
agentic-UQ survey's interactive/evidential action classification, used there
to model information-gain-driven uncertainty reduction, not to gate estimator
invocation — see §4.3) · consequence-labeled released corpus (the survey's
named benchmark gap).

Problem-statement lineage: CEB's formulation — pre-execution estimation of
whether a proposed action will be productive given task information, state,
and history — is adopted as the shared problem definition; we depart on the
estimator (training-free prompted judge vs experience-bank retrieval) and
extend the assessment point beyond pre-execution via τ (post-observation on
reversible steps). Kapoor et al.'s finding that one strong model estimates
others' uncertainty better than they estimate their own — including their
explicit note that agentic integration remains to be designed — is the direct
QA precedent our independence result extends, training-free.

One apparent conflict requires reconciliation, not evasion: Tian et al. show
RLHF-tuned models produce well-calibrated *verbalized* confidence in single-QA
— seemingly against our finding that in-generation verbalized confidence is
the worst instrument everywhere. The settings differ on three axes: post-hoc
elicited confidence on a completed answer vs in-generation emission during
acting (per A1's definition); single-QA factual recall vs relational step
quality; frontier RLHF models vs the 4B–70B open-weight range agents actually
deploy. We report the reconciliation explicitly rather than leaving the
citations to collide.

## 9. Contributions (exactly four)

1. **Impossibility**: no intrinsic UQ signal transfers across models and tasks
   in agentic settings, and trajectory-level evaluation is length-confounded —
   with receipts (§2).
2. **Independence**: an external prompted judge beats self-assessment across
   all tested arms, reinterpreting the capability floor as an estimator
   property (§5).
3. **The judge protocol**: evidence-grid + τ-indexed invocation as one
   specified, training-free methodology for agent-step UQ (§6).
4. **The corpus**: released harness + ~30k-step consequence-labeled,
   step-granular corpus (with agreement-rate metadata), filling the field's
   named benchmark gap (§4.6).

Out of scope (follow-up work): closing the control loop
(continue/verify/replan/defer/block beyond a taxonomy paragraph);
promise-check propagation; trained judge variants; trajectory-level
aggregation of step scores (superseded by the length confound; overlaps
existing typed-aggregation work); deployment-validated tiering guidance.

## 10. Status, timeline, and decision points

Banked: motivation corpus and map; transfer matrix; sample-efficiency curves;
evidence-ladder prototype (self-probe, one arm); independence go/no-go (4/4).
Remaining (~3–4 weeks, all offline): prober×agent matrix; external-judge
evidence grid; loop stratification; gating curves; hindsight-ceiling pass;
adjudication pass; writing.

**Direction decisions pending data**: (a) τ vs grid seniority inside the
protocol (§6) — resolved by the gating curves; (b) the strength of the
independence claim — resolved by loop stratification and upward probing;
(c) knee framing — resolved by the size curve. Open positioning dependency:
scope of the typed-aggregation appendix in adjacent in-department work must be
confirmed before the τ and out-of-scope claims freeze.

## 11. v3 changelog (2026-08-03) — conference diet, pending amendment log

- Reframed as conference paper; §0 added; contributions cut 6 → 4 (§9).
- Economics demoted from contribution to design property (§6c → cost
  paragraph + table column); tiered recommendation moved to discussion-only.
- Rule-reporting "standard" softened to a recommendation we ourselves follow.
- Agreement-rate benchmark claim removed; rates ship as corpus metadata only.
- Hindsight ceiling reduced to one figure; MT-Bench skeleton analogy deleted.
- P-vs-NP naming dropped from §1; knowledge-gap content retained; the
  "explains the field's labels" claim softened to "consistent with."
- Judge-capability knee hedged: size curve tests existence, doesn't presume it.
- Grid/τ conditional hierarchy stated explicitly (§6 preamble, §10a).
- Punchline table simplified (best-intrinsic vs judge at empirically chosen
  size).
