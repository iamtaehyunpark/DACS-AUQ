# Decoupled, Action-Conditioned Step-Wise Uncertainty in Agentic LLM Systems
## Theoretical Framework & Positioning

**Status:** Pre-experimental synthesis. Every claim below rests on the experimental program in the companion spec (`uq_experiments.md`). The thesis has one decisive test (E1) and is flagged accordingly throughout.

**Scope:** This is a **measurement paper**. The question is: *how do you accurately measure uncertainty in an agentic LLM system?* Control, backtracking, and drift-correction are what accurate measurement enables later — they define the *criterion* of accuracy, not the contribution of this work.

---

## 1. The Mental Model

An LLM agent does not produce one answer whose uncertainty accumulates. It traverses a sequence of **locally posed decision problems**. At each step it holds an epistemic state, selects a policy, and proposes a transition whose informational and external consequences determine how those uncertainties should be read.

Three commitments follow:

1. **Uncertainty is a per-step primitive.** History enters only through the state S_t. Steps are *conditionally posed*, not independent — they remain causally coupled through transitions. (Terminology matters: say "conditionally posed," never "independent." The independence claim is in tension with error propagation and a reviewer will find it.)

2. **Thought and Action are different control variables.** U_T ≈ epistemic ("do I know?"), U_A ≈ policy ("do I know what to do?"). They can move in opposite directions, and that is health, not noise.

3. **The criterion is control, not diagnosis.** A measurement is *accurate* if it exposes, at the current prefix, whether belief/policy/transition indicate healthy recovery or dangerous drift — early enough to retrieve, verify, replan, escalate, or abstain. A perfectly calibrated terminal score fails this criterion by construction.

Trajectory-level uncertainty is not universally invalid. It is the wrong *primitive* for online reading, and should be **derived** from typed local states rather than treated as the object from which local behavior is interpreted.

---

## 2. The Argument Chain (Full Context)

This section is the core of the paper. It is not a list of features — each claim forces the next.

### 2.1 The ontological claim: what a trajectory is

An agentic trajectory is a chain of locally posed problems. At each step the agent faces a local sub-goal that is not the global task and usually is not the previous step's sub-goal either. The agent at step t is solving "which drawer do I open," not "complete the household task."

History matters, but it enters **only through S_t**. This is the precise sense of the Markov framing: not that context is irrelevant, but that the decision at t is made against S_t alone.

**Consequence:** if the decision problem is local, uncertainty about that decision is a local quantity. Any method that reads uncertainty off the whole trajectory measures an object that corresponds to no decision the agent actually faces. This kills trajectory-level UQ at the root — as a primitive, not as a derived quantity.

**Known weakness (address in the paper, do not hide):** for an LLM agent, S_t is operationally the context window — i.e., the full history. "History enters only through the state" is therefore *nearly tautological* unless the state is something more structured than the transcript. The framing earns its keep only through what it licenses: the reset rule (§2.5). The MDP language should occupy one paragraph and be explicitly tied to the reset rule; otherwise it is decoration and reviewers will spend the review on it.

### 2.2 The semantic claim: two quantities inside one step

Thought and Action are not two parts of one output. They are different **kinds** of quantities:

- **U_T — epistemic uncertainty.** Do I know?
- **U_A — policy uncertainty.** Do I know what to do?

The crucial observation: **anti-correlation between them is the agent working correctly.** Not knowing a fact is precisely what makes searching for it the confident move:

```
Thought: I don't know the atomic weight of element X.     ← high U_T
Action: Search["atomic weight of element X"]              ← low U_A
```

Standard practice emits both in one generation. This does not add noise — it blends two signals that structurally oppose each other, producing a number with **no interpretation at all**. Structurally uninterpretable, not high-variance.

This is why decoupling is not a measurement trick bolted on. It is **the architecture**: the entangled setup cannot measure the thing, period.

### 2.3 The autoregression caveat (load-bearing, cuts both ways)

Autoregression already factorizes P(T, A | S) = P(T | S) · P(A | S, T). A naive stop-append-resume samples from the **identical distribution**. Decoupling only means something if the action policy π_A has a *different inference contract* — constrained action space, tool grammar, separate elicitation, control prompt.

- **Against the thesis:** ReDAct's action call already has a stage-specific contract (fresh prompt, `YOUR CURRENT REASONING: {THOUGHTS}`, "exactly one line, exactly one of the available commands"). The architecture ground is more occupied than it first appears.
- **For the thesis:** if the split is a no-op absent a contract, then any measured shift *must come from the contract* — and verbalized confidence is the metric that reads contracts. The central E1 prediction acquires a derivation, not a hunch.

### 2.4 The probe claim: entropy is not epistemic uncertainty

Thought-token entropy ≠ epistemic uncertainty. A model can fluently emit "I don't know this, I should search" at **low token entropy** while the underlying belief is maximally uncertain. Fluency about ignorance is still fluency.

**Provenance (cite before a reviewer does):** this argument is now **shared background, not our insight**. AUQ's Appendix A.5.4 makes it explicitly — token-level probability can be statistically confident in the next grammatical token while epistemically uncertain about content, and averaging log-probs over a long CoT introduces length bias that washes out the signal of a specific logical flaw — building on Lin et al. (verbalized uncertainty) and Tian et al. (elicited calibration under RLHF). The paper must frame it as a **shared premise whose step-level validity is untested**, with attribution.

What follows from the shared premise, and what remains ours: ReDAct's negative result (reasoning-level AUROC 0.596) is not evidence that thought-level uncertainty is uninformative — it is evidence that **entropy is the wrong probe**. AUQ demonstrates that elicited confidence carries signal in agents, but only at **trajectory level, against trajectory labels, emitted entangled with the action**. Nobody has validated elicited U_T at **step granularity against step labels**, and nobody has decomposed how much of the signal comes from the elicitation contract vs. the architectural split. That validation and decomposition is the contribution (see §5.1, §6.2).

### 2.5 The world enters: action semantics as the interpretation layer

Even a cleanly measured (U_T, U_A) pair is uninterpretable on its own. The same pair means opposite things depending on what the action does to the world. The measurement primitive is:

$$\mathcal{U}_t = (U_T(t),\ U_A(t),\ \tau_t), \qquad \tau_t = (I_t, W_t, R_t, C_t)$$

where τ encodes the transition type: **I** = information-gathering (epistemic action), **W** = world-modifying, **R** = reversible, **C** = cost class.

| Pattern | Reading |
|---|---|
| high U_T, low U_A, I=1, W=0 | **Healthy epistemic recovery** — doesn't know, knows how to find out → proceed |
| high U_T, low U_A, I=0, W=0 | **Ungrounded continuation** — doesn't know, reasons on regardless → retrieve/verify |
| high U_T, low U_A, I=0, W=1, R=0 | **Dangerous commitment** — doesn't know, acts irreversibly → block |
| low U_T, high U_A | **Not epistemic failure** — planning ambiguity or tool-selection problem |

Same numbers, reversed semantics. Not one matrix — **a family of matrices indexed by transition type**. This is the genuinely agentic part of the theory: action semantics are the *interpretation layer of the measurement*, not an application layer on top of it.

**Hard constraint:** τ must come from the tool/environment specification, **never** from LLM self-classification. Otherwise: uncertain model → uncertain classification → uncertain interpretation, and the circle closes on itself. In benchmark environments τ is free from the transition definition itself.

### 2.6 Propagation, stated precisely: reset, not discount

The naive version — "prior uncertainty can be ignored" — is wrong. The precise version:

A successful epistemic action (I=1) **resolves** the uncertainty that motivated it. U_T(t+1) is generated fresh from S_{t+1}, and S_{t+1} already contains the observation. Prior uncertainty does not need to be carried forward — it is either **resolved** (the search worked, U drops) or it is **not** (the search failed, U stays high — *and that persistence is itself the signal*).

This is a **reset conditioned on action type and observation**, not aggregation with a discount factor. Propagation is not summing. It is asking: **did the transition deliver what its type promised?**

Which yields the claim that is testable and — per the positioning search — unclaimed:

> **The drift signal is a typed action failing to deliver its expected uncertainty reduction.**
> Not high U_T. Not accumulated U. The *failure of a typed action's promise*.

Properties of this claim: grounded in action semantics rather than fitted to outcomes; forward-looking (readable at the prefix); step-level falsifiable once labels exist.

**Published evidence that level-based reading fails exactly here — AUQ's "Delusion Gap."** AUQ's own analysis (their §4.3, App. A.5.1) reports that when their level-triggered System 2 reflects on intractable failures, aggressive reflection can produce *Delusional Confirmation*: confidence rises sharply on a hallucinated plan, and failure cases show **larger** confidence gains than successes. Read through this framework, the mechanism is transparent: their trigger (ĉ < τ) and their post-hoc reading both consume the **level** of confidence, so a re-verbalized upward jump is indistinguishable from genuine resolution. A promise-check is not fooled the same way: in the delusional case, no epistemic transition delivered new information — the confidence rose without an observation that licensed it. Their "True Correction" vs. "Delusional Confirmation" distinction is precisely the distinction V(t) is built to make, and their published scatter plots are evidence that a deployed level-based mechanism cannot make it. This goes in the E3 motivation, with citation.

### 2.7 Why this is one paper, not two

Measurement and propagation are **the same object viewed at t and t+1**. The typed, decoupled, elicited measurement at t is what makes the promise-check at t+1 well-defined. Without typed measurement, "did the promise hold" has no referent; without the promise-check, cross-step reading collapses back into aggregation.

This also resolves the apparent tension between locality and propagation: steps are conditionally posed, all dependence lives in the state, and the object of interest is **how U at t shapes S_{t+1}** — not any sum over steps.

---

## 3. The SAUP Critique, Stated Fairly

The critique is **not** "aggregation is invalid." It is:

SAUP starts from step scores whose semantics are **untyped**, then learns how much each contributes to a terminal prediction — weights fitted to the very signal claimed to be uninformative. Learning is not inherently the problem. Learning weights over an already-collapsed scalar and treating the result as if it recovered the missing semantics — that is the problem.

Our order is reversed:

1. Separate the semantic objects (U_T, U_A — decoupled, elicited)
2. Identify the transition type (τ, from environment spec)
3. Apply the typed reading / promise-check online
4. *Derive* trajectory risk from typed local states, if a trajectory number is needed at all

---

## 4. The Circularity Problem (Labeling)

The deepest structural issue in the subfield:

**Step-level claims need step-level labels. The only widely available signal is task success — one bit per trajectory.** Using it forces aggregation; the granularity of the claim exceeds the granularity of the label. The survey (2602.05073) found only **4 of 44** agent benchmarks provide turn-level annotation; 30 provide a single bit.

Prefix scores do not escape it: scoring U(1..t) against a terminal bit still shares one label across all t.

**The escape is manufactured labels.** ReDAct did it: 2,411 ALFWorld steps, GPT-judge, correct/incorrect (1555/856 split), protocol published (their Fig. 9). Imperfect and contestable — it arguably measures *plausibility*, not correctness — but it breaks the circle.

**Consequence:** the labels are not downstream of the claim; they are a **precondition** for testing it. This is why judge validation (E0 in the spec) runs first: every downstream AUROC inherits label quality, and reporting label noise bounds the ceilings honestly.

---

## 5. Honest Risk Assessment

### 5.1 The elicitation defense is double-edged (highest risk)

Verbalized confidence has well-known pathologies: clustering at round numbers, sensitivity to prompt wording, mode-collapsed miscalibration. If E1 lands, the first skeptical response will not be "mechanism confirmed" — it will be **"you swapped one flawed probe for another; show me it's not a prompt artifact."**

The elicitation *is itself a generation with a contract*, which means the measurement depends on a researcher degree of freedom. This is deeper than a footnote: it is why the experimental program includes a robustness arm (E1b) with multiple elicitation phrasings, and why **discrimination (AUROC/PRR) and calibration (ECE) are reported separately, leading with discrimination**. The claim to establish is rank-stability of U_T across phrasings, not agreement of absolute values.

Two AUQ-derived updates to this risk. First, AUQ softens the naive version of the rebuttal — a published system already shows verbalized confidence discriminates in agents — but it sharpens the specific version: our claim is *step-level* discrimination against *step-level* labels, which AUQ never tested, so their trajectory-level success cannot be borrowed as evidence. Second, AUQ's Limitations note that verbalized-confidence quality **degrades below ~7B parameters**; the framework's instrument claim is therefore scoped to sufficiently capable models (Qwen3-80B clears this comfortably, but the scoping must be stated).

### 5.2 The probe/architecture confound

The thesis bundles two changes: a different **probe** (elicited vs. entropy) and a different **architecture** (decoupled vs. entangled). A single-condition experiment cannot attribute a positive result to either. The instinct-level bet, recorded here so it is a prediction and not a post-hoc story: **entangled + elicited may recover most of the signal**, because the elicitation prompt *is itself* a stage-specific contract. If so, the paper's center of gravity moves from "decoupling" to "elicitation + typing + reset" — which is arguably the stronger paper. The experimental design (2×2 factorial) makes that outcome a finding, not a failure.

**AUQ is inadvertent published support for this bet.** Their elicitation mapping Φ emits (action, confidence, explanation) in **one generation** — structurally, our Cell B — and it discriminates at trajectory level. This raises the prior on "Cell B recovers signal" and simultaneously raises the value of the 2×2: the decomposition question (elicitation vs. split, at step granularity) is now the adjudication of a *live, deployed* mechanism, not a hypothetical. The spec accordingly implements Cell B with AUQ's **verbatim elicitation template**, so Cell B doubles as a faithful step-level evaluation of their published probe.

### 5.3 The dangerous quadrant may be empty where labels exist

ALFWorld has almost no irreversible commits (W=1, R=0 is thin). The framework's *motivating example* — high U_T + confident irreversible action — may barely occur in the one environment with a labeled baseline. Survivable (the measurement claim does not depend on it), but the introduction must not lean on the dangerous-commit story harder than the evidence supports. The spec adds a small second environment (E2b) whose only job is an existence proof.

### 5.4 The Markov framing is nearly decorative

Addressed in §2.1. Keep it to one paragraph, tie it explicitly to the reset rule, or cut it.

### 5.5 Judge-label validity

"Meaningful exploration vs. cyclic behavior" may measure plausibility, not correctness. Not fixable at this scale; boundable via E0 human agreement.

---

## 6. Positioning

### 6.1 Verified prior work

| Paper | What it took |
|---|---|
| **ReDAct** (2604.07036, Apr 2026) | Two-call ReAct split with stage-specific contracts. Reasoning-level UQ at PRR 0.168–0.279, AUROC 0.596–0.682 vs. action-level 0.684–0.710. Concluded reasoning-level UQ has poor discriminative power; used action-level only. Tested MTE/PPL/SP + 12 more (App. D). **Did not test verbalized confidence.** |
| **AUQ** (2601.15703, Jan 2026, Salesforce) | Full read (Jul 2026). Dual-process **control** framework: System 1 keeps verbalized confidence + explanation in memory (soft attention constraint); System 2 = reflection triggered by **level threshold ĉ < τ** (τ ∈ [0.8, 0.95]). Elicitation is **entangled** — (action, ĉ, ê) in one generation, `<confidence>`/`<explanation>` tags (App. A.6.2). Evaluation is **trajectory-level only**: aggregators Φlast/Φavg/Φmin against terminal task success (T-ECE, T-BS, AUROC); no step labels, no action typing, no decoupling. App. A.5.4 argues verbalized > logits (occupies part of our §2.4). Reports the **Delusion Gap**: reflection inflates confidence most in failures (§4.3, A.5.1). Environments: ALFWorld 140 seen, WebShop 140 dev, 50-step cap; Related Work names operationalizing UQ for "branching and backtracking decisions" as the open direction. |
| **Matsnev** (2606.19559, Jun 2026, ITMO) | Decomposes action confidence vs. request uncertainty — **single forward pass**. SOTA on clarification benchmarks. Their stated next step: "move the decomposition out of the prompt." |
| **Survey** (2602.05073, Feb 2026) | Concedes the trajectory-UQ critique in its introduction. Source for the 4/44 labeling gap. |

### 6.2 The claim that is left

Revised after the AUQ full read. "Elicitation works in agents" is no longer claimable — AUQ shows it at trajectory level. What no prior work does:

> Prior work either elicits uncertainty **entangled with the action and validates it only at trajectory level against terminal success** (AUQ), decomposes it **within a single forward pass** (Matsnev), or probes the reasoning stage with **format-blind entropy measures and finds it uninformative** (ReDAct). We provide the first **step-level validation** of elicited agentic uncertainty against step-level labels; we **decompose** the signal's source between the elicitation contract and the architectural split (a 2×2 no prior work runs); we show the measurement is interpretable only **relative to environment-derived action type**; and we show drift is signaled by the **failure of a typed action to deliver its promised uncertainty reduction** — a promise-check that a deployed level-threshold mechanism demonstrably cannot make (AUQ's own Delusion Gap).

The novelty is the **measurement validation and its granularity**, not the probe.

### 6.3 Timeline pressure

Jan → Apr → Jun 2026: three papers converging from three directions. The window is measured in **months** — and the AUQ full read tightens it: this is Salesforce, training-free (trivially replicable), already integrated into their enterprise deep-research stack, and their Related Work explicitly names operationalizing uncertainty signals to control **branching and backtracking** as the open direction. They are one step-level-labels decision away from adjacent territory. Sequencing consequence (reflected in the spec): after the instrument test, the *propagation* result is secured before the supporting experiments, because promise-violation-as-drift-signal is the differentiating claim against this cluster — and E3 now includes their level-threshold trigger as a named baseline, so the differentiation is measured, not asserted.

---

## 7. Relationship to the Experimental Program

The paper makes four claims, each with its own falsification path, inheriting in strict order:

| # | Claim | Test | Kills what if it fails |
|---|---|---|---|
| 1 | **Instrument**: elicited U_T carries signal entropy misses | E1 (2×2) + E1b (robustness) | Everything. Full stop. |
| 2 | **Architecture**: physical decoupling adds signal beyond elicitation | E1 cells B vs. D | The decoupling story; paper re-centers on elicitation + typing + reset |
| 3 | **Semantics**: typing by τ improves predictive validity | E2 (stratified vs. pooled) + E2b (existence) | The interpretation-layer claim; matrix becomes illustrative |
| 4 | **Propagation**: promise-violation predicts error better than level, accumulation, or AUQ's level-threshold trigger | E3 (4 baselines) | The reset rule; framing retreats to per-step measurement only |

Kill-switch: if claim 1 fails (elicited ≈ entropy in all cells), the thesis is dead and no downstream experiment resurrects it. Pre-commit interpretations of all E1 outcomes **in writing before running** (done — see spec §E1, "Outcome table").

Full specifications, protocols, and implementation detail: `uq_experiments.md`.
