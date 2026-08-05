# Conference Paper Proposal — Paper A
## No Universal Signal: A Step-Level Transfer Study and Benchmark for Uncertainty Quantification in LLM Agents

**Taehyun Park · UW–Madison CS · Paper-A v1 (split from unified proposal v3), 2026-08-03**

---

## 0. Shape of the paper

An analysis-and-benchmark paper. One measurement claim (**non-transfer, quantified**),
one methodological warning (**the length confound**), one explanatory finding
(**estimator-dependence**), one artifact (**the corpus**). No method is proposed;
the paper's job is to establish, with receipts, what the field's evaluation
practice gets wrong and to ship the instrument that fixes it. The word
"impossibility" does not appear anywhere in the paper: every negative claim is
stated as a quantified empirical result over a defined arm space, never as a
universal.

## 1. Problem

LLM agents fail mid-trajectory — looping, acting on wrong beliefs, committing
irreversible mistakes — and reliable deployment requires knowing, per step and
online, whether the next action should be trusted. The field's instruments are
intrinsic uncertainty metrics (token entropy, sequence probability, verbalized
confidence, P(True)) and trained meta-models. Published work implicitly
presupposes two things this paper tests directly: (i) that a metric validated
on one model/task pair informs another, and (ii) that trajectory-level AUROC is
a meaningful evaluation target. We show, quantitatively, that (i) fails in
lawful but practice-breaking ways and (ii) is confounded to the point of
vacuity on cap-dominated benchmarks — and that the field cannot currently
check either claim itself, because only 4/44 agent benchmarks provide step
labels. The paper closes that loop by releasing the missing instrument.

## 2. Findings (all banked; §2 of unified v3, promoted to headline)

Across ~30k labeled agent steps (4 model families, 4B–70B, ALFWorld +
HotpotQA, ReAct-style agents, entangled + decoupled generation):

- **Non-transfer, quantified.** The best metric and its winning scope flip
  across models and benchmarks; recipe transfer costs up to −0.10 AUROC;
  trained meta-models show the same irregularity (consistent with published
  escalation predictors). Variation is lawful — rankings cluster by
  architecture × capability tier, not by metric identity — but no
  configuration-independent winner exists in the tested space. The transfer
  matrix is Figure 1.
- **The length confound.** On cap-dominated benchmarks, episode length alone
  reaches trajectory-level AUROC ≈ 1.0; no aggregated intrinsic metric beats
  it. Any trajectory-level result on such benchmarks is uninterpretable
  without a length-only baseline — a reporting requirement we state and
  follow. Step-level evaluation is the only meaningful granularity.
- **Estimator-dependence.** Below ~7B, every self-derived signal sits near
  chance (0.53–0.64), with in-generation verbalized confidence the worst
  instrument everywhere. But the same frozen trajectories read by an external
  35B prober reach 0.82–0.91 (+0.02 to +0.28 AUROC over self-best, 4/4 arms).
  Small agents are not unreadable; they are bad self-readers. Readability is a
  property of the estimator, not the agent — which reframes the field's
  "capability floor" as an artifact of self-assessment.
- **P(True) is the most robust single probe** (best or tied 7/8 arms; recipes
  transfer at −0.016 mean loss) — but its winning scope is model-dependent and
  it requires logprob access many deployments lack. This is the strongest
  version of the transferable-metric hypothesis, and it still fails the
  universality bar.
- **Failure modes are agentic.** Loops, stagnation, and cap-failures carry
  40–87% of error mass and have no QA analog — grounding why QA-derived UQ
  practice does not port.

## 3. Thesis

> **Step-level UQ for LLM agents currently has no configuration-independent
> intrinsic signal; trajectory-level evaluation is length-confounded on
> standard benchmarks; and apparent unreadability of small agents is an
> estimator artifact. Progress requires step-granular, consequence-labeled,
> length-controlled evaluation — which we specify and release.**

## 4. Ground truth and validity (headline-critical for this paper)

Because the artifact is the contribution, label validity is the paper's
load-bearing wall:

1. **Environment-anchored targets are primary** wherever the environment
   yields them (task success, state predicates, loop/stagnation detection,
   cap events).
2. **Judge-ensemble labels** (3-judge, families disjoint from every evaluated
   estimator and agent) cover steps without environment anchors; all
   disagreements are human-adjudicated; a human-adjudicated gold subset is
   reported separately so readers can bound label noise.
3. **Per-step inter-judge agreement rates ship as corpus metadata**, not as a
   benchmark claim.
4. **Prefix-only information asymmetry** is enforced for all online-estimation
   measurements; a **hindsight-ceiling figure** (same judge, prefix-only vs
   full-trajectory context) quantifies the online/hindsight knowledge gap and
   bounds what any online estimator can achieve.

## 5. Paper structure (printable skeleton)

1. **Introduction** — deployment need; the two implicit presuppositions;
   contributions. Figure 1: the transfer matrix.
2. **Related work** — intrinsic UQ metrics and their QA origins; trained
   meta-models and escalation predictors; agentic UQ surveys and the named
   benchmark gap; trajectory-level verdict methods (UALA/SAUP/MATU); calibration
   results (Tian et al.) with the three-axis reconciliation (post-hoc vs
   in-generation; factual recall vs relational step quality; frontier RLHF vs
   deployed open-weight range).
3. **The corpus and measurement framework** — arm space (4 families × 2
   benchmarks × 2 architectures), labeling pipeline (§4 above), harness,
   metric zoo, evaluation protocol (fixed-scope primary reporting;
   cross-corpus AUROCs compared as problems, not estimators).
4. **Transfer study** — full metric × model × task × architecture matrix;
   recipe-transfer cost analysis; meta-model arms; the lawfulness analysis
   (clustering by architecture × capability tier); P(True) as the robustness
   frontier and where it breaks.
5. **The length confound** — length-only baseline vs all aggregated metrics;
   cap-domination analysis; the reporting requirement; survey of affected
   published results (stated as benchmark properties, not accusations).
6. **Estimator-dependence** — self-assessment floor; the frozen-trajectory
   external-reading result across the prober × agent matrix (self-diagonals,
   peer, upward); loop-stratified decomposition (general signal vs
   degenerate-regime detection); judge-size curve testing whether a
   capability knee exists.
7. **Discussion** — practitioner guidance (P(True) where logprobs and
   capability allow; external reading where they don't — guidance, not a
   proposed method); what a transferable signal would have to explain;
   limitations (two benchmarks, open-weight range, label-noise bounds).
8. **Conclusion + artifact statement** — corpus, harness, and reporting
   checklist release.

## 6. Contributions (exactly four)

1. **The transfer study**: quantified non-transfer of intrinsic UQ signals
   across models, tasks, and architectures in agentic settings, including the
   strongest candidate (P(True)) — with the full matrix released (§4/§5.4).
2. **The length confound**: trajectory-level evaluation on cap-dominated
   benchmarks is length-confounded to AUROC ≈ 1.0; step-level granularity is
   necessary; a length-only-baseline reporting requirement (§5.5).
3. **Estimator-dependence**: the sub-7B capability floor is a property of
   self-assessment, not of agent readability — external reading of frozen
   trajectories recovers 0.82–0.91 AUROC (§5.6).
4. **The corpus**: released harness + ~30k-step consequence-labeled,
   step-granular, length-controlled corpus with agreement-rate metadata,
   filling the field's named benchmark gap (§3/§4).

Out of scope (follow-up work): any proposed estimation *method* — including
judge protocols, evidence-selection policies, and invocation gating; control
loops; trained judges; trajectory-level aggregation.

## 7. Positioning (nearest neighbor per clause)

Step-granular measurement (vs UALA/SAUP/MATU trajectory verdicts;
[2511.07364] independently supports step granularity while remaining
self-evaluation) · transfer-tested (no published agentic-UQ work reports a
cross-model × cross-task transfer matrix) · length-controlled (the confound is
unreported in the trajectory-level literature) · estimator-dependence (extends
Kapoor et al.'s QA finding — one strong model estimates others' uncertainty —
to agentic trajectories, observationally) · consequence-labeled corpus (the
agentic-UQ survey's named benchmark gap, and its 4/44 step-label count, are
the documented motivation) · Tian et al. reconciliation reported explicitly.

## 8. Risks and pre-registered answers

- *"Negative results are incremental."* The paper is framed as measurement,
  not negation: the matrix, the confound magnitude, and the
  estimator-dependence effect are each quantitative findings with released
  instruments. The reporting checklist gives the field an actionable take-away.
- *"Only 8 arms."* Scope is stated precisely; claims are bounded to the tested
  space; the harness makes extension by others one command. Lawfulness
  analysis (clustering) shows the arm space is structured, not cherry-picked.
- *"Judge-derived labels evaluate judge-like estimators."* Environment-anchored
  targets are primary; label-judge families are disjoint from all evaluated
  estimators; the gold subset bounds noise (§4). The external-reading result
  in §5.6 is additionally checked against environment-anchored targets alone.
- *"Isn't §5.6 a method?"* No method is specified — no protocol, no evidence
  policy, no invocation rule. It is an observational finding about estimator
  identity, and the method paper is explicitly future work.

## 9. Status and timeline

Banked and sufficient for submission: motivation corpus and map; transfer
matrix; sample-efficiency curves; independence go/no-go (4/4); length-confound
analysis. Remaining (~2–3 weeks, all offline, no agent regeneration):
prober × agent matrix completion (peer + upward arms); loop stratification;
judge-size curve; hindsight-ceiling pass; adjudication pass on the gold
subset; environment-anchored re-check of §5.6 numbers; writing.

No direction decisions pend on data: every headline claim in this proposal is
already banked or is a completion of a banked analysis. The only external
dependency is confirming the scope of the typed-aggregation appendix in
adjacent in-department work before the out-of-scope claims freeze.

## 10. Changelog (Paper-A v1, 2026-08-03)

- Split from unified proposal v3; method contributions (judge protocol,
  evidence grid, τ policy) removed to Paper B; this paper proposes no method.
- "Impossibility" reframed as quantified transfer study throughout; the word
  removed from all claims.
- Corpus promoted from contribution 4 to co-headline; ground-truth validity
  section (§4) promoted to top-level.
- Independence result reframed from method validation to observational
  estimator-dependence finding; environment-anchored re-check added.
- Length-only-baseline reporting requirement stated as a contribution
  component.
- Evidence grid, τ, cost properties, hindsight-gap *framing* (beyond the one
  ceiling figure) all removed.
