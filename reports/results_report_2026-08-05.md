# Results Report — Judge-Based Agent-Step UQ
**2026-08-05 · Basis: selfassess_auroc.csv, crossprobe_matrix.csv, evidence-grid ablation (Qwen3.6-35B, n≈300/condition, 95% CI) · Maps to proposal v3 (2026-08-03)**

---

## 1. No universal intrinsic metric (v3 §2, Contribution 1)

Per-arm best self-assessment metric:

| ALFWorld | best | scope | AUROC | | HotpotQA | best | scope | AUROC |
|---|---|---|---|---|---|---|---|---|
| Llama-70B | ptrue | SPLIT-action | 0.883 | | Qwen-35B | ptrue | AGG-true | 0.842 |
| deepseek-v4-flash | SP | SPLIT-thought | 0.799 | | Llama-70B | ptrue | AGG-true | 0.820 |
| Qwen-35B | ptrue | AGG-mean | 0.708 | | gemma-3-4b | ptrue | AGG-true | 0.725 |
| Mistral-7B | chat_ingen | AGG-true | 0.657 | | Mistral-7B | ptrue | SPLIT-action | 0.723 |
| gemma-3-4b | ptrue | SPLIT-action | 0.642 | | Phi-4-mini | SP | SPLIT-thought | 0.622 |
| Phi-4-mini | chat_ingen | AGG-true | 0.622 | | | | | |

Findings.
1. No common winner: three distinct best metrics across 11 arms; even where P(True) wins, its winning scope flips (SPLIT-action / AGG-mean / AGG-true).
2. P(True) is the dominant tendency — best in 7/11 arms — but not universal; two of its losses (deepseek/alf to SP, Phi/hotpot to SP by 0.006) and two wins by in-generation verbalized confidence (Mistral/alf, Phi/alf) block any "always use X" recipe.
3. Consequence for v3 wording: "verbalized in-generation confidence worst everywhere" must become capability-conditional (it is the *best* self-metric for both sub-7B ALFWorld arms, while sitting at 0.25–0.40 for Llama/Qwen); "P(True) best or tied 7/8" recounts to 7/11 on the expanded arm set.

## 2. Capability tiers, not scale monotonicity (v3 §2 floor, §7(i) size curve)

Fixed-scope P(True)/AGG-true:

| ALFWorld | AUROC | n | | HotpotQA | AUROC | n |
|---|---|---|---|---|---|---|
| Llama-70B | 0.839 | 4765 | | Qwen-35B | 0.842 | 2192 |
| deepseek-v4-flash | 0.720 | 2322 | | Llama-70B | 0.820 | 2530 |
| Qwen-35B | 0.697 | 3197 | | gemma-3-4b | 0.725 | 2565 |
| Mistral-7B | 0.616 | 6482 | | Mistral-7B | 0.668 | 3224 |
| gemma-3-4b | 0.477 | 6790 | | Phi-4-mini | 0.550 | 2716 |
| Phi-4-mini | 0.475 | 6604 | | | | |

Findings.
1. A clear small vs mid/large gap exists, but ordering *within* tiers is irregular and dataset-dependent: gemma-4B outscores Mistral-7B on HotpotQA (0.725 vs 0.668) while sitting at chance on ALFWorld (0.477). Reasoning capability, not parameter count, drives self-UQ.
2. This supports the hedged v3 framing (size curve tests *whether* a knee exists) and rules out any monotonic scale law; the earlier "0.53–0.64 sub-7B floor" band is broken (gemma/hotpot self-best 0.725) — the floor claim survives only in relative form (§3).

## 3. Independence: external judge beats self-assessment (v3 §5, Contribution 2)

Qwen-35B judge on frozen 4B-class trajectories vs those agents' best self-metric, 4/4 arms:

| Arm | self-best | Qwen judge | Δ |
|---|---|---|---|
| gemma / ALFWorld | 0.642 | 0.909 | +0.267 |
| Phi / ALFWorld | 0.622 | 0.815 | +0.193 |
| gemma / HotpotQA | 0.725 | 0.927 | +0.202 |
| Phi / HotpotQA | 0.622 | 0.922 | +0.300 |

Findings.
1. Go/no-go passed with margin: gains +0.19 to +0.30, external readings reach 0.815–0.927. Small agents are not unreadable; they are bad self-readers (v3 §5 numbers to be updated from "+0.02 to +0.28 / 0.82–0.91").
2. Capable judges also lift mid-tier and peer targets (Mistral/alf 0.657→0.868 under Llama-70B; Qwen/alf 0.708→0.823 under Llama-70B; deepseek/alf 0.760→0.864).
3. **Judge-recipe stability** — the intrinsic-metric instability of §1 disappears under an external judge: Qwen-as-judge's best scope is SPLIT-action in 8/9 cross arms (one marginal AGG-mean), with the same pattern for Llama-as-judge. Characterize the judge once, apply across targets: this is the thesis's direct empirical warrant and should be reported alongside §1 as its resolution.
4. Boundary: upward probing has a ceiling. Qwen/hotpot self (0.842) beats the Llama-70B judge (0.816); Llama/alf self (0.883) vs Qwen judge (0.893) is +0.010, likely within noise. The independence claim holds downward and peer-level; it is not universal at the top of the capability range (feeds v3 §10(b)).

## 4. Evidence grid: what the judge reads (v3 §6a, Contribution 3)

Qwen3.6-35B judge, paired conditions, AUROC [95% CI]:

| Condition | Contents | ΔU (inc−cor) | AUROC [CI] |
|---|---|---|---|
| C0/R0 | task + action | 0.011 | 0.512 [0.438, 0.586] |
| C1/R0 | + last observation | 0.150 | 0.622 [0.555, 0.685] |
| C2/R0 | + full history | 0.242 | 0.697 [0.637, 0.755] |
| C3/R0 (base) | + reasoning | 0.248 | 0.741 [0.675, 0.801] |
| C4/R0 | C3 − action | 0.229 | 0.740 [0.673, 0.798] |
| C5/R0 | C3 + realized observation | 0.396 | 0.813 [0.756, 0.865] |
| C6/R0 | C5 + next thought/action | 0.299 | 0.845 [0.799, 0.888] |
| C3/R1 | + generic rubric | 0.325 | 0.804 [0.746, 0.853] |
| C3/R2 | + targeted rule | 0.366 | 0.813 [0.753, 0.866] |
| C3/R3 | + decoy rule | 0.242 | 0.728 [0.661, 0.789] |
| C0/R2 | rule without history | 0.026 | 0.531 [0.455, 0.603] |

Findings.
1. An action string alone is chance (0.512) — step quality is relational to state; the QA judging problem does not port (v3 §4.1 receipt confirmed with CI).
2. History is the signal carrier (0.512→0.697); a rule without history is inert (C0/R2 = 0.531).
3. Realized evidence is the largest single increment: +0.072 over base (0.741→0.813), rising to 0.845 with one-step lookahead — the gradient toward the §7(vi) hindsight ceiling, and the basis for post-observation assessment of reversible steps in the τ policy.
4. Targeted rules reproduce the realized-evidence gain pre-execution: R2 = +0.072 over base and +0.085 over the decoy floor (R3 ≈ base). This is the rule-recoverable fraction of the cost of irreversibility, per protocol design.
5. Precision on dispensability: given history + reasoning, the action token adds nothing (C4 0.740 ≈ C3 0.741); removing reasoning costs −0.044 (C2 0.697), CIs overlapping. Black-box operation (no reasoning access) is viable at a small, currently non-significant penalty — state it as such, not as "reasoning is dispensable" flatly.

## 5. Status and open items

1. **Amendments required (candidate A20):** revise v3 §2 wording per §1.3 and §2.2 above; update §5 numbers per §3.1; scope the independence claim per §3.4.
2. **CIs exist only for the evidence grid.** Items decided by ≤0.010 gaps (P(True)-vs-SP counts, top-tier upward probing) stay open until DeLong/bootstrap CIs land on the full matrices.
3. **Hygiene:** chat_ingen and AGG-true coverage varies (down to 41% for gemma arms; deepseek AGG-true n=2322/3304) — report per-cell coverage; deepseek is ALFWorld-only, so either complete or scope it as a partial arm; sub-0.5 AUROCs (sep_verbalized/posthoc_num at 0.19–0.40 on capable models) are inverted signal — a pre-registered no-post-hoc-flip orientation stance must appear in the paper.
4. **Still unrun from §7:** full prober×agent matrix under the judge protocol, loop stratification, τ-gating budget curves, hindsight-ceiling pass, adjudication pass.
5. **External dependency:** typed-aggregation appendix scope (in-department) blocks the τ freeze; coordination with Changdae Oh remains open and deadline-critical.
