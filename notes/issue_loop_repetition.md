# Issue note: byte-identical repeated reasoning in stuck episodes (E0 smoke, cc8a064)

Date: 2026-07-20 · Status: **RESOLVED** — Taehyun's positions adopted 2026-07-20 and
implemented as a pre-data amendment (schema 1.4.0); see the resolution block at the
end. Raised repeatedly by Taehyun while reviewing
`data/labels/smoke_entangled_auq.local.labeled.jsonl`; this note separates what is
settled from what was debated.

## 1. The observation

Episode `alfworld/look_at_obj_in_light-Bowl-None-DeskLamp-301/trial_T20190909_150719_492274`
(smoke, condition `entangled_auq`, Qwen3.6-35B-A3B, temp 0.7, 50-step cap, failed):

- Steps **9–49: 41 byte-identical `thought_text`s** (~1,550 chars each), all choosing
  action `look`, all receiving the identical observation, all judged `incorrect`,
  all reporting verbalized confidence **0.9** (`U_T_verbalized = 0.1`).
- A second episode (AlarmClock-DeskLamp-323) shows the same pattern with two
  alternating repeated states and occasional wording forks.
- 83 of the smoke's 104 step records belong to some repeated-thought group.

## 2. Settled: it is not an implementation bug

Falsification checks run against the raw records (all clean):

| Check | Result |
|---|---|
| Each step's prompt contains prior step's action, thought, observation (49/49 transitions) | pass |
| All 50 prompts distinct, strictly growing; step counter correct at every step | pass |
| Thought is a substring of *its own step's* generation (104/104, incl. all repeats) | pass |
| Not serving-cache replay: 48/50 generations byte-distinct, 4.3–6.6 s real inference per loop step | pass |
| Condition is entangled by design: one generation per step with think/action/confidence; no separate action call exists or should exist (decoupled = E1's ReDAct arm, different code path, test-covered) | pass |

## 3. Settled: the mechanism, in three layers

1. **Belief lock-in (semantic).** At step 9 the model concludes — after explicitly
   considering and dismissing the correct task interpretation — that the task is
   complete. Its subsequent action (`look`) is valid, succeeds, and returns a benign
   unchanged observation: no disconfirming evidence ever enters the context.
2. **Copy-conditioning (distributional).** The entangled history (AUQ's published
   design) carries prior thoughts verbatim. Each repetition becomes a stronger copy
   template: measured mean token entropy over the think span falls from ~0.44 nats
   (steps 0–8) to **0.009 nats** (steps 9+), i.e. ~99.9% top-token probability.
3. **Seed determinism (sampling).** Even at 0.009 nats, *independent* draws would
   reproduce the exact text only ~22–37% per step (recorded `thought_sp` ≈ 1.0–1.5
   nats ⇒ P(exact) = e^-sp); 41 consecutive exact copies would be ~10⁻²¹ —
   Taehyun's "statistically impossible" instinct was **correct**. The resolution:
   the driver reuses **one seed for every step of an episode** (spec §0.1
   determinism), so each step replays the same RNG stream against a near-identical
   distribution ⇒ deterministic reproduction. The randomness was spent once, at
   step 9.

So: the pipeline faithfully recorded a real model behavior, whose byte-exactness is
a deterministic consequence of two recorded design choices (thoughts-in-history,
per-episode seed) amplifying a real phenomenon (agent belief lock-in).

## 4. Open questions — the actual discussion agenda

These are not misunderstandings; they are legitimate design/validity questions the
observation exposes.

**Q1. Does token entropy measure the right thing under self-conditioning?**
On loop steps, low `thought_mte` reflects *linguistic* predictability (copying own
text from the prompt), not *epistemic* confidence. Entropy says "certain," the
verbalized probe says "0.9 confident," ground truth says "wrong" — three readings
diverging on the same steps. Position to defend: this is not a flaw but the very
contrast the 2×2 design measures (entangled vs decoupled isolates the self-copying
contribution, since the decoupled arm regenerates reasoning without prior thoughts
in context). Counter-position: if Cell A/B entropy is dominated by a copy artifact,
its AUROC is uninterpretable as "uncertainty quality." To discuss.

**Q2. Statistical treatment of loop steps.**
41/50 steps of one episode are one repeated state. Step-level pooled AUROC treats
them as 41 independent samples; they are ~1. Candidate mitigations (analysis-stage,
no generation change): trajectory-clustered bootstrap, per-episode weighting,
reporting a per-episode loop-collapse fraction as a covariate, and/or sensitivity
analysis with loop steps deduplicated. To decide before analysis is frozen.

**Q3. Seed policy and external validity.**
Per-episode seed reuse converts "mostly repeats with drift" into "locked exact
repetition." Real deployments sample fresh randomness per call; our loops are
therefore *more* absorbing than a production agent's. Candidate E1 amendment:
per-step seed (`seed_base + task_index * K + step_idx`) — keeps reproducibility,
restores across-step independence. Trade-off: breaks comparability with E0 and
changes the loop dynamics being measured. Pre-data decision for E1; NOT to be
changed mid-E0.

**Q4. Is the loop the phenomenon or an artifact?**
The Delusion Gap framing wants exactly this: an agent confidently asserting a
conclusion it once doubted, 41 times, while wrong. But if most miscalibrated steps
across the dataset come from a few collapsed episodes, the headline metric may be
measuring "propensity to lock into loops" rather than "step-level uncertainty
quality." Possibly both are worth reporting, separately.

## 5. Verdict in one paragraph

Not a bug, and not purely a misunderstanding: the statistical-impossibility
intuition was right and led to correctly identifying seed determinism as the final
mechanism. The experiment is implemented as specified; the specification's choices
(AUQ thoughts-in-history, per-episode seeds, 50-step cap) jointly make locked loops
an expected regime, and that regime stresses the validity of entropy-based probes
(Q1) and step-level pooling (Q2). Recommended: proceed with Step 4 unchanged (the
data is informative either way and the design is frozen), add the loop-collapse
fraction as a report-only metric, and resolve Q1–Q4 before the analysis stage is
frozen — Q3 before E1 config freeze.

## 6. Resolution (2026-07-20, Taehyun) — supersedes §5's recommendation

- **Q1**: finding, not flaw — but claimable only stratified. AUROC/PRR reported
  pooled AND loop/fresh-stratified (pre-registered in spec §0.7). If entropy fails
  only on loop steps, the claim narrows to the sharper mechanistic one: entropy is
  uninterpretable under the self-conditioning regime entangled thoughts-in-history
  induces — which retroactively explains ReDAct's 0.596. Honesty requirement kept:
  the verbalized probe also failed on these steps; report both, and note the typed
  trace catches the regime structurally when both scalars are pathological (§2.5).
- **Q2**: trajectory-clustered bootstrap was already mandated (§0.7); added the
  loop-collapse fraction covariate and a first-occurrence dedup sensitivity
  analysis. Loop step defined ENVIRONMENT-SIDE (repeated (action, observation)
  pair within episode — src/analysis/loop_steps.py), so the diagnostic is
  independent of every probe and survives the seed change. Per-episode weighting
  rejected as a primary analysis.
- **Q3**: **per-step seeds adopted, jointly for E0-full and E1** —
  seed = 1000 + task_index*100 + step_idx. §5's "proceed unchanged, decide before
  E1" had the coupling backwards: E0 validates the judge on the step distribution
  E1 will produce; a per-episode-seed E0 would validate against an artificially
  loop-locked population E1 never generates. Still pre-data (the smoke is a smoke).
- **Q4**: both, reported separately; the loop episode is the §2.5 punchline (no
  scalar probe catches it; the typed trace does). ReDAct's judge rubric explicitly
  targets cyclic behavior — cite when defending label validity on loop steps.
- **Sampling fix**: E0's 150-step annotation sample stratifies by τ × loop/fresh
  (83/104 smoke steps were loop-group members; unstratified, human κ would be
  measured almost entirely on repeated states).
- **Step 4**: cleared to proceed once this amendment lands and Step 3 smoke
  re-passes under it.

## 7. Addendum (2026-07-20): the per-step-seed smoke exposed a second latent mode

The 4bd6a08 smoke failed terminally: 71/104 steps were degenerate echoes of the
instruction suffix's bullet list (first sampled token `-`, ~16-token generations,
no think/action). Diagnosis against the raw records — NOT a "seed pathology":

1. Per-draw tail risk was always there. At temp 0.7 the model has a real per-draw
   probability (~5–15% in clean context) of continuing the instruction list (or
   emitting bare EOS — episode 16's mode in the first E0 run) instead of opening
   `<think>`. The old per-episode seed replayed one RNG stream, sampling this risk
   once per episode; per-step seeds sample it every step, making onset near-certain
   somewhere in a 50-step episode. The seeds didn't create the behavior — they
   measured it at the correct granularity.
2. The cascade was history poisoning: the raw-action fallback executed the echo
   line verbatim and rendered it into every later prompt as an `<action>`; 30/31
   and 39/40 of post-onset bad steps carried the first echo in their history.

Fix (schema 1.5.0, contract-level only): prefill `<think>` at the end of the
entangled prompt (the degenerate-opening branch becomes unreachable at token 1;
E1★'s logit-bias pin already sanctioned this), extend the one-re-draw retry to
degenerate generations, and bar EOS-repair on degenerate text. Probe semantics
untouched. Gate note for E0-full: with prefill, a surviving double-degenerate echo
would parse as a garbage non-empty thought, so the quality gate must also count
`generation_retry.retry_degenerate == true` steps.
