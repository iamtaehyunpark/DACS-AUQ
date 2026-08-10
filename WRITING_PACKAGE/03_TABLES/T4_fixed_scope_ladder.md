# T4 — Fixed-scope capability ladder (P(True)/AGG-true)

**Caption-of-record.** Self-assessment AUROC at one fixed recipe (P(True), AGG-true) across the 11 arms. A clear small vs mid/large gap exists, but ordering within tiers is irregular and dataset-dependent (gemma-4B beats Mistral-7B on HotpotQA, 0.725 vs 0.668, while sitting at chance on ALFWorld, 0.477). Reasoning capability, not parameter count, drives self-UQ; no monotonic scale law.

- Labels: L1 (L1-era analysis) · claim: C1-nointrinsic / C1-selfceiling
- source: `reports/results_report_2026-08-05.md` §2

| dataset | agent | AUROC | n |
|---|---|---|---|
| alfworld | Llama-70B | 0.839 | 4765 |
| alfworld | deepseek-v4-flash | 0.720 | 2322 |
| alfworld | Qwen-35B | 0.697 | 3197 |
| alfworld | Mistral-7B | 0.616 | 6482 |
| alfworld | gemma-3-4b | 0.477 | 6790 |
| alfworld | Phi-4-mini | 0.475 | 6604 |
| hotpotqa | Qwen-35B | 0.842 | 2192 |
| hotpotqa | Llama-70B | 0.820 | 2530 |
| hotpotqa | gemma-3-4b | 0.725 | 2565 |
| hotpotqa | Mistral-7B | 0.668 | 3224 |
| hotpotqa | Phi-4-mini | 0.550 | 2716 |
