# T1 — Punchline table: judge tier × discrimination × cost

**Caption-of-record.** Six judges tested as external assessors, ranked by mean external-cell AUROC on the primary construct (violation+judgment), L2 labels, self-cells excluded, underpowered cells dropped; the frontier arm is measured on the b3 sample. The cost column is the debt-18 completion: frontier API $7.60/1k steps (measured, b3 receipt); self-hosted capable ~$0.05–0.10/1k at market A100 rates on the measured 3,300 assessments/5min/A100 (prefill + 1 token; KV-sharing basis). Volume sentence: 1M steps/day ≈ $7,600 API vs ~8.5 A100-hours self-hosted; one-clause concession — the API path suits low-volume/infrastructure-free deployments. Scope: the tested frontier model (gpt-4o) only.

- Labels: L2 · constructs: all five (f columns) · sources: `S8_CRITERIA.md` (six-judge table), `S5_SUMMARY.md` (cost receipts), `runs/manifest.json` (throughput), `FINAL_BUNDLE/WORDING_DEBTS.md` debt 18 (volume sentence)
- assembled-from: S8_CRITERIA.md + S5_SUMMARY.md + runs/manifest.json

| judge | scale | viol+jud | judgment | violation | outcome | y_env | $/1k steps | qualifies A-1 |
|---|---|---|---|---|---|---|---|---|
| Qwen3.6-35B-A3B | 35B (3B active) | **0.898** | 0.907 | 0.862 | 0.774 | 0.800 | ~$0.05–0.10 | yes |
| Llama-3.3-70B | 70B | **0.876** | 0.884 | 0.846 | 0.734 | 0.770 | ~$0.05–0.10 | yes |
| gpt-4o (frontier) | API | **0.859** | 0.861 | 0.822 | 0.711 | 0.732 | $7.60 (measured) | yes — external judging only |
| Mistral-7B-v0.3 | 7B | 0.679 | 0.682 | 0.818 | 0.759 | 0.780 | ~$0.05–0.10 | no |
| gemma-3-4b-it | 4B | 0.590 | 0.582 | 0.649 | 0.598 | 0.605 | ~$0.05–0.10 | no |
| Phi-4-mini | 3.8B | 0.546 | 0.546 | 0.748 | 0.744 | 0.751 | ~$0.05–0.10 | no |
