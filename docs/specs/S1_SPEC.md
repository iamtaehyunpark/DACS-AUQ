# S1 SPEC — Stratified Recompute + Gate-2 L2 Pass of Record

**2026-08-06 · Pre-registered before S1 computes · EXECUTION_HANDOVER.md §2**
**Depends on: S0 (manifest OK, 61 cells). Blocks: S2, and every claim in §5/§6c/§7.**
**Labels: L2 (gate-1) is the pass of record here; L1 (ensemble) reported beside it.**

## 0. The registration this spec is forced to make

The handover names four strata — "A1/A2/A3 pooled; A4 alone; Tier-B alone; judgment
alone" — but does not say what the NEGATIVE class is in a stratum whose rules only ever
emit *incorrect*. Tier A never emits correct; in the corpus only Tier B does (6,303
steps, of which 5,183 survive the "A wins on conflict" override). Without a registered
answer the strata are not computable, so it is fixed here, before any number exists.

**Rule: a stratum varies its POSITIVE class and holds the NEGATIVE class fixed.** The
question each stratum answers is "which kinds of error can this judge detect?", not
"which kinds of correctness". Negatives come from the only source that certifies
correctness at all.

| construct / stratum | positive (y=1, incorrect) | negative (y=0, correct) |
|---|---|---|
| **violation** | A1 ∨ A2 ∨ A3 fired | `y_tier_b == 0` ∧ no violation |
| **outcome** | A4 ∨ `y_tier_b == 1` | `y_tier_b == 0` |
| **judgment** | `y_ensemble == 1` | `y_ensemble == 0` |
| **y_env** (composite, registered) | `y_env == 1` | `y_env == 0` |
| **violation+judgment** (composite, A30 §5.3 primary) | violation fired, else `y_ensemble == 1` | `y_ensemble == 0` ∧ no violation |

Consequences accepted in advance, so neither can be read as a result:

- The violation and outcome strata share a small negative pool (≤5,183 corpus-wide,
  concentrated in ALFWorld). Their cell counts will be small and their CIs wide. This is
  a property of the corpus, not a finding, and no stratum comparison may be reported as
  a difference unless the CIs separate.
- `violation+judgment` does NOT lose sample size relative to `judgment`: the composite
  substitutes violation labels only where they fire and keeps ensemble labels elsewhere.
  Any n-collapse in this construct would be a bug, not a corpus property.

**n floor: 100 labelled steps and ≥10 in the minority class per cell.** Cells below it
are computed, reported with their n, and marked `underpowered`; they are excluded from
every aggregate count and every PASS/FAIL tally. Registered now because A28.1's deciding
statistics already straddled their thresholds at full n.

## 1. Scope

61 cells from `runs/manifest.json`. Headline tables filter `in_matrix == 1` (gate-1
handover §6): the five `Qwen3.5-*` arms are inventoried but out of matrix, and
`alfworld/Qwen3.5-27B` has zero ensemble labels so it cannot carry a judgment column at
all. Scope AGG-true primary; SPLIT-thought / SPLIT-action reported where the banked
scores exist.

## 2. S1a — stratified crossprobe matrix

AUROC per (assessor × target × dataset × scope × construct/stratum), soft-weighted for
`judgment` (by `judge_frac_correct`) and hard for the environment constructs. CIs:
episode-clustered bootstrap, 2000 draws, seed 13 — clustered because steps within an
episode are not independent, which the existing crossprobe script already respects.
Output: `tables_S1/S1a_crossprobe_{labelpass}_{construct}.csv`, one row per cell, with
`n`, `n_pos`, `n_neg`, `auroc`, `ci_lo`, `ci_hi`, `underpowered`.

## 3. S1b — independence restatement (the R3 obligation)

Per arm: best-self AUROC vs best-external AUROC, Δ with episode-clustered bootstrap CI
on the *paired difference* (same episodes, so the pairing is real and a naive
independent-sample CI would be too wide). Per construct. Output
`tables_S1/S1b_independence_{labelpass}_{construct}.csv`.

## 4. S1c — A30 §4 prediction check

Reported PASS / FAIL / UNDERPOWERED per sub-claim, against the pre-registered text:

- **(i) capable external superiority intact on violation+judgment.** PASS iff, on the
  `violation+judgment` construct, the capable assessors (Llama-3.3-70B, Qwen3.6-35B)
  beat the non-capable assessors on the same target in ≥⅔ of countable external cells,
  AND the pooled Δ CI excludes 0.
- **(ii) self-probe inflation confined to outcome strata.** PASS iff the self-minus-
  external Δ is larger on `outcome` than on `violation+judgment` in ≥⅔ of arms AND the
  paired difference-of-differences CI excludes 0.

If either is UNDERPOWERED the sub-claim is reported as such and NOT counted as PASS.
A30 §6's sentence — that the claims shrink to what the tables show — governs.

## 5. S1d — gate-2 L2 reruns, per construct

Primaries unchanged from their own specs; only the label input moves.

- **b1** verdict vs value (`verdict_vs_value.py`): gain_out per cell.
- **A28** fixed-percentile transfer: V / S-LOTO-raw / S-LOTO-quantile / S-fitted,
  rules G2b-R1..R3 exactly as in `docs/GATE2B_SPEC_A28.md`.
- **A28.1** the g-rule: adds S-g-quantile / S-oracle-pct / S-mid-gap, rules G2b1-R1..R3
  exactly as in `docs/GATE2B1_SPEC_A28_1.md`, including the blocking parse-rate audit
  and the realized-flag-rate columns.

Pre-registered secondaries, labelled exploratory and never promotable (ground rule 2):
cross-only stratum (drop self cells from every pool and fit); **h-rule** — fit the
optimal percentile directly on the pool, `pct* ~ mean-U`, as an alternative to g's
error-rate indexing; tolerance table — flatness width per construct.

Output `tables_S1/S1d_{gate}_{labelpass}_{construct}.csv` plus the console log each
gate script already emits.

## 6. S1e — summary

`S1_SUMMARY.md`, one page, numbers first: every gate verdict L1 vs L2 vs per-construct
side by side; A30 §4 prediction PASS/FAIL; the underpowered-cell count per construct.
No prose evaluation beyond the registered rules (ground rule 5 — no paper text).

## 7. Failure policy

Per ground rule 12: any L2 number contradicting its banked L1 counterpart by more than
the tolerance below is not reconciled silently — `DISCREPANCY_S1.md` is emitted with
both numbers and this branch halts. **Tolerance: L1-recomputed-here vs L1-as-banked must
agree to 0.001 balanced accuracy / AUROC.** This is a reproduction check on the harness,
not on the science: the L1 pass must reproduce the banked A28/A28.1 tables exactly, since
nothing but the code path changed. L1-vs-L2 differences are the result and are never a
discrepancy.
