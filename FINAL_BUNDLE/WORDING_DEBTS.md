# WORDING_DEBTS — checklist for the rewrite pass

**2026-08-10 · one line per debt, with its source amendment · the author's writing pass
should be able to work this list without reconstructing anything from memory**

| # | debt | source |
|---|---|---|
| 1 | Thesis scoped **"per environment family, across agents"** in §3 — not "across environments". | Part D no-claim; A34 scope condition 2 |
| 2 | Mechanism section = **flatness + coarse affine regularity**, with conditional invariance stated as **sufficient-not-necessary** and the Part B split verdict given (holds hotpotqa, fails alfworld). | GATE-4 Part B |
| 3 | Cite **label-shift / BBSE** literature where the percentile-indexing family is introduced. | REMAINING_WORK v2 §3 |
| 4 | State the **A28 → A28.1 → A33 arc with the attempt count plainly** — three label-free attempts, the third passed within-gate and then failed forecast validation. | GATE-3 §0, GATE-4 closure |
| 5 | **A32 limitation verbatim**: judgment labels are a human proxy, validated at ~2% error on the environment-certain band, **untested on the contested band**, pending the deferred spot check. | A32 / D4 |
| 6 | **Bootstrap ladder → "label-source menu"** as the §6d spine, presenting **two validated routes**: day-one violation-calibrated (0.801 primary, with its **outcome-construct collapse to 0.672** shown) and the **~200-label tier as the lead** (0.808). **h is referenced beneath the menu as the attempted third route — within-gate validation only, forecast miss disclosed — not as a peer route.** | P3 ladder; GATE-4 closure; resolves the conflict with debt 10 |
| 7 | **Pools exclude self-cells** stated in the recipe, not only in the appendix. | A34 scope condition 1; Part C leverage finding |
| 8 | **Cross-environment anomaly** in one sentence; family granularity in limitations. Part D carries no success criterion and its CI includes 0. | Part D |
| 9 | **Soften the two S2-flagged sentences** (A28.1 P-g2 and capture): both point estimates sit below their bars with CIs spanning them. | S2 registry; item 4 |
| 10 | §6d **leads with the ~200-label calibrated tier**; h appears scoped to within-gate validation with the forecast miss as its boundary. | GATE-4 closure (binding) |
| 11 | **h-noself disclosure**: both GATE-4 sealed variants excluded self-cells because the cross-probe pipeline skips the diagonal; the h-with-self forecast was never sealed. | GATE-4 summary, seal defect |
| 12 | **b3 deviations**: the first 1,188 calls ran without the D2.2 acknowledgement, and the frozen-sample guarantee did not hold (sample file regenerated per run) — analysed steps are enumerated instead. | S5 summary |
| 13 | **S4 postmortem paragraph**: 69,940 records void from appending a prompt after a closed chat template; detected by top-1 token distribution; tripwire adopted as A35. | A35 |
| 14 | **Floors are a NEW registration**; R1's FAIL stands. Discrimination confers external-judging eligibility only; label-free additionally requires the stability condition, which rests on n=2 with validation open. | S8 signature |
| 15 | **gpt-4o qualifies for external judging but not label-free** — no (b) audit exists for it. | S8 signature |
| 16 | **Name the label-ensemble trio verbatim in the validity section** — `grok-4.3`, `DeepSeek-V4-Pro`, `gpt-5.6-sol` — and state that gpt-4o is disjoint from all three. That disjointness is what legalizes every judgment-column comparison in the b3 arm; without the names a reader cannot check it. | S5 / D2.1(b) |
| 17 | **Frontier construct-asymmetry paragraph**: the frontier deficit is smallest on `judgment` (−0.026) and roughly doubles on the environment constructs (−0.064 outcome, −0.061 y_env). Pre-registered in D2.3 and confirmed; read as same-species affinity between LLM judges and LLM-derived labels. | S5; D2.3 |
| 18 | **Complete the punchline table's cost column**: accuracy × $/1k steps per judge tier — frontier API $7.60/1k (measured, b3), self-hosted capable ~$0.05–0.10/1k at market A100 rates (measured throughput), with one volume sentence (1M steps/day ≈ $7,600 API vs ~8.5 A100-hours) and the prefill+1-token/KV-sharing basis stated. Scope to the tested frontier model; include the one-clause API-path concession for low-volume/infrastructure-free deployments. | S5 receipt; §4.4 cost property |
