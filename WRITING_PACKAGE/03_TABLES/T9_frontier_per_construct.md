# T9 — b3 frontier judge (gpt-4o) per construct, including the asymmetry

**Caption-of-record.** Δ = AUROC(gpt-4o) − AUROC(open judge), paired on identical steps, episode-clustered bootstrap, trust framing (matching the banked open-judge probe verbatim; only the model differs). Against the capable stratum gpt-4o trails on every construct (−0.0209 primary); against the full open field it leads on the judgment-flavoured constructs (+0.147) and not on the environment constructs. The deficit is smallest on `judgment` (−0.026) and roughly doubles on the environment constructs (−0.064 outcome, −0.061 y_env) — pre-registered in D2.3 and confirmed (C-frontierasym).

- Labels: L2 · constructs: all five · claims: C-frontier, C-frontierasym
- source: `S5_SUMMARY.md`; per-cell CIs in `T9b_frontier_per_cell.csv` (copy of `tables_S5/S5_frontier_vs_open.csv`, 280 rows)

| comparison | construct | cells | mean Δ | gpt-4o wins | CI excludes 0 |
|---|---|---|---|---|---|
| vs capable | violation+judgment | 22 | −0.0209 | 8/22 | 4 |
| vs capable | judgment | 22 | −0.0264 | 8/22 | 3 |
| vs capable | violation | 22 | −0.0374 | 5/22 | 1 |
| vs capable | outcome | 22 | −0.0643 | 3/22 | 1 |
| vs capable | y_env | 22 | −0.0610 | 2/22 | 0 |
| vs ALL open | violation+judgment | 56 | +0.1473 | 42/56 | 38 |
| vs ALL open | judgment | 56 | +0.1469 | 42/56 | 37 |
| vs ALL open | violation | 56 | +0.0469 | 30/56 | 13 |
| vs ALL open | outcome | 56 | −0.0153 | 20/56 | 9 |
| vs ALL open | y_env | 56 | −0.0048 | 19/56 | 8 |
