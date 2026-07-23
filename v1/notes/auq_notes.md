# AUQ — Paper Notes (source of Cell B probe + trajectory metrics + Delusion Gap)

**Agentic Uncertainty Quantification (AUQ)** — arXiv:2601.15703v1 (22 Jan 2026), Salesforce AI Research
(Zhang, Choubey, Huang, Xiong, Wu). PDF: `/Users/t/Documents/SCLAB/dacs/AUQ_Salesforce.pdf`.
Extracted text: scratchpad `auq.txt` (36pp).

## One-line thesis
Dual-Process **control** framework turning verbalized uncertainty into bi-directional control signals:
- **System 1 = Uncertainty-Aware Memory (UAM)** (Forward): elicit verbalized confidence ĉ + explanation ê at
  each step, keep (ĉ,ê) in context → "soft cognitive constraint" via attention suppresses overconfidence.
- **System 2 = Uncertainty-Aware Reflection (UAR)** (Inverse): triggered by **level threshold S(h_t)=𝟙[ĉ_t<τ]**,
  τ∈[0.8,0.95] (default 0.85; DeepResearch 0.95). Uses ê as a "rational cue" for Best-of-N (N=3) reflection,
  consistency-weighted selection. Training-free.

## Elicitation mapping Φ — this IS our Cell B probe
Φ: h_t → (a_t, ĉ_t, ê_t). Agent emits **action + `<confidence>` (0.0–1.0) + `<explanation>` in ONE generation**.
Verbatim suffix in `prompts/elicit_auq_entangled.txt` (App A.6.2). Baseline system prompt (`<think>`/`<action>`
tags) in `prompts/auq_baseline_system.txt` (App A.6.1). Our `U_auq_entangled = 1 − ĉ`.
**Entanglement caveat (by design):** ĉ,ê are in the same generation the action conditions on and are propagated
in memory — this feedback is exactly the entanglement our paper measures; do NOT "fix" it.

## Evaluation — TRAJECTORY-LEVEL ONLY (the gap we fill)
AUQ has **no step labels, no action typing, no decoupling**. It aggregates per-step ĉ into a trajectory scalar
C(τ)=Φ(c) via three aggregators (our metrics §0.7 "comparability suite"):
- **Φ_last** = ĉ_T (end-state)   **Φ_avg** = mean_t ĉ_t (overall)   **Φ_min** = min_t ĉ_t (weakest-link / process reliability)
Trajectory metrics (App A.3.4): **T-ECE** (binned |acc−conf| over trajectories), **T-BS** (Brier / MSE of C(τ) vs
binary success), **trajectory-AUROC** (C(τ) as classifier for task success). Y∈{0,1} = terminal task success.

## Key result numbers (ALFWorld / WebShop)
- ReAct success: ALFWorld **63.6%**, WebShop 29.3%. Dual-Process(AUQ): ALFWorld **74.3%** (+10.7), WebShop 42.9%.
- Trajectory-AUROC (Table 2): ReAct Φ_last 0.913 / Φ_avg 0.783 / Φ_min 0.667. AUQ 0.968 / 0.905 / 0.791.
  → verbalized confidence discriminates task success well **at trajectory level** — but never tested per-step.
- Verbalized confidence quality **degrades below ~7B params** (Limitations) → instrument scoped to capable models.

## Protocol (App A.3.1) — this is what our spec AUQ-matches
- **ALFWorld: Seen Evaluation Set, 140 unique environments**, metric = Success Rate.
- **WebShop: 140 episodes randomly sampled from Development Set** (for E2b), high observation noise.
- **50-step cap** on both. ReAct/System-1 run **greedy temp=0.0**; System 2 sampling temp=0.7.
- DeepResearch Bench: 100 PhD tasks, RACE rubric (not relevant to us).
- Models: GPT-5.1, GPT-4.1, GPT-4o, Gemini-2.5-Pro/Flash, **Qwen3-235B**, DeepSeek-V3.1. Judge for DeepResearch
  = Gemini-2.5-Pro (RACE). NOTE: AUQ used **GPT-5.1** not GPT-5.2; for ALFWorld/WebShop success is env-derived, no judge.

## Why verbalized > logits (App A.5.4) — SHARED premise, attribute it (theory §2.4)
"Token trap": model statistically confident in next grammatical token while epistemically uncertain about content;
averaging logprobs over long CoT adds length bias that washes out a specific logical flaw. Verbalized confidence =
"metacognitive compression." Builds on Lin et al. 2022 (verbalized), Tian et al. 2023 (elicited calibration under RLHF).
→ This is now shared background, NOT our insight. Our contribution is step-level validation + the entropy-vs-elicit decomposition.

## The Delusion Gap (§4.3, App A.5.1) — MOTIVATES E3 (theory §2.6)
System 2 reflection inflates confidence most in **failures**. Three intervention modes:
1. **Validation** (high c_init→high c_final, success): reflection = sanity check, small Δ.
2. **True Correction** (low→high, success): ideal; c_init≈0.6–0.8, Δ≈+0.3.
3. **Delusional Confirmation** (low→high, FAILURE): fabricates plausible-but-wrong plan, adopts w/ high confidence
   (e.g. 0.5→0.9). Failing agents look *more* confident in their gains.
Quadrant vs ReAct (Fig 9): 60.0% shared success, 22.1% shared failure, **14.3% correction**, **3.6% regression** (~4:1).
→ Their trigger 𝟙[ĉ<τ] and post-hoc reading both consume the **level** of confidence, so a re-verbalized upward jump
is indistinguishable from genuine resolution. Our V(t) promise-check (did a typed epistemic action deliver info?)
is built to make exactly their True-Correction vs Delusional-Confirmation distinction. E3 uses their level-threshold
τ∈{0.8,0.85,0.9,0.95} as a NAMED, measured baseline (best-of-sweep, generous).

## System 2 mechanics (reference only — NOT in our E0/E1 measurement pipeline)
Best-of-N N=3, reflection depth D=3, consistency-weighted score S(a)=(|C_a|/N)·mean_{i∈C_a}ĉ_i (semantic clusters;
ALFWorld/WebShop use normalized string match on `<action>` content). Memory Expansion: if still <τ after reflection
in limited-history (h=5) setting, retrieve full history and re-reflect once. Reflection + Memory-Expansion prompts
in `prompts/auq_reflection.txt`. Algorithm 1 p.19.

## What we take
- Cell B verbatim elicitation suffix (probe 4); baseline `<think>/<action>` prompt; τ range for E3 baseline;
  Φ_last/avg/min + T-ECE/T-BS/traj-AUROC comparability suite; 140-seen/50-cap protocol; Delusion-Gap framing for E3.
- AUQ is "inadvertent published support" for the E1 "Cell B recovers signal" bet (theory §5.2): their Φ emits
  (action,ĉ,ê) in one generation = structurally our Cell B, and it discriminates at trajectory level.
