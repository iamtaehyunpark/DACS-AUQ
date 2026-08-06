# Conference Paper Proposal
## Judging the Step, Not the Answer: A Qualified, Characterized LLM Judge for Online Uncertainty Quantification in Agentic Systems

**Taehyun Park · UW–Madison CS · Draft v4, 2026-08-05** (v4 changes in §12; amendments A20–A24)

---

## 0. Shape of the paper

Four pillars, one line each: a negative result motivates (**impossibility**),
a positive result delivers (**independence**), a method enables (**the
instrument**: protocol + qualification + characterization), an artifact
remains (**the corpus**). v4 upgrades pillar three from "a judging protocol"
to "a characterized instrument with a grounded online deployment procedure" —
same experiments, sharper claim. Everything else in this document is a
property, a receipt, or discussion — not a contribution claim.

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
comparison (§8.vi). This framing is consistent with the field's reliance on
failure- and consequence-anchored labels, which are hindsight verdicts.

## 2. Motivating result: there is no such signal

Across ~30k judge-labeled agent steps (6 model families, 4B–70B plus one
API-only model, ALFWorld + HotpotQA, ReAct-style agents; 11 complete
self-assessment arms — the API-only model runs as target on ALFWorld only), we
find:

- **No intrinsic metric transfers.** The best metric and its scope flip across
  models and benchmarks (three distinct winning metrics across 11 arms; even
  where P(True) wins, its winning scope flips between action-split and
  aggregated variants); recipe transfer costs up to −0.10 AUROC; trained
  meta-models show the same irregularity (consistent with published escalation
  predictors). Variation is lawful — rankings cluster by configuration and
  capability tier — but no universal winner exists.
- **Trajectory-level evaluation is confounded.** On cap-dominated benchmarks,
  episode length alone reaches AUROC ≈ 1.0; no aggregated metric beats it. Step-
  level evaluation is the only meaningful granularity — and only 4/44 agent
  benchmarks provide step labels (per the field's own survey).
- **Self-assessment has a capability ceiling, stated relatively.** Sub-7B
  agents' best self-derived signal reaches only 0.62–0.73 AUROC — 0.19–0.30
  below what an external judge reads from the *same frozen trajectories* (§5).
  In-generation verbalized confidence is capability-conditional in the worst
  way: for capable models it is inverted or near-inverted (0.19–0.40), while
  for sub-7B agents on ALFWorld it is the *best* of a bad lot — the one
  channel that varies is the one that cannot be trusted across tiers.
  Orientation stance, pre-registered: no post-hoc sign flips; sub-0.5 AUROCs
  are reported as-is and discussed as anti-signal.
- **P(True) is the most robust single probe** (best in 7/11 arms; its recipes
  transfer at −0.016 mean loss) — but its winning scope is model-dependent,
  and it requires logprob access many deployments lack.

The search for the ultimate metric fails empirically. We propose to stop
searching and change the estimator instead.

## 3. Thesis

> **Agent-step uncertainty should be estimated by an independent, qualified
> LLM judge characterized once and deployed across target agents online:
> reading environment-grounded evidence under a specified protocol, scoring
> prompted P(True)-style trust per step, invoked selectively via
> environment-derived action typing, with its operating point computed from
> its own label-free competence estimate of the target — rather than
> extracted from the acting model's internals.**

Three properties make "characterized once, deployed anywhere" literal rather
than aspirational, each measured (§7): the judge's *recipe* is
target-invariant; its *normalized separation* is target-invariant; and the one
target-dependent quantity — the operating point — is a function of the
target's error rate, which the judge estimates from its own unlabeled scores.

## 4. Why the agentic setting is the novelty (not a domain swap)

Judging agent steps is structurally different from judging answers, with a
measured receipt per difference:

1. **The judged object has no intrinsic truth value.** An action string scored
   alone is chance (AUROC 0.512 [0.438, 0.586]). Step quality is relational to
   state — the QA judging problem does not port.
2. **Evidence is environmental and temporal, with a measured hierarchy.**
   Trajectory history buys 0.512→0.697; the environment's realized response to
   the action is the largest single gain (+0.072 over the full-context base,
   0.741→0.813); given history and reasoning, the action token itself adds
   nothing (0.740 vs 0.741) — and operating without the agent's reasoning
   costs −0.044 with overlapping CIs, so black-box operation is viable at a
   small, currently non-significant penalty.
3. **The environment supplies typed structure (τ = information/world-modifying/
   reversible/cost).** τ gives the judge an invocation policy and an evidence
   policy no QA judge has (§6). Nearest antecedent: the agentic-UQ survey
   classifies actions (interactive/evidential) to *model* uncertainty
   reduction via an information-gain term. No prior work uses action typing to
   *gate judge invocation and evidence selection* — typing as estimator
   policy, not as uncertainty model, is ours.
4. **Assessment is online and per-step**, making cost a first-class property:
   the probe is prefill + 1 token (measured: 3,300 assessments in ~5 min on one
   A100; near-free with KV prefix sharing when judge = agent).
5. **The detected failures are agentic**: loops, stagnation, cap-failures carry
   40–87% of the error mass and have no QA analog.
6. **Ground truth is environment-anchored** (gate-1): deterministic violation
   labels (inadmissible actions, no-ops, exact state-action repeats, malformed
   or zero-result tool calls) plus replay-derived progress labels
   (expert-planner distance on ALFWorld; gold supporting-fact retrieval on
   HotpotQA), with the 3-judge ensemble label retained as a secondary column
   and its error rate on deterministically-labeled steps reported as a
   circularity audit. The released labeled corpus is the artifact the field
   lacks; per-step label provenance ships as metadata.

## 5. Core empirical result (go/no-go: passed, margin widened)

**Generation–assessment independence pays.** A Qwen-35B judge probing frozen
trajectories of 4B-class agents beats those agents' best self-assessment in
4/4 arms, by **+0.19 to +0.30** AUROC (external readings reach 0.815–0.927
where self-best sits at 0.62–0.73). Capable judges also lift mid-tier and
peer targets (e.g., 0.657→0.868, 0.708→0.823 under a 70B judge). This
reinterprets the capability ceiling: small agents are not unreadable — they
are bad self-readers; readability is a property of the estimator. It extends
the published QA finding that one strong model can estimate others'
uncertainty (Kapoor et al.) to the agentic setting, **training-free and
prompted** rather than fine-tuned.

**Stated boundary.** Independence holds downward and peer-level; it is not
universal at the top of the capability range — the strongest agent's
self-assessment on one benchmark exceeds its external 70B reading (0.842 vs
0.816), and the largest agent's margin under a smaller judge is +0.010,
within noise pending CIs. The claim we make is the claim the data licenses.

## 6. The instrument (one methodological contribution, four components)

The methodology is a single contribution: a training-free judge **instrument**
with a specified protocol, a qualification criterion, a one-time
characterization, and a grounded online deployment rule. Components (a)–(b)
specify what the judge reads and when it is invoked; (c)–(d) specify who may
hold the instrument and how it is pointed at an unseen target.

**(a) Evidence grid — what the judge reads.** The judge's prompt is a policy
over evidence classes — *prior* (task rules), *process* (history, reasoning,
action), *realized* (the observation the action produced) — characterized by a
paired, decoy-controlled ablation (n=300 × 11 conditions with 95% CIs,
scaling to full corpora). Established: history is the signal carrier (a rule
without history is inert: 0.531); a **relevant** rule adds discrimination
(+0.072, beating a decoy floor by +0.085) while a merely-stated rule only
shifts level; rules manufacture false positives on rule-adjacent correct steps
(+0.155 on legitimate revisits). We report rule-augmented judges against a
decoy floor with their false-positive rate, and follow this practice in all
our own reporting.

**(b) τ-indexed evidence & invocation policy — when the judge is invoked.**
Reversible steps (R=1): assess post-observation with realized evidence
(one-step detection latency; the realized increment is the largest in the
grid). Irreversible steps (R=0): assess pre-execution, substituting prior
evidence (targeted rules recover +0.072 of the realized-evidence gain — the
rule-recoverable fraction of the cost of irreversibility). Invocation is
gated by τ and budget, expressed **quantile-first**: the gate fires on the
top-k% most uncertain steps of the deployment's own score stream, which is
distribution-free and requires no labels; conversion of budget k to absolute
risk uses the competence estimate from (d). Evaluated as budget-vs-detection
curves against uniform gating.

**(c) Judge qualification — who may hold the instrument.** Operating-point
uniformity is capability-gated, so qualification is part of the method, not a
footnote. A candidate judge is characterized on a labeled reference corpus
(we release ours) and qualifies iff it clears pre-registered floors on:
normalized separation *f* (fraction of achievable ranking separation,
base-rate free) with bounded range across reference targets; the correlation
between its optimal cut percentile and target error rate; and the fit quality
of its competence estimator *g* (below). Provisional floors from the pivot
corpus — frac ≥ 0.70 with range width ≤ 0.25, correlations ≥ 0.90 — freeze
only after gate-1 recomputation (§10, R1). On current numbers capable judges
pass with wide margin (f = 0.88 and 0.84, ranges 0.78–0.98) while sub-8B
judges fail and are *erratic*, not merely weaker (f spanning −0.08–0.57,
inverting on some targets). Scope limit, stated honestly: qualification
requires one labeled reference corpus per environment family; it does not
solve label-free qualification of an unknown judge in an unknown environment.

**(d) Characterization triple and the online deployment rule — how the
instrument is pointed.** Fitted once per qualified judge: the invariant
**recipe** (scope + evidence policy; measured invariance: one scope is
optimal or within 0.02 in 52/54 columns, and under external judging the best
scope is stable in 8/9 cross arms — the recipe instability of §2 is a
property of self-assessment, not of the instrument); the separation constant
**f**; and the competence map **g**: mean judge uncertainty on a target's
unlabeled stream → estimated target error rate p̂ (observed tracking
r ≈ 0.96–0.99, provisional until gate-1). Deployment on an unseen agent is
then label-free and online: run the fixed recipe; estimate p̂ = g(Ū) from the
accumulating score stream; set the gate at the top-p̂ quantile (the optimal
cut percentile tracks the target error rate at r = 0.94–0.96 for qualified
judges); predict expected yield from f. What does **not** transfer — measured,
not conceded: raw score thresholds (group-mean uncertainty levels move 5–30×
across targets and overlap across correct/incorrect pools between targets), so
absolute-τ deployment is explicitly rejected in favor of the computed
operating point. Validation is predictive leave-one-target-out (§8.vii):
characterize on all-but-one cell, predict the held-out cell's cut, precision,
and recall, compare to oracle, rotate. Worst case if g degrades under gate-1
labels (§10, R2): the policy ships quantile/budget-only and p̂ estimation
demotes to a heuristic — the instrument survives with a weaker pointer.

**Cost properties (not a contribution — a property of the design).** Prefill +
1 token per assessment; KV-shared self-probing near-free; external judging
priced per step and amortized by τ-gating; local recipe calibration saturates
at ~200 labeled steps (96–99.9% retention), which is also the worst-case
per-deployment footprint if the label-free pointer is demoted. One paragraph
and a cost column in the results table. A practical tiering note — intrinsic
P(True) where logprobs and capability allow, gated external judge where they
don't — belongs in the discussion section as a takeaway, not among the claims.

## 7. Operating-point findings (the receipts behind §6c–d)

From the 56-cell (assessor × target) pivot analysis, SPLIT-action scope,
provisional until gate-1:

1. Absolute thresholds do not transfer — not even within one dataset (§6d).
2. Percentile rules are directionally stable everywhere but not uniform in
   yield (lift@10% varies ~2.5× within an assessor); at a 10% budget the best
   judges recall 18–25% of incorrect steps in error-dense regimes — reported
   as a ceiling, not hidden.
3. The optimal cut is determined by the target's error rate (r = +0.94–0.96,
   capable judges), and the error rate is estimable from the judge's own
   unlabeled scores (r ≈ 0.96–0.99) — the two facts that make the online rule
   grounded rather than assumed.
4. Raw percentile-position correlations with error rate are mostly arithmetic
   (a perfect ranker shows them); the informative, base-rate-free quantity is
   normalized separation f, which is uniform for capable judges only.

## 8. Evaluation plan

Frozen-corpus probe passes only (no agent regeneration): (i) full prober ×
agent matrix — self-diagonals, peer and upward probing, and a judge-size
curve (4B → 70B → frontier) testing *whether* a judge-capability knee exists
and, if so, where; (ii) evidence grid under external judges, both benchmarks;
(iii) loop-stratified decomposition of all gains (general signal vs
degenerate-regime detection); (iv) τ-gating budget curves, quantile-first;
(v) the punchline table: best-intrinsic vs external judge (at the empirically
chosen size), AUROC × cost per step; (vi) **hindsight ceiling** — the same
judge scoring the same steps under full-trajectory hindsight context vs
prefix-only online context, measuring the §1 knowledge gap; one figure;
(vii) **LOTO predictive validation** of the characterization triple —
held-out-target prediction of cut/precision/recall vs oracle across all
cells; (viii) **judge-elicitation ablation** — P(True)@logit vs verbalized
0–100 score vs binary majority@k at matched compute, same frozen trajectories
and protocol, closing the "a closed binary judge would do" objection with a
measurement (and testing the closed-judge deployment path); (ix) **replay
demo** — frozen trajectories streamed step-wise through the online rule with
causal information flow only: gating decisions, realized vs LOTO-predicted
yield, and p̂ convergence to the target's true error rate. Validity: judge
families disjoint from label-judge trio and agent set; prefix-only
information asymmetry for pre-execution claims; environment-anchored primary
labels with the ensemble as audited secondary (gate-1) against
judge-judging-judges circularity; a perturbation battery as the judge's
construct-validity/bias analysis (MT-Bench-style); fixed-scope primary
reporting; cross-corpus AUROCs compared as problems, not judges; CIs
(DeLong/bootstrap) on all matrices — best/tied counts and near-tie boundary
claims (§5) are not asserted without them.

## 9. Positioning (each clause vs its nearest neighbor)

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
self-enhancement bias as precedent) · **characterized-instrument deployment**
(vs per-model metric search, which our §2 shows failing, and vs one-threshold
LLM-judge practice, which our §7.1 shows failing — the amortized/target-
dependent split is measured, not assumed) · τ-gated (nearest antecedent: the
agentic-UQ survey's interactive/evidential action classification, used there
to model information-gain-driven uncertainty reduction, not to gate estimator
invocation — see §4.3) · consequence-labeled released corpus with
environment-anchored provenance (the survey's named benchmark gap).

Problem-statement lineage: CEB's formulation — pre-execution estimation of
whether a proposed action will be productive given task information, state,
and history — is adopted as the shared problem definition; we depart on the
estimator (training-free prompted judge vs experience-bank retrieval) and
extend the assessment point beyond pre-execution via τ. Kapoor et al.'s
finding that one strong model estimates others' uncertainty better than they
estimate their own — including their explicit note that agentic integration
remains to be designed — is the direct QA precedent our independence result
extends, training-free; §6d is one concrete answer to their open integration
question.

The Tian et al. reconciliation (RLHF verbalized calibration in single-QA vs
our inverted in-generation verbalized channel) is retained from v3 and now
additionally scoped by tier: the channel's behavior differs by capability
(§2), which sharpens rather than weakens the reconciliation. Settings differ
on: post-hoc elicited vs in-generation emission; single-QA recall vs
relational step quality; frontier RLHF models vs the 4B–70B open-weight range
agents actually deploy.

## 10. Gate-1: environment-anchored recomputation (blocking)

All §7 numbers and the §6c floors were computed against 3-judge ensemble
labels. Gate-1 rebuilds labels from the environment (deterministic violations
+ replay-derived progress; execution spec committed to repo, A-log) and
recomputes every table side-by-side, with pre-registered decision rules:
R1 floors freeze iff capable-judge f ≥ 0.70 and assessor ordering is
preserved under env labels; R2 g demotes to heuristic if its correlation
drops below 0.85; R3 any AUROC cell moving > 0.05 forces restatement of the
affected headline; R4 the ensemble's error rate on deterministically-labeled
steps is reported regardless (circularity audit). Environment labels are
high-precision/incomplete-recall; both restricted and full-set evaluations
are reported, plus a ~150-step label-QC spot check (label QC, not a human
evaluation arm).

## 11. Contributions (exactly four), status, and decision points

1. **Impossibility**: no intrinsic UQ signal transfers across models and tasks
   in agentic settings, and trajectory-level evaluation is length-confounded —
   with receipts (§2).
2. **Independence**: an external prompted judge beats self-assessment across
   all tested downward and peer arms, reinterpreting the capability ceiling as
   an estimator property, with the upward boundary stated (§5).
3. **The instrument**: evidence grid + τ-indexed quantile-first invocation +
   judge qualification criterion + characterization triple (recipe, f, g)
   with a label-free online deployment rule, LOTO-validated — one specified,
   training-free methodology for agent-step UQ (§6–§7).
4. **The corpus**: released harness + ~30k-step step-granular corpus with
   environment-anchored primary labels, ensemble secondary labels, full
   provenance metadata, and the circularity audit — filling the field's named
   benchmark gap (§4.6, §10).

Out of scope (follow-up work): closing the control loop — intervention
policies and end-task success improvement, incl. multi-agent settings
(continue/verify/replan/defer/block beyond a taxonomy paragraph; the replay
demo §8.ix emits decisions, it does not act on them); promise-check
propagation; trained judge variants; trajectory-level aggregation of step
scores; label-free qualification of unknown judges in unknown environments;
deployment-validated tiering guidance.

**Status.** Banked: motivation corpus and map; transfer matrix;
sample-efficiency curves; evidence grid with CIs (self-probe + base external
arm); independence go/no-go (4/4, margins §5); 56-cell pivot analysis (§7,
provisional). Sequenced remaining (~3 weeks, all offline): gate-1 →
(f, g) fits + LOTO (§8.vii) → qualification floors freeze → gating curves +
replay demo → elicitation ablation → hindsight ceiling → adjudication-free
writing pass. **Direction decisions pending data**: (a) τ vs grid seniority —
gating curves; (b) raw-τ vs quantile-only framing of the deployment rule —
gate-1 R2; (c) knee framing — size curve. Open positioning dependency,
unchanged and now blocking two sections (§6b typed claims, out-of-scope
list): scope of the typed-aggregation appendix in adjacent in-department work
must be confirmed — the Changdae Oh conversation — before the τ claims
freeze.

## 12. v4 changelog (2026-08-05)

- Title and thesis extended: qualified/characterized instrument with online
  deployment rule (A23, A24).
- §2 corrected against full data (A20): 6 families / 11 arms; verbalized-
  confidence claim made capability-conditional; absolute floor band replaced
  by relative ceiling; P(True) count restated 7/11; orientation stance
  pre-registered.
- §5 numbers updated (+0.19–0.30, 0.815–0.927); upward boundary stated
  explicitly; near-tie claims made CI-conditional.
- §6 restructured from two components to four: qualification (c) and
  characterization/deployment (d) added; τ policy restated quantile-first;
  recipe-stability receipt (8/9) added as the resolution of §2's instability.
- §7 added: operating-point findings incl. threshold non-transfer, cut ↔
  error-rate law, label-free competence estimation, normalized separation.
- §8 extended: LOTO validation (vii), judge-elicitation ablation (viii, A21),
  replay demo (ix); CI requirement made explicit.
- §10 added: gate-1 with pre-registered decision rules R1–R4 (execution spec
  in repo).
- Labels re-based: environment-anchored primary, ensemble secondary with
  circularity audit; §4.6 and Contribution 4 updated accordingly; human
  adjudication replaced by label-QC spot check.
- Out-of-scope list extended: control-loop/MAS application named as the
  follow-up paper; label-free judge qualification named as open.
- Contribution count held at exactly four; (c)–(d) absorbed into
  Contribution 3, not added as a fifth.
