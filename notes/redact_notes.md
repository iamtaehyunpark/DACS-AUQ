# ReDAct — Paper Notes (source of E0/E1 anchor)

**ReDAct: Uncertainty-Aware Deferral for LLM Agents** — arXiv:2604.07036v1 (8 Apr 2026), MBZUAI et al.
PDF: `/Users/t/Documents/SCLAB/dacs/ReDAct.pdf`. Extracted text: scratchpad `redact.txt` (28pp).

## One-line thesis
Equip an agent with a **small** model (default) + **large** model (expensive). Compute UQ at the
**action-selection stage**; if uncertainty > calibrated threshold τ, **defer that action to the large model**.
Deferring ~15% of steps matches full large-model performance at a fraction of cost.

## Architecture — CRITICAL for our theory doc §2.3
ReDAct's "ReAct" is **already a two-call decoupled loop**, not single-call:
1. **Reasoning call** (`prompts/redact_reasoning.txt`, Fig 5): DESCRIPTION + HISTORY + AVAILABLE COMMANDS → free-form thought.
2. **Action call** (`prompts/redact_action.txt`, Fig 6): fresh prompt with `YOUR CURRENT REASONING: {THOUGHTS}` + AVAILABLE COMMANDS + strict "output exactly ONE line = one available command."

→ This is the **stage-specific contract** our theory §2.3 concedes "the architecture ground is more occupied
than it first appears." Their action call is the same distinct-contract idea as our decoupled-action prompt.
Uncertainty (SP/PPL/MTE) is computed on the **action-selection generation**, after reasoning is done.

## The manufactured step labels (this is the labeling escape in theory §4)
- **100 trajectories** simulated with ReAct + **Qwen3-80B** (small) on ALFWorld → **2411 steps total**.
- Each step labeled by **GPT-5.2 as LLM-as-judge** (Fig 9 prompt, `prompts/judge_redact_fig9.txt`).
- Result: **1555 correct / 856 incorrect** (~64.5% correct).
- Judge processes the **WHOLE trajectory in one call**, returns JSON `{"step i": {"label":0|1,"reason":...}}`.
  label **1 = good/helpful**, **0 = bad** (loop/wander/irrelevant). Our AUROC positive class = `incorrect` = label 0.
- Judge criterion is admittedly **plausibility / helpful-exploration**, not ground-truth correctness (theory §5.5).

## ANCHOR NUMBERS (Table 1, p.5) — E1 Cell A MUST land near these
Qwen3-80B, ALFWorld, 2411 labeled steps. ROC-AUC and PRR (PRR computed up to 50% rejection):

| UQ metric | Action PRR | Action ROC-AUC | Reasoning PRR | Reasoning ROC-AUC |
|---|---|---|---|---|
| Mean Token Entropy (MTE) | 0.424 | **0.710** | 0.168 | **0.596** |
| Perplexity (PPL)         | 0.399 | **0.684** | 0.193 | **0.616** |
| Sequence Probability (SP)| 0.417 | **0.704** | 0.279 | **0.682** |

- **Reasoning-level band 0.596–0.682** = the spec's E1 anchor check (Cell A MTE/PPL/SP must land within ±0.05).
- Action-level band 0.684–0.710. ReDAct's conclusion: reasoning-level UQ has **poor** discriminative power →
  they use action-level only. (Our claim: entropy is the wrong probe, not that thought UQ is uninformative.)
- Full action-level table (Table 6, p.16) also has 12 sample-diversity methods (Semantic Entropy 0.665, etc.);
  MTE/SP/PPL are the top 3. ReDAct **did NOT test verbalized/elicited confidence** — that gap is our opening.

## UQ formulas (Appendix A, p.15) — implement to match verbatim
For sequence y=[y1..yL], token probs p(y_i | x, y_<i, θ):
- **SP** (Sequence Probability):  U_SP  = − Σ_i log p(y_i | ...)      (i.e. total negative log-likelihood)
- **PPL** (Perplexity):           U_PPL = − (1/L) Σ_i log p(y_i | ...) (mean NLL; note: NOT exp(); their "PPL" is mean NLL)
- **MTE** (Mean Token Entropy):    U_MTE = (1/L) Σ_i H(y_i | ...), H = entropy of the token distribution
- Higher score = more uncertain. Implemented via **LM-Polygraph** library (Fadeeva et al. 2023).
- MTE needs the full per-token entropy → requires `logprobs` over the distribution (spec requests logprobs=20).

## PRR (Prediction Rejection Ratio, Appendix C, p.16)
PRR = (AUC_unc − AUC_rnd) / (AUC_oracle − AUC_rnd), computed **only up to 50% rejection**.
Higher = better ordering. This is the metric for direct Table-1 comparability (our metrics §0.7).

## ALFWorld protocol (Appendix B.1)
- `AlfredTWEnv`, all 6 task types: Pick & Place, Examine in Light, Clean & Place, Heat & Place, Cool & Place, Pick Two & Place.
- Calibration subset: **100 episodes randomly sampled from `valid seen` split**.
- Main eval: **400 episodes**, **50-step cap** (our spec uses AUQ's 140-seen instead — see discrepancies).
- Deferral threshold calibrated on N_cal=100 episodes, target K=5 large-model calls/episode.

## Models
- Small: `Qwen/Qwen3-Next-80B-A3B-Instruct` (this is the spec's "Qwen3-80B"), Llama3.3-70B, Llama4-Maverick.
- Large: GPT-5.2, `Qwen/Qwen3-235B-A22B-Instruct-2507`, `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8`.
- Served via **Together AI** (except GPT-5.2). Only models >70B (smaller ones fail agentic tasks w/o finetuning).
- ALFWorld base success rates: Qwen3-80B **0.683**, Llama3.3-70B 0.635, GPT-5.2 0.783, Qwen3-480B 0.793.

## What we take / what differs from our plan
- TAKE: two-call split w/ contracts (Cell C/D architecture), Fig 9 judge, SP/PPL/MTE defs, PRR, reasoning-AUROC anchor.
- DIFFERS: they cap 400 episodes (we use AUQ's 140 seen); their judge = whole-trajectory JSON (adopt as-is);
  their point is deferral/cost, ours is measurement. Their negative reasoning-UQ result is the foil we reinterpret.
