# S5 SUMMARY — frontier judge (gpt-4o) vs mid-tier open judges

Resolves **G2-R4**. gpt-4o via Azure, disjoint from the label ensemble (`grok-4.3` / `DeepSeek-V4-Pro` / `gpt-5.6-sol`), so **no column is marked contaminated** and all three constructs are answerable.

Sample: 1,188 steps, 11 in-matrix arms, 110/arm, stratified per A27, seed 13, frozen before the first call. 100%% top-1 Yes/No, 0 errors, ~$2.85. One framing (the banked trust wording), one scope (AGG-true) — only the model differs.

Δ = AUROC(gpt-4o) − AUROC(open judge), paired on identical steps, episode-clustered bootstrap.

## Against the CAPABLE open judges (the decisive contrast)

| construct | cells | mean Δ | gpt-4o wins | CI excludes 0 |
|---|---|---|---|---|
| violation+judgment | 22 | -0.0304 | 6/22 | 1 |
| judgment | 22 | -0.0353 | 6/22 | 1 |
| violation | 14 | -0.0334 | 6/14 | 1 |
| outcome | 20 | -0.0438 | 8/20 | 0 |
| y_env | 20 | -0.0396 | 6/20 | 2 |

## Against ALL open judges

| construct | cells | mean Δ | gpt-4o wins | CI excludes 0 |
|---|---|---|---|---|
| violation+judgment | 56 | +0.1375 | 40/56 | 29 |
| judgment | 56 | +0.1366 | 40/56 | 28 |
| violation | 35 | +0.0465 | 23/35 | 6 |
| outcome | 51 | +0.0199 | 28/51 | 4 |
| y_env | 51 | +0.0312 | 26/51 | 7 |

## G2-R4

On the primary construct, against the capable stratum: mean Δ **-0.0304** over 22 cells, gpt-4o ahead in 6, CI excluding 0 in 1. **the frontier judge does NOT clearly beat the capable open judges.**

Read with the cost column: gpt-4o cost ~$2.85 for 1,188 steps (~$2.40/1k). The open judges are self-hosted; their marginal cost is GPU time already owned.

## Tables
- `tables_S5/S5_frontier_vs_open.csv`

