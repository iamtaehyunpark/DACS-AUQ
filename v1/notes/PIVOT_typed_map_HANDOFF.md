# PIVOT HANDOFF — from "verbalized wins" to the typed uncertainty map

**Status: DRAFT for PI sign-off. NOT frozen.** Three decisions (D1–D3, end of doc)
block the freeze because they touch H1/H4 and the kill-switch. Once resolved, this
becomes the single-pass edit spec for `uq_theory.md` and `uq_experiments.md`.

Date opened: 2026-07-21. Supersedes nothing until committed; the current §7 four-claim
table and the §E1 outcome table remain authoritative until the freeze commit.

---

## 0. The move in one line

The paper stops betting on **"verbalized (in-generation) U_T beats entropy"** (old §7
claim 1, the kill-switch) and instead asks: **which uncertainty estimator works for
which agentic object — Thought, Action, action-type, transition — and does any single
one work across all of them?** Decoupling stops being the novelty (ReDAct has priority)
and becomes the *coordinate system* the comparison runs in.

New central claim (keep verbatim, one tightening from the proposal):

> No uncertainty estimator is intrinsically agentic; its meaning and utility depend on
> the stage it measures, the transition the action induces, and whether that transition
> delivers its expected uncertainty effect.

Abstract's empirical last line:

> We provide the first stage-separated, action-typed, perturbation-validated map of
> where existing uncertainty estimators work, fail, and change meaning inside an agent.

Framing (not "a new decoupled architecture"): **A systematic study and framework for
decoupled, action-conditioned uncertainty measurement and control in LLM agents.**

---

## 1. Old claim → new home (maps the real §7 table; nothing silently drops)

| Old §7 claim | Old status | New home | What changed |
|---|---|---|---|
| **1. Instrument** — verbalized U_T carries signal entropy misses | Kill-switch; E1 2×2 decides everything | **Row of the map** (verbalized = one *m* in the Thought column) + **H1** (do rankings reverse across stages) | De-privileged. Verbalized is no longer crowned pre-data; it competes. Its win, if it wins, lands *with* the comparison that makes it credible. |
| **2. Architecture** — decoupling adds signal beyond the contract | E1 cells B vs D | **H4** (entanglement ablation with a *mechanism prediction*) | Sharpened, not dropped. §2.3 gives a falsifiable form: token-intrinsic metrics invariant / contract-carrying shift — **under matched contract** (see Catch 1 / D2). |
| **3. Semantics** — typing by τ improves validity | E2 stratified vs pooled | **Axis of every cell** (τ in every record) + **H2** (typed beats pooled across *multiple* metric families) | Strengthened: probe-independent now. Can't be dismissed as an artifact of one confidence probe. |
| **4. Propagation** — promise-violation beats level | E3, 4 baselines | **H3** (Δ beats level for failed epistemic transitions, ≥1 metric) + the map's **delta column** | Preserved and generalized. No benchmark could *define* this column without our §2.6 reset rule — the theory is why the instrument has that dimension. |

The §2 argument chain (2.1 ontological → 2.2 semantic → 2.3 autoregression → 2.4 probe
→ 2.5 action semantics → 2.6 reset → 2.7 one-paper) is **retained intact as the
framework spine** — it now *justifies the axes* rather than defending one probe. The §2.7
sentence ("measurement at t and the promise at t+1 are the same object viewed twice")
becomes the narrative's closing move.

---

## 2. H1–H4 — replaces the §7 four-claim table AND the §E1 outcome table

Pre-registered, structural (not metric-crowning), each with a falsification path.

- **H1 (stage reversal).** Metric rankings by discrimination reverse between the Thought
  stage and the Action stage: rank_m AUROC(U_T^m) ≠ rank_m AUROC(U_A^m). Decided by
  paired bootstrap CIs on AUROC differences (D3), not eyeball.
- **H2 (typing generalizes).** Typed models g_m(U_T,U_A | τ) beat pooled across **≥2
  metric families**, not just one. Kills "typing helps because of one probe's quirk."
- **H3 (transition beats level).** For failed epistemic transitions (τ.I=1), the promise
  delta ΔU_T^m predicts subsequent error better than the level, for **≥1** estimator m.
  This is §2.6's reset rule made empirical, tested across estimators not asserted for one.
- **H4 (entanglement mechanism).** Under **matched contract** (contract toggled, prompt +
  seed held fixed — the E1b contamination-ablation design, NOT a raw entangled-vs-
  decoupled comparison; see Catch 1): token-intrinsic metrics (MTE/PPL/SP) are invariant
  entangled↔decoupled, while the contract-carrying metric (in-generation verbalized)
  shifts. Either half failing is informative. Derived from §2.3, not hunched.

---

## 3. New kill-switch — replaces §7's single-line kill-switch

The thesis stops **only if ALL of the following hold** (four-way conjunction, plus a
power clause so "boring" can't be "underpowered"):

1. Stage separation reveals no metric differences (H1 null — *and CIs are tight enough
   to distinguish a true null from noise*, D3);
2. Action typing adds no predictive/control value (H2 null across all families);
3. Transition deltas offer no advantage over levels (H3 null for every estimator);
4. Decoupled and entangled measurements are behaviorally indistinguishable under matched
   contract (H4 null both halves).

Honesty note to write into the doc: the pivot **relocates** outcome risk, doesn't remove
it. Old bad outcome: "verbalized ≈ entropy." New bad outcome: "one metric wins
everywhere, rankings stable, map boring" — which collapses back toward the single-winner
paper. That outcome is *less* bad (a stable ranking is still a result; H2/H3 can land
independently), which is why the pivot is net risk-reducing — but it is named, not hidden.

---

## 4. Metric cap — the coverage-treadmill boundary, pre-committed

The benchmark genre's real killer is "add semantic entropy, add 5 models, add 3 envs."
Fix the boundary now, with citable justification.

| Metric family | Thought | Action | Notes |
|---|---|---|---|
| Mean token entropy (MTE) | ✓ | ✓ | requires reasoning-channel logprobs → **D1** |
| Perplexity (PPL) | ✓ | ✓ | same |
| Sequence prob / NLL | ✓ | ✓ | |
| In-generation verbalized | ✓ | ✓ | = old Cell B, AUQ verbatim template; relocates into H4 ablation |
| **Targeted verbalized u(q_t)** | ✓ | — | Amendment 3a — the row most differentiated from AUQ's generic ĉ; do NOT drop |
| Post-hoc numeric | ✓ | ✓ | comparator (§5.1 plausibility exposure) |
| Post-hoc verbal scale | ✓ | optional | |
| Yes/no logprob | ✓ | optional | |
| **ΔH_k** (TEPO) | ✓ | — | delta family, for H3's E3 column |
| **PA** (checkpoint-pair) | ✓ | — | **feasibility-gated**; include only if the ckpt pair clears cost |

**Deferred, with the reason stated (not an excuse):** semantic-entropy /
sampling-/consistency-based methods — prohibitive inference cost in long-horizon agentic
settings, per the survey's own §4.1. Strong epistemic Thought-labels → future work
(conservative framing below carries the paper without them).

**Roster / envs capped:** the E1★.2 three-scale Qwen roster (down to the Qwen3.5-4B
sweep floor); Llama-3.3-70B disjoint judge; ALFWorld + WebShop only.

**Durable artifact (the genre's insurance):** released harness + judge-validated,
perturbation-backed, typed step-label corpus — keeps its value even if any single finding
is scooped at the field's monthly cadence.

---

## 5. Experiment renumbering (maps to existing E-sections)

| New | Was | Content |
|---|---|---|
| **E1 — stage-wise metric map** (primary) | E1 2×2, decoupled half | Decoupled agent; every metric × {Thought, Action}; AUROC/PRR/ECE + rank correlations + action-type strata + bootstrap CIs. Headline = the metric×stage map, not "D>C". |
| **E1b — entanglement ablation** (secondary) | E1 entangled half + old E1b | H4, matched-contract. Cell B (AUQ verbatim) survives here as the in-generation verbalized row. |
| **E1c — perturbation battery** (validity column) | old E2b-adjacent | Each estimator scored on causal response to manipulated observations (resolves-on-informative / persists-on-corrupted / responds-on-contradictory). Exposes plausibility meters (Kim & Kang defense, built into structure). |
| **E2 — typed vs pooled** | E2 | H2 across metric families. |
| **E3 — promise/transition** | E3 | H3; ΔU_T^m per estimator, τ.I=1, reset-fresh per §2.6. The map's delta column; arrives as the framework's culmination, not an appendix. |
| **E5 — cost** | E5 | unchanged, overhead accounting. |

Generation cost barely moves: still two runs (decoupled-primary + entangled-ablation);
growth is all on the cheap analysis side. ~2–2.5-week budget holds **if the §4 cap holds.**

---

## 6. Labeling — conservative framing (unchanged from Amendment 3b)

Call the quantities **Thought-stage / Action-stage uncertainty estimators**, evaluated by
(a) judge-label discrimination AND (b) the E1c perturbation battery — NOT "validated
epistemic uncertainty measures." A metric that predicts judge labels but fails
perturbations is exposed as a plausibility meter. No new annotation protocol. Strong
epistemic labels stay in future work. E0 is **unchanged and more central** — every cell
inherits its labels; the architecture-invariant label design (actions+observations only)
is what lets the E0 decision transfer to the new runtime.

---

## 7. What does NOT change

- E0 judge validation (local earned E1, κ-gap 0.078) — inherited by every cell.
- τ tagging from the environment (§2.5 hard constraint: never LLM self-classification).
- Loop/fresh stratification (§0.7) — every map cell reported both strata.
- Dual labeling (local decisional + gpt-5.2 sensitivity) — applies to the whole map.
- The §2 argument chain — retained as the framework spine.
- The system rebuild (src/runtime/, steps 0–3) — theory-free, proceeds in parallel;
  schema 2.0.0 ("store every assistant turn whole") already satisfies "compute any
  metric offline," so it needs no pivot input except the frozen §4 metric list before
  step-4 probes.

---

## 8. THREE DECISIONS THAT BLOCK THE FREEZE

**D1 — reasoning-channel logprobs (theory-gating, not just runtime).** Run one live chat
call to the served Qwen thinking-model with logprobs on, thinking enabled. Confirm
per-token logprobs come back on BOTH content and reasoning channels. If reasoning-channel
logprobs are absent, the Thought × {MTE, PPL, SP} quadrant is uncomputable natively and
H1 loses half its table — we'd have to force reasoning into visible content (string
surgery, the thing the rebuild kills). **This must pass before H1/H4 freeze.** ~20 min.

**D2 — H4 phrasing.** Confirm H4 is tested via the **matched-contract ablation** (E1b
contamination design: contract toggled, prompt+seed fixed), NOT a raw entangled-vs-
decoupled comparison. §2.3's own text shows the raw comparison confounds contract with
action-grammar and thought-conditioning. Sign off on the matched phrasing → it goes in
the freeze.

**D3 — H1 power rule.** Confirm H1 is decided by paired bootstrap CIs on AUROC
differences (bootstrap.py) with a pre-registered n and a power clause in the kill-switch,
so a null ranking-reversal is distinguishable from an underpowered one. Sign off → freeze.

Once D1–D3 are answered, this doc becomes the single-pass edit spec: rewrite §7
(claims→H1-H4), replace the §E1 outcome table, install the new kill-switch, add the §4
cap table, renumber E1/E1b/E1c/E2/E3.
