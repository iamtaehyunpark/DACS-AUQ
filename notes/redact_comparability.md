# Comparability report: our setup vs. ReDAct (anchor validity check)

Date: 2026-07-20 · Written while E0 Step 4 runs under `96102fc` (schema 1.5.0).
Question: can our numbers be compared against ReDAct's Table 1 (reasoning-AUROC
0.596–0.682, action-AUROC 0.684–0.710), and did our amendments drift us away?

## 1. Side-by-side

| Dimension | ReDAct (arXiv:2604.07036) | Ours (96102fc) | Comparable? |
|---|---|---|---|
| Env / split | ALFWorld `valid_seen`, AlfredTWEnv, admissible commands exposed | same | ✅ exact |
| Step cap | 50 | 50 | ✅ exact |
| Labeled set | 100 trajs → 2,411 steps | 140 tasks (E1), 30 (E0) | ✅ same regime |
| Agent model | **Qwen3-Next-80B-A3B-Instruct** (MoE, 3B active) | Qwen3.6-35B-A3B (MoE, 3B active) | ⚠️ same class, smaller |
| Serving | Together AI API | local vLLM, raw completions | ⚠️ see §3 |
| Sampling | API; temp/top_p **not reported** | temp 0.7, top_p 0.95, per-step seeds | ⚠️ unverifiable |
| Architecture | **two-call decoupled** (Fig 5 reasoning → Fig 6 action) | our decoupled arm = their prompts **verbatim** | ✅ (Cells C/D) |
| Thought in history | **No** (reasoning regenerated per step) | decoupled arm: no; entangled arm: yes (AUQ's design) | ✅ / n.a. |
| Confidence tag in prompts | none | v2 adds it; **v1 arm = tag-free = their exact prompts** (E1b) | ✅ via v1 arm |
| UQ formulas | SP = total NLL, PPL = mean NLL, MTE = mean token entropy (LM-Polygraph) | implemented verbatim | ✅ |
| MTE distribution depth | LM-Polygraph over API logprobs (top-k limited) | top-20 logprobs | ⚠️ both truncate; depth unknown |
| Judge | GPT-5.2, Fig-9 whole-trajectory JSON, label 0 = bad | same prompt; local Llama-70B + GPT-5.2 pass (E0 measures their agreement) | ✅ |
| Positive class | label 0 (incorrect) | same | ✅ |
| Base success | Qwen3-80B: 0.683 | first E0 run: 0.80 (30 tasks) | ✅ ballpark |

## 2. The spec inconsistency this exposed — anchor cell is mis-pointed

ReDAct's loop is **decoupled**. Their reasoning-AUROC band was measured on
reasoning generated *without prior thoughts in context*. Our spec anchors **Cell A
(entangled + entropy)** against that band — a cross-architecture comparison that
contradicts our own thesis: we *predict* entanglement changes entropy readings
(smoke evidence: thought-MTE inverted, 0.070 on incorrect vs 0.407 on correct).

**Correction (pre-data, recommended):** the replication anchor is **Cell C**
(decoupled + entropy), and the *strict* replication configuration is the **E1b v1
arm** (tag-free prompts — byte-identical to ReDAct's). Expect Cell C in-band
= pipeline valid. Cell A relative to the band is then a *result* (the entanglement
effect), not a sanity check. If Cell A happens to land in-band too, that is
informative, not required.

## 3. "ReDAct used an API, so no loops" — the record says otherwise

Two pieces of evidence that ReDAct's data **contained loops**:
1. Their own judge rubric defines label 0 as "bad (**loop**/wander/irrelevant)" —
   you don't put looping in the rubric unless it shows up in the data.
2. 856/2,411 steps incorrect (35.5%) with base success 0.683 and a 50-step cap —
   ~⅓ of episodes failing, the classic ALFWorld wander/loop signature; their mean
   24.1 steps/trajectory is consistent with a cap-hitting tail.

What the API changed is not *whether* loops occur but *how they sample*: API calls
draw fresh randomness each step, so their loops drift and fork rather than lock
byte-exact. Our original per-episode seeds were the deviation from that regime;
the **per-step-seed amendment (4bd6a08) moved us toward ReDAct's sampling
behavior, not away from it** — same fresh-draw-per-step statistics, but
reproducible.

The deeper structural difference: their decoupled reasoning is **never
copy-conditioned on its own prior text** (thoughts absent from history), so their
reasoning entropy lacks the self-copy collapse channel entirely. Repeated
action/observation lines in their history provide only a weak echo of it. That is
precisely the Cell A vs Cell C contrast — and a candidate mechanistic explanation
for why their reasoning-UQ looked merely *weak* (0.596) rather than *inverted*:
their architecture couldn't produce the full collapse.

## 4. Deviations that remain, honestly classified

- **Harmless / convergent:** per-step seeds (≈ API fresh sampling, reproducible);
  local vLLM vs Together (same model weights class, logprobs available); the
  `<think>` prefill and degenerate-retry live only in the **entangled** arm — the
  ReDAct-comparable decoupled path is untouched by them.
- **Bounded by design:** the v2 confidence-tag instruction may perturb decoupled
  thoughts; the pre-registered E1b v1-vs-v2 ablation measures that bound, and the
  v1 arm gives an exact-prompt replication point.
- **Real caveats to state in the paper:** agent is 35B-A3B not 80B-A3B (same MoE
  class; contingent Cell-C/v1 run on the 80B remains the clean upgrade path if
  weights become cacheable); their sampling temperature and logprob depth are
  unreported, so exact-number replication was never possible for anyone —
  only band-level comparison, which is what the ±0.05 tolerance encodes.

## 5. Verdict

Comparable **where it matters and by construction**: our decoupled arm runs
ReDAct's prompts verbatim, their metrics verbatim, their judge prompt verbatim,
their env protocol exactly. The anchor comparison is valid for **Cell C (strictest:
E1b v1 arm)** and should be re-pointed there in the spec — comparing their band to
our entangled Cell A is not replication but the experiment's own hypothesis, and
conflating the two would let a true finding read as a failed sanity check.
