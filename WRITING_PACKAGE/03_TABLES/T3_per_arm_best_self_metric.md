# T3 — Per-arm best self-assessment metric (impossibility)

**Caption-of-record.** The best intrinsic self-assessment metric and its scope for each of the 11 complete self-assessment arms. Three distinct winning metrics; P(True) best in 7/11; where P(True) wins its scope flips (SPLIT-action / AGG-mean / AGG-true). No universal recipe exists; this is Contribution 1's core table.

- Labels: L1 (3-judge ensemble; L1-era analysis, pre-gate-1) · claim: C1-nointrinsic
- source: `reports/results_report_2026-08-05.md` §1 (underlying per-metric matrix: `reports/tables/selfassess_auroc.csv`)

| dataset | agent | best | scope | AUROC |
|---|---|---|---|---|
| alfworld | Llama-70B | ptrue | SPLIT-action | 0.883 |
| alfworld | deepseek-v4-flash | SP | SPLIT-thought | 0.799 |
| alfworld | Qwen-35B | ptrue | AGG-mean | 0.708 |
| alfworld | Mistral-7B | chat_ingen | AGG-true | 0.657 |
| alfworld | gemma-3-4b | ptrue | SPLIT-action | 0.642 |
| alfworld | Phi-4-mini | chat_ingen | AGG-true | 0.622 |
| hotpotqa | Qwen-35B | ptrue | AGG-true | 0.842 |
| hotpotqa | Llama-70B | ptrue | AGG-true | 0.820 |
| hotpotqa | gemma-3-4b | ptrue | AGG-true | 0.725 |
| hotpotqa | Mistral-7B | ptrue | SPLIT-action | 0.723 |
| hotpotqa | Phi-4-mini | SP | SPLIT-thought | 0.622 |
