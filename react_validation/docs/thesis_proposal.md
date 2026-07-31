# Thesis Proposal
## Judging the Step, Not the Answer: An LLM-as-Judge Methodology for Uncertainty Quantification in Agentic Systems

**Taehyun Park · UW–Madison CS · Draft v1, 2026-07-31**

---

## 1. Problem

LLM agents fail mid-trajectory — looping, acting on wrong beliefs, committing
irreversible mistakes — and reliable deployment requires knowing, per step and
online, whether the next action should be trusted. The field's instruments for
this are intrinsic uncertainty metrics (token entropy, sequence probability,
verbalized confidence, P(True)) and, increasingly, trained meta-models. Both
presuppose that some signal, once found, transfers across models and tasks.

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
   policy no QA judge has (Sec. 6). No prior work uses typed selective judging.
4. **Assessment is online and per-step**, making cost a first-class property:
   the probe is prefill + 1 token (measured: 3,300 assessments in ~5 min on one
   A100; near-free with KV prefix sharing when judge = agent).
5. **The detected failures are agentic**: loops, stagnation, cap-failures carry
   40–87% of the error mass and have no QA analog.
6. **Ground truth is consequence-anchored**: 3-judge ensemble labels with human
   adjudication of disagreements, plus environment-anchored targets — and the
   released labeled corpus is the artifact the field lacks.

## 5. Core empirical result (go/no-go: passed)

**Generation–assessment independence pays.** A Qwen-35B judge probing frozen
trajectories of 4B-class agents beats those agents' best self-assessment in 4/4
arms, by +0.02 to **+0.28** AUROC (reaching 0.82–0.91 where self-reading sits
at 0.53–0.64). This reinterprets the capability floor: small agents are not
unreadable — they are bad self-readers; readability is a property of the
estimator. It extends the published QA finding that one strong model can
estimate others' uncertainty (Kapoor et al.) to the agentic setting,
**training-free and prompted** rather than fine-tuned.

## 6. The protocol (contributions 2–4)

**(a) Evidence grid.** The judge's prompt is a policy over evidence classes —
*prior* (task rules), *process* (history, reasoning, action), *realized* (the
observation the action produced) — characterized by a paired, decoy-controlled
ablation (n=300 × 11 conditions, scaling to full corpora). Established so far:
history is the signal carrier; a **relevant** rule adds discrimination (+0.072,
beating a decoy floor by +0.086) while a merely-stated rule only shifts level;
rules manufacture false positives on rule-adjacent correct steps (+0.155 on
legitimate revisits) — hence a reporting standard: any rule-augmented judge is
reported against a decoy floor with its false-positive rate.

**(b) τ-indexed evidence & invocation policy.** Reversible steps (R=1): assess
post-observation with realized evidence (one-step detection latency, near-zero
cost in loop-dominated failure regimes). Irreversible steps (R=0): assess
pre-execution, substituting prior evidence (targeted rules). The measured gap
between the two on matched steps is the **cost of irreversibility** (~0.07
AUROC upper bound; rule-recoverable fraction to be measured). Invocation is
gated by τ and budget: always on irreversible/costly steps, never on cheap
reads — evaluated as budget-vs-detection curves against uniform gating.

**(c) Economics.** Prefill + 1 token per assessment; KV-shared self-probing
near-free; external judging priced per step and amortized by gating; local
recipe calibration saturates at ~200 labeled steps (96–99.9% retention). The
deliverable is a tiered recommendation: free intrinsic default (P(True)) where
logprobs and capability allow → gated external judge where they don't.

## 7. Evaluation plan

Frozen-corpus probe passes only (no agent regeneration): (i) full prober ×
agent matrix — self-diagonals, peer and upward probing (does external reading
help equals/superiors or only weaker agents?), judge-size curve (4B → 70B →
frontier) locating the judge-capability knee; (ii) evidence grid under external
judges, both benchmarks; (iii) loop-stratified decomposition of all gains
(general signal vs degenerate-regime detection); (iv) τ-gating budget curves;
(v) the punchline table: best-intrinsic vs judge-at-knee vs judge-at-frontier,
AUROC × cost per step. Validity: judge families disjoint from label-judge trio
and agent set; prefix-only information asymmetry for pre-execution claims;
environment-anchored targets and a human-adjudicated gold subset against
judge-judging-judges circularity; a perturbation battery as the judge's
construct-validity/bias analysis (MT-Bench-style); fixed-scope primary
reporting; cross-corpus AUROCs compared as problems, not judges.

## 8. Positioning (each clause vs its nearest neighbor)

Training-free prompted (vs Kapoor's fine-tuned QA estimator; CEB's
experience-bank critic; supervised escalation predictors) · step-granular
online (vs UALA/SAUP/MATU/guideline-accumulation trajectory verdicts) ·
evidence-grid characterized (vs single-evidence guideline grounding; vs QA
judging where answer text suffices — here it is chance) · independence-tested
(vs all self-evaluation; MT-Bench self-enhancement bias as precedent) ·
τ-gated (no neighbor) · consequence-labeled released corpus (the survey's named
gap).

## 9. Deliverables

(1) The impossibility result with receipts; (2) the judge protocol + evidence-
grid methodology and reporting standards; (3) the independence result and floor
reinterpretation; (4) τ-indexed evidence/invocation policy with the cost model;
(5) tiered deployment recommendation; (6) released harness + ~30k-step
consequence-labeled corpus. Out of scope (follow-up work): closing the control
loop (continue/verify/replan/defer/block beyond a taxonomy paragraph);
promise-check propagation; trained judge variants.

## 10. Status & timeline

Banked: motivation corpus and map; transfer matrix; sample-efficiency curves;
evidence-ladder prototype (self-probe, one arm); independence go/no-go (4/4).
Remaining (~3–4 weeks, all offline): prober×agent matrix; external-judge
evidence grid; loop stratification; gating curves; adjudication pass; writing.
