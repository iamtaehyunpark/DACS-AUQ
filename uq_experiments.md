# Experimental Specification: Decoupled, Action-Conditioned Step-Wise UQ
## Implementation-Ready Spec (for CLI coding agent)

Companion to `uq_theory.md`. This document is written so that a coding agent can implement each experiment without consulting the theory doc. Where a design decision exists, it is stated as a decision, not an option.

---

## 0. Global Setup

### 0.1 Stack

- **Agent model:** Qwen3-80B (instruct variant), served via vLLM. All conditions use the **same checkpoint, same sampling params** unless a condition explicitly varies them.
  - Default sampling: `temperature=0.7, top_p=0.95, max_tokens=512` per stage.
  - Logprobs: request `logprobs=20` on every generation (needed for entropy/PPL/SP baselines and yes/no-token probes).
- **Judge model:** GPT-5.2 via API, `temperature=0`, using ReDAct's Fig. 9 judge prompt verbatim (transcribe from paper; store at `prompts/judge_redact_fig9.txt`).
- **Environment:** ALFWorld (TextWorld backend), **Seen evaluation split, all 140 episodes** — matching AUQ's protocol exactly for cross-paper comparability (AUQ App. A.3.1: 140 seen episodes, 50-step cap). Episode step cap: **50** (AUQ-matched; also prevents runaway trajectories). If total labeled steps fall short of ~2,400 (ReDAct scale), extend with the Unseen split and report the extension. Secondary environment for E2b only (§E2b.1).
- **Repro:** fixed seeds per trajectory (`seed = 1000 + task_index`); log seed, model revision, vLLM version, and full sampling config into every record.
- **Cross-paper comparability note:** AUQ ran their ReAct/System-1 baseline greedy (`temperature=0.0`); ReDAct's settings govern our anchor cell. We keep one sampling config across all cells (ours), and additionally note in results that our Cell A anchor is checked against ReDAct's band, while environment/protocol (140 seen, 50-step cap) is AUQ-matched. Do not mix sampling configs across cells to chase either paper's exact numbers.

### 0.2 Repository layout

```
uq-agentic/
├── configs/               # yaml per experiment/condition
├── prompts/               # ALL prompts as versioned text files, never inline
│   ├── entangled_react.txt
│   ├── decoupled_thought.txt
│   ├── decoupled_action.txt
│   ├── elicit_numeric.txt
│   ├── elicit_verbal.txt
│   ├── elicit_yesno.txt
│   ├── elicit_auq_entangled.txt   # AUQ App. A.6.2 elicitation suffix, VERBATIM (Cell B canonical)
│   └── judge_redact_fig9.txt
├── src/
│   ├── env/               # ALFWorld wrapper + tau tagging
│   ├── agent/             # entangled + decoupled loops
│   ├── probes/            # entropy, ppl, sp, elicitation
│   ├── judge/             # labeling pipeline
│   ├── analysis/          # metrics, bootstrap, plots
│   └── run.py             # single entrypoint: python -m src.run --config configs/<x>.yaml
├── data/
│   ├── trajectories/      # raw jsonl, one file per condition
│   ├── labels/            # judge + human labels
│   └── analysis/          # computed metrics, cached
└── results/               # tables + figures, one dir per experiment
```

### 0.3 Core data schema

Every step in every condition is one JSONL record. **This schema is frozen; all experiments read it.**

```json
{
  "run_id": "e1_cellD_seed1042",
  "condition": "decoupled_elicited",
  "task_id": "alfworld/pick_and_place-042",
  "step_idx": 7,
  "state_summary_hash": "sha256:...",
  "thought_text": "...",
  "action_text": "go to drawer 2",
  "action_parsed": {"verb": "goto", "arg": "drawer 2"},
  "tau": {"I": 0, "W": 0, "R": 1, "C": "free"},
  "observation_text": "...",
  "probes": {
    "U_T_elicited_numeric": 0.35,
    "U_T_elicited_verbal": 0.40,
    "U_T_yesno_logprob": 0.31,
    "U_auq_entangled": 0.15,
    "auq_explanation_text": "...",
    "U_A_elicited_numeric": 0.10,
    "thought_mte": 1.82,
    "thought_ppl": 4.1,
    "thought_sp": 0.88,
    "action_mte": 0.41,
    "action_ppl": 1.6,
    "action_sp": 0.97,
    "action_nll": 0.9
  },
  "sampling": {"temperature": 0.7, "top_p": 0.95, "seed": 1042},
  "label": {"judge": "correct", "judge_raw": "...", "human_1": null, "human_2": null},
  "timing": {"latency_ms": 840, "prompt_tokens": 1301, "completion_tokens": 96}
}
```

Notes:
- All `U_*` values normalized to [0,1] where 1 = maximally uncertain. Elicited confidence c ∈ [0,100] → U = 1 − c/100.
- `tau` is assigned by the environment wrapper (§0.4), **never** by the model.
- `probes` fields not applicable to a condition are `null`, not omitted.

### 0.4 τ tagging for ALFWorld (environment-derived, hardcoded)

Static mapping in `src/env/tau_map.py`:

| ALFWorld action family | I | W | R | C |
|---|---|---|---|---|
| `look`, `examine`, `inventory` | 1 | 0 | 1 | free |
| `go to X` | 1 | 0 | 1 | cheap |
| `open X`, `close X` | 0 | 1 | 1 | cheap |
| `take X from Y`, `put X in/on Y` | 0 | 1 | 1 | cheap |
| `heat X`, `cool X`, `clean X` | 0 | 1 | 0 | costly |
| `slice X` | 0 | 1 | 0 | costly |
| `use X` (e.g., lamp) | 0 | 1 | 1 | cheap |

(`heat/cool/clean/slice` treated as irreversible within an episode: state transformations ALFWorld does not undo.) The map is a config file; changing it is an experiment change, not a code change.

### 0.5 The two agent loops

**Entangled (baseline architecture).** Single call per step. Prompt = ReAct standard: task + history + `Thought:`/`Action:` few-shot format. Parse thought and action from one completion. Stop on `\nObservation`.

**Decoupled (test architecture).** Two calls per step with **distinct contracts**:
1. *Thought call* (`prompts/decoupled_thought.txt`): task + history; instruction: reason about current state, next sub-goal, what is known/unknown. **No action vocabulary in the prompt.** Free-form, ≤150 tokens.
2. *Action call* (`prompts/decoupled_action.txt`): fresh prompt containing `YOUR CURRENT REASONING: {thought}` + the admissible-commands list from the environment + "Output exactly one line, exactly one of the available commands." (Mirrors ReDAct's contract so the comparison is fair.)

**Elicitation calls** (probe, §0.6) are additional calls appended after the relevant stage; they never feed back into the agent's context (the agent does not see its own elicited number — measurement must not perturb the trajectory beyond the architecture change itself).

### 0.6 The three elicitation probes (E1b arms)

All elicitation calls: `temperature=0`, fresh call, context = everything the relevant stage saw plus the stage's own output.

1. **Numeric** (`elicit_numeric.txt`): "On a scale of 0–100, how confident are you that the reasoning above is factually correct and sufficient to decide the next action? Reply with a single integer." → U_T = 1 − x/100.
2. **Verbal-scale** (`elicit_verbal.txt`): 5-point scale {almost certain, likely, unsure, unlikely, almost certainly not} mapped to {0.05, 0.275, 0.5, 0.725, 0.95} uncertainty.
3. **Yes/no logprob** (`elicit_yesno.txt`): "Do you know enough to be confident in this reasoning? Answer Yes or No." → U_T = P("No") from first-token logprobs, renormalized over {Yes, No} token variants (handle leading-space and case variants; sum probability mass per class).

U_A elicitation: numeric probe only, worded for the action stage ("...that the action above is the correct next action?").

4. **AUQ-entangled** (`elicit_auq_entangled.txt`) — **applies to the entangled loop only, and is the canonical Cell B probe.** Not a separate call: AUQ's published elicitation suffix (their App. A.6.2) is appended to the entangled agent prompt itself, so the agent emits `<action>`, `<confidence>0.0–1.0</confidence>`, and `<explanation>` **in one generation** — exactly their mechanism, verbatim template. → `U_auq_entangled` = 1 − ĉ; store the explanation text (`auq_explanation_text`) for qualitative analysis. This makes Cell B a faithful step-level evaluation of a *published, deployed* probe rather than our own construction, which is worth more than any argument. **Caveat, logged:** unlike probes 1–3, this one feeds back into the agent's context (the confidence is in the generation the agent conditions its own action on) — that is inherent to AUQ's design and is exactly the entanglement being measured; do not "fix" it. The post-hoc numeric probe (probe 1) is *also* run on the same entangled trajectories so Cell B reports both variants: `in-generation (AUQ)` and `post-hoc numeric`.

Entropy-family baselines (computed from logprobs, no extra calls): mean token entropy (MTE), perplexity (PPL), normalized sequence probability (SP), per stage. Implement to match ReDAct App. D definitions.

### 0.7 Metrics module (`src/analysis/metrics.py`)

- **AUROC** of each probe vs. judge label (step-level, `incorrect` = positive class).
- **PRR** (prediction rejection ratio), ReDAct's definition, for direct Table-1 comparability.
- **ECE** (15 equal-mass bins) — reported separately, never headline.
- **Kendall's τ** between probe rankings (E1b).
- All point estimates with **bootstrap 95% CIs, resampled at the trajectory level** (steps within a trajectory are not independent; resampling at step level is wrong and a reviewer will catch it). 10,000 resamples.
- Paired comparisons (probe A vs. probe B on same steps): bootstrap the AUROC difference, report CI and p.
- **Trajectory-level comparability suite (AUQ-matched, secondary):** implement AUQ's three aggregators over per-step confidence — Φ_last = ĉ_T, Φ_min = min_t ĉ_t, Φ_avg = mean_t ĉ_t — and their trajectory metrics: T-ECE (binned |acc − conf| over trajectories), T-BS (mean squared error of C(τ) vs. binary success), and trajectory-AUROC (aggregated confidence as classifier score for task success). Purpose: one supplementary table showing our typed step measurements, aggregated their way, reproduce or beat AUQ-style trajectory calibration — connecting to §3's "derive trajectory risk from typed local states" and giving reviewers a familiar yardstick. **These never headline; step-level metrics do.**

---

## E0 — Judge Validation (run FIRST, blocks everything)

**Purpose:** every downstream AUROC inherits label quality. Bound it.

**Protocol:**
1. Generate 30 entangled trajectories (standard ReAct, config `e0_gen.yaml`) → expect ~250–400 steps. Randomly sample **150 steps**, stratified by τ cell (proportional, min 10 per non-empty cell).
2. Label all 150 with the GPT judge (Fig. 9 prompt).
3. Two human annotators label the same 150 independently, using the *same rubric text* as the judge prompt, blind to judge output. Annotation UI: a simple static HTML page reading the JSONL, radio buttons, exports CSV. (Generate this page; do not build infrastructure.)
4. Report: Cohen's κ human–human, κ judge–human (each), raw agreement %, and a confusion breakdown by τ cell.

**Decision rule:** proceed regardless of κ, but κ enters the paper as the label-noise bound. If judge–human κ < 0.4, add a sentence to every results table noting the ceiling; if < 0.2, escalate to Taehyun before running E1 (labels may need a different judge prompt).

**Budget:** ~half a day of compute + human annotation time.

---

## E1★ — Authoritative Execution Plan (supersedes §0.1 model choices and the E1 framing below where they conflict)

Decided 2026-07-16 after the AUQ/ReDAct full read and a server-capability check. This block is
authoritative; the original E1 text below is retained for its outcome-table reasoning, now re-keyed
onto the paired-difference decision metric defined here.

### E1★.1 Compute & infrastructure (verified on server `user@165.132.172.57`, mount `/data5/kje/MULTIAGENT`)

- 5× A100 80GB, vLLM 0.23.0, torch 2.11 (env `/opt/anaconda3/envs/yllm`). Shared box — check `nvidia-smi` before serving.
- **Build everything fresh in this repo (`/Users/t/github/DACS-AUQ`), a self-contained package under `src/` (spec §0.2).**
  DACS stays clean: **all experiment code is derived from the two papers + this spec, from scratch.** No code, no modules,
  no algorithms are lifted from another repo.
- **The `uala` codebase (`/data5/kje/MULTIAGENT/uala/uala`) is consulted ONLY for *environmental circumstance* — never for experiment code.**
  Legitimate references: how vLLM is launched on this box (flags, ports, tensor-parallel, served-model-name), where ALFWorld's
  data/config YAMLs live and how the split is selected, the conda env (`yllm`) and package versions, and the `lg` run/serve workflow.
  We do **not** import from it, edit it, or copy its metrics/judge/agent-loop logic — those we write ourselves against ReDAct App. A / AUQ App. A.6.
- **Design points our code must hit (from the papers, not from any repo):** SP/PPL/MTE per ReDAct App. A (SP = −Σ logp, PPL = mean NLL, MTE = mean top-k token entropy);
  PRR ≤50%-rejection per ReDAct App. C; tie-aware trajectory-level AUROC with 10k-resample bootstrap; ALFWorld **Seen split** with **admissible commands exposed** to the prompt;
  the ALFWorld judge uses ReDAct's Fig-9 **whole-trajectory → per-step JSON** prompt; unparseable elicitation → **excluded + exclusion-rate reported per cell**;
  τ tagger a pure env-string function with a unit test per action family; `VLLMClient` requesting logprobs=20, fixed seed, and pinning `<think>` via `logit_bias` if thinking is off.
- **Serving is shared infra, not code reuse:** we launch our own vLLM servers on the box (agent + judge on separate ports) and point our fresh `VLLMClient` at them.

### E1★.2 Model roster — single agent family (Qwen), disjoint judge family (Llama)

Within-family sweep makes capability a controlled axis (shared tokenizer/lineage/chat template), so the
"where elicitation stops working" boundary is a *scale* result, not scale-confounded-with-family.

| Role | Model | Availability | Notes |
|---|---|---|---|
| **Primary (decides E1 — only cell that runs full 2×2)** | Qwen3.6-35B-A3B | ✅ `/data5/user/hf_cache` | MoE (3B active), serves fast with logprobs; also the backtracking-paper instrument |
| Sweep floor | Qwen3.5-4B | ✅ `/data5/user/hf_cache` | Deliberately below AUQ's ~7B verbalization threshold — supposed to look bad; gives the scoping claim its edge |
| Sweep upper | 80B-class Qwen | ❌ **not cached** (galaxy nodes down) | **OPEN**: use Qwen3.5-27B (dense, cached at `/data3/hg_weight`) as upper, or download an 80B (disk 941G free, 87% full). Defer — sweep runs only after the outcome table fires |
| **Judge** | Llama-3.3-70B-Instruct | ✅ full bf16 `/data3/hg_weight/hg_weight` | Disjoint lineage kills correlated-plausibility failure; frozen ckpt + versioned prompt = reproducible labels. Fallback: Gemma-3-27B-it (same dir) |

Generational caveat (log it): primary is 3.6, floor/mids are 3.5 (only 3.6 in cache is the 35B-A3B).
Three scales only — a five-point curve is a different paper. **Middle point (35B) is primary; only it runs the full 2×2.**

**Thinking-mode decision (DECIDED 2026-07-16: native thinking OFF, frozen).** Qwen3.6-35B-A3B is a hybrid reasoning model.
E1 needs well-formed probes and a Cell A entropy anchor comparable to ReDAct's — a second native-CoT stream would blur what
"thought" means, break the yes/no first-token + numeric probes, and length-bias the thought entropy (the exact failure ReDAct/AUQ
warn about). So: native thinking **off**; the AUQ/ReDAct prompt's own reasoning channel (`<think>…</think>` entangled, or the
reasoning-call output decoupled) is the CoT we measure. Implementation: disable at the chat-template level (raw Completions prompt
that never emits the thinking trigger) **and** belt-and-suspenders `logit_bias` ban `<think>` if it is a single token. **Safety net:**
during the Cell A pilot (step 2), log the `<think>`-leak rate and per-probe parse rates; if leak > a few %, revisit before freeze.

### E1★.3 Generation & probes (as locked)

- ALFWorld **Seen split, all 140 tasks**, 50-step cap, `seed = 1000 + task_index`, one sampling config everywhere
  (`temperature=0.7, top_p=0.95, logprobs=20`).
  - **140 is native, not a selection (confirmed 2026-07-16):** `AlfredTWEnv(train_eval="eval_in_distribution")` with
    `regen_game_files: False` filters `$ALFWORLD_DATA/json_2.1.1/valid_seen` (242 raw dirs) to the 140 solvable games
    that have a built `game.tw-pddl` → `env.game_files` has exactly **140**. This IS AUQ's "140 unique environments" /
    ReDAct's seen set; no custom sampling. Data cache: `/home/user/.cache/alfworld`; env config: `configs/alfworld_base.yaml`.
  - Env integration + τ tagger validated end-to-end on real seen data (`scripts/smoke_env.py`): τ is **total** over the
    real admissible-command set (the only gap found — TextWorld's meta-command `help` — is now tagged I=1/free).
- **Primary = 2 generation runs:** (a) entangled-with-AUQ-suffix → Cells A+B; (b) decoupled (ReDAct two-call) → Cells C+D.
  Vanilla-ReAct third run **held in reserve** — trigger only if Cell A entropy looks pathological *and* debugging implicates the suffix.
- Cell B probe: AUQ verbatim in-generation `<confidence>` canonical + post-hoc numeric alongside. Cell D: post-hoc numeric
  primary; verbal + yes/no deferred to E1b on frozen trajectories.
- Entropy MTE/PPL/SP per ReDAct App. A, **computed within-cell only** — raw values never compared across cells (state as policy in
  the paper; cite Kim & Kang). Top-20 logprob entropy is a ranking-invariant approximation — fine for AUROC/PRR.

### E1★.4 Decision metric — paired difference, pre-frozen

For each architecture, decision variable **Δ = AUROC(elicited U_T) − AUROC(best entropy probe on the SAME steps)**,
trajectory-level bootstrap CI, 10k resamples. "Best entropy probe" chosen **within** each cell (generous to the baseline so a win means something).
The E1 outcome table keys on: **Δ_D** (does the instrument claim live), **Δ_B** (does elicitation alone recover it), and the
**B-vs-D paired comparison** (does the architectural split add anything). ReDAct's 0.596 appears once as anchor context — **never in a decision rule**.

### E1★.5 Order of operations (strict)

1. **E0 triangle first, expanded.** 30 entangled primary trajectories → 150 τ-stratified steps → **local Llama-3.3-70B judge + one frontier-API pass + two humans**.
   Pre-committed rule: local-vs-human κ within ~0.1 of frontier-vs-human κ → local judge earned, proceed; local clearly worse → fix judge prompt once, re-run triangle once; still worse → frontier API labels the headline runs, local judge demoted to the sweep. (~1 day + annotation.)
2. **Cell A pilot, 30 tasks.** Pipeline sanity only: entropy AUROC in a plausible band (~0.55–0.72), parse rates logged, τ tagging eyeballed on 20 steps. Cheapest place to catch a broken parser. (~1 day.)
3. **Freeze.** Prompts versioned, outcome table + decision rules committed, **git-tagged** so "before data" has a checkable timestamp.
4. **Full primary generation + labeling.** Both runs, every step judged (local, GPU-hours not dollars). ~1,500–2,000 steps.
5. **Analysis, outcome table fires.** Live outcome → **E3 immediately** on the already-logged Cell-D ΔU_T (re-analysis, near-free) → **then** the sweep extends the winning contrast to the upper + 4B point, each needing only the probe families on the cells the outcome made relevant (usually 2 runs/model, not 4).

Nothing in the sweep starts until the outcome table has fired. Primary-model E1 ≈ one week wall-clock, generation + judging dominant.

### E1★.6 Two failure modes to guard in code (build them in now)

- **Elicitation parse failures:** log every one with the raw completion; imputation policy fixed in advance — **unparseable → excluded from that probe's metrics, exclusion rate reported per cell** (Kim & Kang parse-rate lesson).
- **τ mis-tagging:** the τ tagger is a **pure function of the environment action string** with a **unit test per action family** — a silent mis-tag corrupts E2/E3 invisibly while leaving E1 looking fine.

---

## E1 — The Instrument Claim (2×2 factorial) ⚠️ DECIDES EVERYTHING

**Design:** two factors, fully crossed. Same **140 ALFWorld Seen-split tasks** (AUQ-matched, §0.1) in all cells, same seeds, 50-step cap, so trajectories are as comparable as the architecture change allows.

| | Probe: entropy-family (MTE/PPL/SP) | Probe: elicited U_T |
|---|---|---|
| **Arch: entangled** | **Cell A** — ReDAct replication anchor | **Cell B** — **AUQ's verbatim elicitation (probe 4)** + post-hoc numeric |
| **Arch: decoupled** | **Cell C** | **Cell D** — headline |

- Cells A+B share trajectories (one entangled run **with the AUQ elicitation suffix in the prompt** — this generates Cell B's in-generation probe natively; entropy for Cell A computed from the same run's logprobs; post-hoc numeric elicitation added via extra calls). **Note the consequence, accept it, report it:** the AUQ suffix in the prompt means the "entangled" run is AUQ-System-1-style, not vanilla ReAct. If Cell A's entropy anchor then misses ReDAct's band, generate a second vanilla-ReAct entangled run for the anchor only and report both — the suffix's effect on entropy is itself a (minor) finding.
- Cells C+D share trajectories (one decoupled run) likewise.
- So: **2 trajectory-generation runs (possibly 3, see above), 4 analysis cells.** With 140 tasks × ~8–15 steps, expect ~1,500–2,000 labeled steps; if short of ~2,400 (ReDAct scale), extend with Unseen-split tasks per §0.1. Label every step with the judge.

**Per-cell output:** AUROC + PRR for every probe against judge labels, with trajectory-level bootstrap CIs.

**Anchor check:** Cell A's MTE/PPL/SP AUROC must land near ReDAct's reported 0.596–0.682 band for reasoning-level. If it does not (±0.05), stop and debug the replication before interpreting anything else.

**Outcome table (pre-committed — do not reinterpret after seeing data):**

| Result | Interpretation | Consequence |
|---|---|---|
| D > A significantly; entropy flat across A/C | Elicitation reads what entropy cannot; contract mechanism confirmed | Paper proceeds as framed. Run E3 next. |
| B ≈ D > A; C ≈ A | Elicitation alone recovers the signal; decoupling adds nothing | **Recorded pre-registration bet.** Re-center paper on elicitation + typing + reset; decoupling becomes an ablation. Still run E3. |
| D > B > A | Both mechanisms contribute; clean decomposition | Strongest version of the paper. Run E3. |
| B ≈ D ≈ A ≈ C (all ~0.6) | Elicited U_T is no better than entropy | **THESIS DEAD. STOP.** Write up negative result; do not run E2/E3/E5. |
| D shifts vs. A but AUROC does not improve | Interference exists but does not matter | Much weaker paper; discuss with Taehyun before continuing. |

**Reading the outcome table post-AUQ:** because Cell B is AUQ's verbatim probe, the "B ≈ D > A" row now has a sharper meaning — *AUQ's published mechanism carries step-level signal, and the split adds nothing* — which is simultaneously a validation of their probe at a granularity they never tested and a demotion of our decoupling claim. Either way the paper reports the first step-level evaluation of a deployed elicitation mechanism. The prior on this row is now elevated (theory doc §5.2).

**Also log (required for E3):** per-step ΔU_T is computable only if U_T is recorded at every step in decoupled runs — it is, by schema. No extra work; noted so nobody "optimizes" it away.

**Budget:** ~1 week wall-clock including labeling.

---

## E1b — Elicitation Robustness (runs inside E1, same trajectories)

**Purpose:** pre-empt the "prompt artifact" rebuttal (theory doc §5.1).

**Protocol:**
1. On Cell B and Cell D trajectories, run **all post-hoc elicitation probes** (§0.6 probes 1–3) on every step. (Numeric is already there; add verbal + yes/no — re-elicitation on frozen trajectories, cheap.) Cell B additionally carries the in-generation AUQ probe (probe 4) natively, giving Cell B four probe readings per step.
2. One temperature arm: repeat numeric elicitation at `temperature=0.7`, 3 samples per step, take the mean.

**Analysis:**
- Kendall's τ between the probes' step rankings (pairwise, per cell; in Cell B this includes AUQ-in-generation vs. post-hoc numeric — **the rank agreement between AUQ's probe and a post-hoc probe on identical steps is itself a publishable side-result**, since it measures how much the in-generation entanglement perturbs the reading).
- AUROC per probe per cell, same bootstrap protocol.
- **Claim to establish:** rank-stability. Absolute values may disagree; the *ordering* of steps by U_T must be stable (target: pairwise τ ≥ 0.5 and all three probes' AUROC CIs overlapping each other while excluding the entropy baseline).
- Report round-number clustering: histogram of raw numeric responses (expect spikes at 50/70/80/90 — show it, own it, demonstrate ranking survives it).

**Budget:** ~1 day of extra elicitation calls + analysis. No new trajectories.

---

## E2 — The Semantics Claim (stratified vs. pooled predictive validity)

**Precondition:** E1 landed (any non-dead outcome).

**Purpose:** turn "same numbers, different meanings under different τ" into a likelihood-ratio test instead of a philosophical stance.

**Protocol:**
1. Data: all labeled decoupled steps from E1 (Cell D), features (U_T, U_A), target = judge label.
2. Fit two logistic models:
   - **Pooled:** `error ~ U_T + U_A + U_T:U_A`
   - **Typed:** same formula, fit **separately per τ stratum** (strata: I=1/W=0; I=0/W=0; I=0/W=1/R=1; I=0/W=1/R=0 — merge R strata if the R=0 cell has <100 steps and report the merge).
3. Evaluate out-of-sample: 5-fold CV **grouped by trajectory** (no trajectory spans train and test). Metrics: held-out log-loss and AUROC.
4. Test: bootstrap the pooled-vs-typed log-loss difference (trajectory-level resampling).

**Prediction:** typed dominates pooled. Secondary descriptive analysis: sign of corr(U_T, U_A) per stratum — predicted negative for I=1/W=0, no systematic relation for I=0/W=0.

**Thin-cell rule (pre-committed):** any stratum with <100 labeled steps is reported as under-powered and excluded from the headline test; this is a scoping limit, not a failure, and it motivates E2b.

**Budget:** analysis-only. ~1 day.

---

## E2b — Existence Proof for the Dangerous Quadrant

**Purpose:** ALFWorld's W=1/R=0 cell is thin; the framework's motivating example (high U_T + confident irreversible commit) needs to be shown to *exist* somewhere labeled.

**Environment (decision):** WebShop. Rationale: text-based (same agent stack), has a genuinely irreversible terminal commit (`buy now`), well-established, cheap — **and AUQ evaluated on it**, so protocol-matching buys direct comparability. τ map: `search[...]` → I=1/W=0; `click[item]`/`click[option]` → I=0/W=1/R=1; `click[buy now]` → I=0/W=1/R=0/C=costly. If WebShop integration exceeds 2 days of engineering, fall back to a τ-instrumented ToolBench slice and flag the substitution.

**Protocol (AUQ-matched):**
1. **140 episodes randomly sampled from the standard Development Set, 50-step cap** — AUQ's exact protocol (their App. A.3.1). Fix and log the sampling seed for the episode draw. Decoupled architecture + numeric elicitation only (the E1-winning probe if different). AUQ characterizes WebShop as high-observation-noise; that makes it a *harder* test of the instrument than ALFWorld — say so in the paper rather than hiding it.
2. Judge-label with the same protocol, adapted rubric for WebShop step correctness (new prompt file `judge_webshop.txt`, derived from Fig. 9 structure; include it in the repo).
3. **Deliverable is one figure + one table:** occupancy counts of the (U_T tercile × U_A tercile × τ) grid, and — the money panel — the set of steps in {high U_T, low U_A, I=0, W=1, R=0} with their labels. Show (a) the cell is occupied, (b) the instrument's uncertainty reading at those steps, (c) their error rate vs. the complement. The `buy now` steps also feed E3's analysis as the highest-stakes promise-check population.

**Falsification honesty (E4 folded in here):** if the low-U_T/high-U_A region is empty across *both* environments, report that the matrix degenerates toward a threshold in practice. Occupancy of the full matrix is a reported result either way.

**Budget:** 2–4 days including environment integration.

---

## E3 — The Propagation Claim (promise-violation as the drift signal)

**Precondition:** E1 landed. **Priority: runs immediately after E1, before E2** (timeline pressure — this is the differentiating claim; see theory doc §6.3).

**Purpose:** test the reset rule's empirical content directly.

**Definitions (frozen):**
- For every step t with τ_t.I = 1 in decoupled trajectories: **ΔU_T(t) = U_T(t+1) − U_T(t)** (elicited, winning probe from E1). Undefined at terminal steps; excluded.
- **Promise-violation indicator:** V(t) = 1 if ΔU_T(t) ≥ −ε, with ε = 0.05 (i.e., the epistemic action failed to reduce uncertainty by more than a trivial margin). Sensitivity analysis over ε ∈ {0, 0.05, 0.1}.
- **Downstream error target:** label of step t+1, and separately, "any error in steps t+1..t+3" (windowed variant).

**The four-predictor comparison (the whole experiment):**

| Predictor | Encodes |
|---|---|
| **V(t)** — promise violation | this paper's claim |
| **U_T(t)** level | "high uncertainty is the signal" (naive step reading) |
| **Level-threshold trigger 𝟙[ĉ(t) < τ_AUQ]** | **AUQ's deployed System-2 switch** (their §3.3), swept over their published ablation range τ_AUQ ∈ {0.8, 0.85, 0.9, 0.95}; report best-of-sweep to be maximally generous to the baseline |
| **Σ U_T(1..t)** and mean-U_T(1..t) | accumulation (SAUP-style trajectory reading; both variants because Σ confounds with length) |

AUROC of each against the downstream-error targets, same steps, trajectory-level bootstrap on the pairwise differences. The level-threshold baseline turns the differentiation against AUQ into a **measured head-to-head against a published mechanism**, not an asserted one.

**Prediction (pre-committed):** V(t) > U_T level ≈ level-threshold > accumulation on the step-t+1 target, at least for the I=1 subset. (Level and level-threshold should track each other — the threshold is a binarized level; if the binarized version *beats* the continuous one, that itself is worth reporting.) If U_T level wins outright, the reset rule is decoration — the paper retreats to per-step measurement only, and §2.6 of the theory doc is rewritten as motivation rather than claim.

**Descriptive companion:** distribution of ΔU_T after I=1 actions, split by whether the observation was informative (heuristic: observation is non-empty and non-error) — expect a bimodal-ish picture: resolved (ΔU_T ≪ 0) vs. failed (ΔU_T ≈ 0). This figure *is* the reset rule, visually.

**Exploratory arm — "unearned resolution" (the Delusion Gap, inverted; clearly flagged exploratory, not pre-committed):** AUQ reports that reflection inflates confidence most in failures (Delusional Confirmation). The reset rule's mirror-image prediction: a large U_T *drop* at a step whose transition delivered **no new information** (τ.I = 0, or I = 1 with an uninformative observation) is *unlicensed* — confidence rose without an observation to justify it. Define D(t) = 1 if ΔU_T(t) ≤ −δ under a non-informative transition (δ = 0.15, sensitivity over {0.1, 0.15, 0.2}); test whether D(t) predicts downstream error. If it does, promise-checking catches *both* failure modes — unresolved uncertainty **and** unearned certainty — which is the complete answer to AUQ's Delusion Gap and a figure the paper leads its discussion section with.

**Budget:** analysis-only on E1 Cell-D data (plus E2b data if available). ~1–2 days.

---

## E5 — Instrument Cost (measurement overhead)

**Purpose:** a measurement paper that hides its instrument's cost invites suspicion. Report it.

**Protocol:** from E1's two generation runs (no new compute):
1. Task success rate: entangled vs. decoupled, with trajectory-level bootstrap CI on the difference.
2. Tokens per step and per episode; wall-clock latency per step; number of model calls per step (entangled: 1; decoupled: 2 + elicitations — report with and without elicitation calls since elicitation is offline-able).
3. Episode length distribution (decoupling might change behavior, not just cost).

**Framing rule:** this is overhead accounting, not a hypothesis test. If decoupling *degrades* success significantly, that is a limitation reported in the paper's cost section — it does not gate the measurement claims, but it must be visible.

**Budget:** analysis-only. Half a day.

---

## Sequencing & Kill-Switches (authoritative)

```
E0 (judge validation)
 └─► E1 + E1b (2×2 + robustness)          ⚠️ decision point
      ├─ all cells ≈ 0.6  ──────────────► STOP. Negative-result writeup only.
      └─ any live outcome
          └─► E3 (propagation)             ← before E2, deliberately
               └─► E2 (semantics) ─► E2b (existence) ─► E5 (cost)
```

- Every experiment reads/writes the frozen schema (§0.3). No experiment mutates another's data files.
- Every table in `results/` is generated by a script in `src/analysis/`; no hand-edited numbers.
- All prompts versioned in `prompts/`; any prompt change bumps a version suffix and is logged in the run config.
- Pre-committed interpretations (E1 outcome table, E2 thin-cell rule, E3 prediction) are **not** to be edited after data exists. If reality demands reinterpretation, it is written as a deviation note, not a silent edit.

**Total budget estimate:** E0 (0.5d) + E1/E1b (~7–8d) + E3 (1–2d) + E2 (1d) + E2b (2–4d) + E5 (0.5d) ≈ **2–2.5 weeks** wall-clock, dominated by E1 generation + judging.
