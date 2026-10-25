# S7 SUMMARY — prequential replay (cost of going online)

Spec: `docs/specs/S7_SPEC.md`. Warm-up 100 steps, 10 episode orderings (seeds 13-22).

Each cell is compared against the batch g-rule **on the same construct**. S1d put that batch rule at G2b1-R3 FAIL on `violation+judgment`; S7 measures the sequential penalty relative to it and has no gate of its own.

| construct | cells | P-seq (post within 0.01) | P-warm (incl worse by >0.01) | mean post penalty | mean incl penalty |
|---|---|---|---|---|---|
| violation+judgment | 22 | 22/22 | 0/22 | -0.0002 | -0.0011 |
| judgment | 22 | 22/22 | 0/22 | +0.0007 | -0.0005 |

**P-seq**: post-warm-up balanced accuracy within 0.01 of the batch rule in a majority of capable cells.
**P-warm**: the warm-up-inclusive number is worse than batch by more than 0.01 in a majority of capable cells — the warm-up is not free.

- **violation+judgment**: P-seq HOLDS (22/22), P-warm FAILS (0/22)
- **judgment**: P-seq HOLDS (22/22), P-warm FAILS (0/22)

A sequential form that tracks a batch rule which fails its own gate is faithful to a rule that does not work; per spec §Prediction that is the honest outcome and is not a success.

