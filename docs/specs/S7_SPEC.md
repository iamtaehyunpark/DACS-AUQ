# S7 SPEC — Prequential Replay of the Label-Free Cut

**2026-08-06 · Pre-registered before S7 computes · EXECUTION_HANDOVER.md §8**
**Depends on: S1 (constructs, L2 labels), S2 (registry). Free — no inference.**

## Why this exists, given S1d

A28.1's batch g-rule used the target's **full frozen score distribution** to map a
percentile to a raw cut — the honesty label attached to it from the start. S7 is the
sequential form: past-only statistics, no lookahead. The handover wrote it as a demo of
a working rule.

S1d changed what it can be. Under the A30-primary construct `violation+judgment` the
batch rule is **G2b1-R3 FAIL** (P-g2 77%, capture 0.455). A sequential variant cannot
rescue a batch rule that does not clear its bar — the sequential form is strictly harder,
since it sees less. **S7 is therefore registered as a cost-of-going-online measurement,
not as a deployment demo**, and its pre-registered prediction is restated accordingly
before any number is produced.

## Method

Per capable cell (Llama-3.3-70B, Qwen3.6-35B assessors), per construct:

1. Stream the target's episodes in a fixed order. Steps arrive in episode order;
   within an episode, in step order.
2. Maintain past-only running statistics: mean score, and the empirical quantile of
   scores seen so far.
3. **Warm-up**: until `W = 100` steps have been seen, use the prior cut from the LOTO
   pool (other targets of the same assessor × dataset) mapped through the pool's own
   distribution. After W, use the target's own past-only distribution.
4. `p̂_t` from g fitted on the other targets (identical g to A28.1 — refitted per
   construct, never refitted on the stream), applied to the past-only mean score.
   Cut at percentile `100·(1 − p̂_t)` of the past-only distribution.
5. Decide each step as it arrives; score against its L2 label. Nothing is revisited.
6. **10 episode orderings**, seeds 13..22; report mean ± sd across orderings.

## Metrics

- Balanced accuracy, **warm-up-inclusive** and **post-warm-up** (both, always — the
  warm-up-inclusive number is what a deployment actually gets).
- `p̂_t` convergence: |p̂_t − p̂_batch| as a function of t.
- Cut convergence: |cut_t − cut_batch|.
- Steps-to-convergence: first t after which |balanced accuracy_t − batch| ≤ 0.01 and
  stays so.

## Pre-registered prediction (restated for the S1d result)

Original (report_online_labelfree_rule.md §6): *within 0.01 of the batch g-rule by
≤100 steps on cross cells.*

**Registered here, before computing:** the comparison target is the batch g-rule **on
the same construct**, whatever its verdict. The prediction is about the *sequential
penalty*, not about the rule working:

- **P-seq**: post-warm-up balanced accuracy is within 0.01 of the batch g-rule on the
  same construct, in a majority of capable cells.
- **P-warm**: the warm-up-inclusive number is *worse* than the batch rule by more than
  0.01 in a majority of capable cells — i.e. the warm-up is not free.

P-seq holding while the batch rule FAILS its own gate means the sequential form is
faithful to a rule that does not work. That is the honest outcome and is written down
now so it cannot be reported as a success.

## Decision rule

S7 has **no gate**. It reports a penalty. No S7 number may be used to revisit,
soften, or overturn a G2b1 verdict (ground rule 2: no post-hoc changes to primaries).

## Output

`tables_S7/S7_prequential_{construct}.csv` — per cell, per ordering: warm-up-inclusive
and post-warm-up balanced accuracy, batch comparator, steps-to-convergence.
`tables_S7/S7_curves_{construct}.csv` — p̂_t and cut_t traces, mean over orderings.
`S7_SUMMARY.md` — P-seq / P-warm, the penalty distribution, and the explicit statement
of which construct's batch rule each cell is being compared against.
