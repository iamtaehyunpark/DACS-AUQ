# S2 SUMMARY — CI registry

Spec: `docs/specs/S2_SPEC.md`. Seed 13, 2000 bootstrap draws.

| claim | estimate | 95% CI | null | status | n |
|---|---|---|---|---|---|
| C-g2 — S-g-quantile >= V on capable cells (P-g2) | 0.8182 | [0.6364, 0.9545] | 0.80 | **soften** | 22 |
| C-cap — pooled capture ratio of the g-rule (capable) | 0.5552 | [0.0970, 0.8471] | 0.50 | **soften** | 16 |
| C-chan — mean OOS gain of value over verdict | 0.0652 | [0.0517, 0.0793] | 0.00 | **ok** | 60 |
| C-chan-frac — fraction of cells where value beats verdict | 0.9167 | [0.8500, 0.9833] | 0.50 | **ok** | 60 |
| C-a30i — capable external superiority (violation+judgment) | 0.2222 | [0.1802, 0.2724] | 0.00 | **ok** | 11 |
| C-a30ii — self-inflation larger under outcome than violation+judgment | 0.1185 | [0.0359, 0.2054] | 0.00 | **ok** | 11 |
| C-tier — capable-tier assessors beat the tier below | 0.2820 | [0.2353, 0.3293] | 0.00 | **ok** | 45 |

## Sentences committed to soften

These intervals include their null. The commitment to soften was registered in the spec before the intervals were computed.

- **C-g2** — S-g-quantile >= V on capable cells (P-g2): 0.8182, CI [0.6364, 0.9545] includes 0.80
- **C-cap** — pooled capture ratio of the g-rule (capable): 0.5552, CI [0.0970, 0.8471] includes 0.50

