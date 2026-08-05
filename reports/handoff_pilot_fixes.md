# HANDOFF: Pre-Full-Run Fixes (Pilot Review → Regeneration Gate)
## Amendments A8–A13 · 2026-07-22 · applies to uq_experiments_v2.md + driver codebase

**Status:** decisions FINAL (ratified by Taehyun after slice review + full-corpus
validation). All changes are pre-data for the full run — the pilot is superseded and
will be regenerated. Doc agent and code agent apply this in one pass; nothing here is
optional. Flag conflicts; do not silently resolve.

**Pilot verdict being acted on:** plumbing validated (logprobs/top-20/spans/probe
parsing/seeds/loop accounting all correct); two design defects (thought-stage
contamination by action vocabulary; τ absent) and one design-point divergence (only
the post-hoc probe class was built; no in-generation elicitation; entangled arm is
neither AUQ nor canonical ReAct).

---

## A8 — Thought contract: restore the pre-action epistemic state

**Defect:** decoupled thought prompt included the full AVAILABLE COMMANDS list
(copied from ReDAct's reasoning prompt); 593/702 thoughts contained the chosen
action string, 432 ended with it; all 3510 thought-stage probes conditioned on
thought+action. U_T never measured a pre-action state.

**Fixes:**
1. `prompts/decoupled_thought_v4.txt`: REMOVE the AVAILABLE COMMANDS block entirely.
   Contract: task + history + "Think step by step about the current situation: what
   is known, what is unknown, and what needs to be determined next." No action
   vocabulary anywhere in the prompt. (Action call keeps the full admissible list
   and its constrained contract — verify unchanged.)
2. **Defensive trim rule (driver):** the thought span terminates before any trailing
   line that exactly matches an admissible command (case/whitespace-normalized).
   Log `thought_trimmed: bool` and the trimmed text. Thought-stage probes condition
   on the TRIMMED span only; action-stage probes on (trimmed thought + action).
3. **Paper note (doc agent, theory doc anchor discussion):** ReDAct's own reasoning
   prompt contains AVAILABLE COMMANDS — their "reasoning-stage" uncertainty also
   conditioned on the action vocabulary, an interpretive caveat on their negative
   result. Our deviation from their thought contract is disclosed and motivated by
   exactly this.

## A9 — Build the in-generation elicited class (both arms)

**Decision 1 (ratified): the elicited class is mandatory.** Without it the probe
taxonomy loses a class, H4 has no contract-carrying family, the two-horns comparison
is one-horned, and Cell B (AUQ verbatim, first step-level evaluation of a deployed
probe) is impossible.

1. `decoupled_thought_v4.txt` closes with the tag block:
   `<target>one short declarative claim about the environment that your next decision
   turns on</target>` then `<confidence>0.00-1.00 that this claim is true</confidence>`.
   Both parsed → `q_t_text`, `U_T_targeted_ingen` (U = 1 − c); both STRIPPED before
   the action call and before the thought span used by post-hoc probes
   (strip-before-pass invariant, unit-tested: no tag string in any downstream
   prompt).
2. Entangled arm = **AUQ System-1 verbatim**: their A.6.2 suffix
   (`<confidence>`/`<explanation>`) appended to the joint prompt; ĉ →
   `U_T_verbalized` (entangled row), explanation logged. In-context persistence of
   prior confidences is the published mechanism — do NOT strip in the entangled arm.
3. **Decision 3 (ratified): entangled history carries prior THOUGHTS** (full
   Thought/Action/Obs transcript, AUQ System-1 style). Rationale: the pilot's
   thought-free entangled arm matches no published architecture; and the
   self-conditioning entropy-collapse regime (our mechanistic account of ReDAct's
   0.596, a headline figure) structurally requires thoughts-in-history. Decoupled
   stays thought-free (ReDAct regenerate-each-step); the history asymmetry is part
   of the published-architecture contrast — do not symmetrize.

## A10 — Action-targeted in-gen probe (single tag)

**Decision 2 (ratified, simplified):** the decoupled action call carries ONE in-gen
tag on line 2: confidence that this action will achieve its intended effect as
stated in the reasoning → `U_A_targeted_ingen`. Stripped before env execution.
No generic in-gen action tag (generic action reading stays covered by post-hoc
P(True)/numeric on the action stage; entangled generic ĉ is AUQ's). Every roster
row populated; no contract carries two numbers.

## A11 — Parse robustness: continuation-repair, not evaluator calls

**Resolution of the "mathematically identical" question (recorded):** in-gen vs
separate emission are distribution-identical ONLY for a pure continuation of the
same context. The pilot's `sep_verbalized` is a different conditioning context
(third-person evaluator template, supplied text, T=0) — that is the **post-hoc
self-evaluation class** (Kim & Kang: context changes shift readings; supplied-text
framing drifts to plausibility). It stays, correctly labeled. The elicited class
uses **continuation-repair** for format robustness:
- Tag instruction lives in the agent prompt (in-gen design).
- On tag parse failure: truncate the completion at the expected tag start and
  re-sample the continuation of the SAME context (same prompt, same prefix), up to
  3 bounded retries, T unchanged; log `tag_retries`, raw failures kept.
- Same S ⇒ same conditional ⇒ distribution preserved by construction; report
  first-pass tag-compliance rate per arm (expected >90% at 35B; revisit only if
  catastrophically low).

**Probe-suite relabeling:** `posthoc_numeric` (0–100) is THE post-hoc numeric roster
row; `sep_verbalized` (0.00–1.00) is demoted to its wording variant in the E1b
robustness arm (46% identical values full-corpus — same probe, two scales). ptrue,
qt_extract, targeted(post-hoc) unchanged. NOTE the map now has both targeted
readings — in-gen declared-target `U_T_targeted_ingen` vs post-hoc extracted-target
`targeted` — their divergence is an E1b analysis (declared vs extracted q_t match
rate reported too).

## A12 — τ inline + backfill

1. Wire the §0.4 τ map into the driver: every `kind:"step"` record gains
   `tau: {I,W,R,C}` derived from `action_parsed`. Unit test per action family
   (mandatory; a silent mis-tag corrupts E2/E3 while E1 looks healthy). τ never
   from the model.
2. Backfill script for existing corpora (pilot + smoke) from `action_parsed` — the
   pilot stays usable for tooling tests even though it's superseded.

## A13 — Bookkeeping fixes

- Probe skip-reasons logged (`skip_reason: action_parse_failed` etc.) so coverage
  gaps are auditable (pilot: 4/157 entangled action-probe gaps were silent).
- Seed formula: add the task term — `seed = 1000 + task_index*100000 + step_idx*100
  + call_offset` — or log the deviation note if kept; either way E0-full and E1
  share the policy (A4 intent).
- Entangled action-span=None steps: keep graceful handling; now logged per A13.1.

---

## One-afternoon extraction from the superseded pilot (before regeneration)

Re-run thought-stage post-hoc probes on the TRIMMED thought span over the existing
pilot; compare against recorded probe-on-full values, same steps, paired. This
measures how much conditioning on the committed action shifted post-hoc U_T — a
quantified bound on the exact contamination A8 fixes, and the supplementary table
answering "did the contamination matter?" before anyone asks.

## Regeneration gate

Full run may start only when: (1) A8–A13 implemented; (2) audit script v2 (adapted
to the real multi-record schema: call/step/episode/probe kinds, `gen_logprobs`,
`config.seed`, τ present) passes on a fresh 5-episode smoke of BOTH arms with zero
blocking findings — including the new checks: tag present + parseable (post-repair)
in every thought/action; thought span excludes admissible-command trailing lines;
no tag text in any downstream prompt (decoupled); AUQ suffix present and thoughts
in history (entangled); τ on every step record with verb-consistency; per-step seeds
per the chosen formula; (3) H1–H4 + decision rules git-tagged (the freeze), with
A8–A13 recorded as pre-data amendments.
