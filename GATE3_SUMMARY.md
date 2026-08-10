# GATE-3 SUMMARY (A33) — final label-free attempt

Spec: `GATE3_SPEC_A33.md`. Primary construct **violation+judgment**, capable stratum, seed 13, 2000 draws.

## Arm 0 — h-rule (spec §2)

The direct percentile map was pre-registered as an S1 secondary and **was not computed there** (S1d ran b1/A28/A28.1 only). It is computed here as the S1 spec defined it.

## Verdicts, primary construct, capable stratum

| arm | pass-rate | 95% CI | pooled capture | 95% CI | abstain | verdict |
|---|---|---|---|---|---|---|
| arm 0 — h-rule (pct* ~ mean-U) | 20/22 (91%) | [0.77, 1.00] | 0.940 | [0.80, 1.04] | 0 | **PASS** |
| arm 1 — mixture cut | 8/22 (36%) | [0.18, 0.55] | -0.180 | [-0.98, 0.43] | 4 | **FAIL** |
| arm 2 — violation-calibrated | 19/22 (86%) | [0.73, 1.00] | 0.969 | [0.88, 1.03] | 0 | **PASS** |

Bars are A28.1's, unchanged: PASS needs ≥80% of countable cells at or above V **and** pooled capture ≥0.5. Abstentions count as losses (spec §3.4).

## Robustness across constructs (spec §1 — primary decides)

| construct | h-rule | mixture | violation-calibrated |
|---|---|---|---|
| violation+judgment ←primary | PASS 20/22, cap 0.94 | FAIL 8/22, cap -0.18 | PASS 19/22, cap 0.97 |
| judgment | PASS 19/22, cap 0.95 | FAIL 9/22, cap -0.08 | PASS 18/22, cap 0.97 |
| violation | FAIL 16/22, cap 0.84 | FAIL 7/22, cap 0.08 | FAIL 17/22, cap 0.94 |
| outcome | PASS 18/22, cap 0.96 | FAIL 9/22, cap 0.09 | FAIL 14/22, cap 0.33 |
| y_env | PASS 20/22, cap 1.00 | FAIL 8/22, cap 0.16 | FAIL 13/22, cap 0.36 |

## Per-cell detail, primary construct, capable stratum

| dataset | assessor | target | n | V | h-rule | mixture | viol-cal | fitted |
|---|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | 4285 | 0.777 | 0.780 | 0.766 | 0.782 | 0.779 |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | 6203 | 0.754 | 0.787 | 0.772 | 0.787 | 0.782 |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | 6005 | 0.697 | 0.766 | 0.766 | 0.758 | 0.766 |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | 2872 | 0.641 | 0.687 | 0.686 | 0.693 | 0.701 |
| alfworld | Llama-3.3-70B-Instruct | deepseek-v4-flash | 3067 | 0.725 | 0.749 | 0.745 | 0.756 | 0.752 |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | 6507 | 0.728 | 0.799 | 0.807 | 0.803 | 0.798 |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | 4285 | 0.759 | 0.792 | ABSTAIN(no_boundary_between_means) | 0.834 | 0.835 |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | 6203 | 0.715 | 0.804 | ABSTAIN(no_boundary_between_means) | 0.803 | 0.798 |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | 6005 | 0.667 | 0.787 | 0.593 | 0.791 | 0.787 |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | 2872 | 0.614 | 0.608 | ABSTAIN(no_boundary_between_means) | 0.645 | 0.649 |
| alfworld | Qwen3.6-35B-A3B | deepseek-v4-flash | 3067 | 0.792 | 0.755 | ABSTAIN(no_boundary_between_means) | 0.801 | 0.763 |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | 6507 | 0.713 | 0.821 | 0.590 | 0.822 | 0.824 |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | 1878 | 0.745 | 0.822 | 0.822 | 0.805 | 0.822 |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | 2626 | 0.826 | 0.829 | 0.773 | 0.817 | 0.830 |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | 2282 | 0.859 | 0.860 | 0.800 | 0.862 | 0.856 |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | 1787 | 0.667 | 0.822 | 0.776 | 0.811 | 0.812 |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | 2248 | 0.864 | 0.865 | 0.853 | 0.856 | 0.863 |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | 1878 | 0.810 | 0.814 | 0.664 | 0.812 | 0.811 |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | 2626 | 0.768 | 0.828 | 0.818 | 0.833 | 0.827 |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | 2282 | 0.832 | 0.872 | 0.654 | 0.872 | 0.868 |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | 1787 | 0.808 | 0.847 | 0.682 | 0.806 | 0.835 |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | 2248 | 0.852 | 0.876 | 0.698 | 0.876 | 0.872 |

## Mechanism

Spec §0 diagnosed the A28.1 failure as the indexing identity: the optimal flag-rate is not the error rate. The g-rule predicted the error rate and cut at 1−p̂; the h-rule predicts the optimal **percentile** directly and never forms the identity. On the same cells under the same bars, pooled capture moves 0.455 → 0.940.

Arm 1 was the arm registered to *escape* the percentile family altogether, and it is the one that failed — 4 abstentions on degenerate EM, each counted as a loss per spec §3.4. Bimodality is present in the scores but its component boundary is not where the decision boundary belongs, which is the same result S7 reached from the gap side.

Arm 2 is **not label-free**. Per spec §4 its claim wording is "human-annotation-free, environment-self-calibrating": it fits on violation labels the environment emits automatically in any deployment log. Its risk was pre-registered — violation steps are gross failures, so the cut may sit wrong for subtle errors.

## Closure clause (spec §6)

**NOT INVOKED** — an arm reached PASS on the primary construct. §6d recovers a deployment story with this gate as its provenance; the A28 and A28.1 verdicts remain beside it in the record.

Sentence §6d leads with: *a label-free operating point transfers across targets when it is placed by the arm above, at the capture and pass-rate recorded here.*

## Per-construct tables

- `tables_gate3/gate3_cells_violation-judgment.csv` (55 cells)
- `tables_gate3/gate3_cells_judgment.csv` (55 cells)
- `tables_gate3/gate3_cells_violation.csv` (55 cells)
- `tables_gate3/gate3_cells_outcome.csv` (55 cells)
- `tables_gate3/gate3_cells_y_env.csv` (55 cells)

