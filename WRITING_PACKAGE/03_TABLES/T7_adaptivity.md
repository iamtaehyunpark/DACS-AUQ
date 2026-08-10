# T7 — Adaptivity: the verdict tracks difficulty and still mis-places

**Caption-of-record.** Verdict behavior per judge (AGG-true). Capable judges' implicit threshold tracks target difficulty almost perfectly (r ≈ 0.97) yet placement is biased per judge: Llama under-flags low-error regimes (worst cell flags 7% at a 15% error rate, bal_acc 0.614); Qwen over-flags everywhere (+0.121). Weak judges' verdicts collapse to majority-class or below in 9–11/11 cells while their scores remain recoverable (+0.02…+0.11 via a cut). Adaptation is not optimization; a bit cannot be re-thresholded, a score can.

- Labels: L1 · claim: C-adaptivity · source: `reports/report_gate2_score_vs_verdict.md` §2

| judge | corr(flag rate, error rate) | mean(flag − error rate) | verdict mean bal_acc | cells ≤ majority-class |
|---|---|---|---|---|
| Llama-3.3-70B | +0.978 | −0.013 | 0.723 | 0/11 |
| Qwen3.6-35B | +0.956 | +0.121 | 0.734 | 2/11 |
| Mistral-7B | +0.834 | −0.489 | 0.503 | 11/11 |
| Phi-4-mini | +0.706 | −0.321 | 0.507 | 9/11 |
| gemma-3-4b | +0.690 | −0.332 | 0.483 | 10/11 |
