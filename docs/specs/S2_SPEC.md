# S2 SPEC — CI Sweep and the Claim→Interval Registry

**2026-08-06 · Pre-registered before S2 computes · EXECUTION_HANDOVER.md §3**
**Depends on: S1 (tables_S1). Blocks: nothing — but every boundary sentence in the
rewrite pass depends on its output.**

## Purpose

Every headline number in the program that currently ships without an interval gets
one, and each is mapped to the paper sentence it supports. The deliverable is not
"more CIs"; it is a registry that makes it impossible to quote a boundary claim
without its interval sitting next to it.

## Method, fixed now

- **AUROC quantities**: DeLong where the estimator is a plain unweighted AUROC on
  independent samples; otherwise **episode-clustered bootstrap**, 2000 draws, seed 13.
  Default to the bootstrap. Steps inside an episode are not independent, and DeLong
  assumes they are — where the two disagree the bootstrap is primary and the DeLong
  value is reported beside it as a sensitivity, never the other way round.
- **Aggregate/count quantities** (proportions such as "18/22", pooled ratios, mean
  gains): cell-level percentile bootstrap, 2000 draws, seed 13, resampling CELLS.
- **Paired contrasts** (self vs external, capable vs non-capable, L1 vs L2, arm vs
  arm on the same cells): bootstrap the PAIRED difference over shared episodes or
  shared cells. An unpaired interval on a paired contrast is wrong in the
  conservative direction and would hide real effects.

## Claims covered (the §3 list, made explicit)

| id | claim | quantity | source |
|---|---|---|---|
| C-tier | capable tier beats the tier below | 8/9 contrast | S1a / banked |
| C-g2 | the indexed cut beats the verdict | P-g2 82% (18/22) | A28.1 |
| C-cap | pooled capture of the g-rule | 0.555 | A28.1 |
| C-chan | reading the value beats reading the verdict | 55/60 cells, +0.065 | b1 |
| C-tie-alf | Llama/ALFWorld upward-probing tie | +0.010 | crossprobe |
| C-tie-hot | hotpot/Qwen self-vs-70B tie | — | crossprobe |
| C-r4 | ensemble error on environment-certain steps | 9.1% / 2.0% ex-A4 | gate-1 |
| C-a30i | capable external superiority | S1c (i) | S1 |
| C-a30ii | self-inflation confined to outcome | S1c (ii) | S1 |

Any claim in the list whose source table does not exist when S2 runs is emitted with
`status=absent` rather than skipped, so the registry cannot quietly under-report.

## Decision rule (the only one S2 has)

**A claim whose 95% interval includes the null is flagged `soften`.** Null means: 0.5
for an AUROC, 0 for a difference, the registered threshold for a threshold claim
(0.80 for P-g2, 0.5 for capture). Flagged sentences are pre-committed to soften in the
rewrite pass — that commitment is made here, before the intervals are known, so it
cannot be renegotiated once they are.

S2 never changes a point estimate and never re-decides a gate.

## Output

`tables_S2/ci_registry.csv` — one row per claim: `claim_id`, `quantity`, `estimate`,
`ci_lo`, `ci_hi`, `null_value`, `method`, `n`, `source_table`, `status ∈
{ok, soften, absent, underpowered}`.
`S2_SUMMARY.md` — the registry, plus the explicit list of sentences now committed to
soften.
