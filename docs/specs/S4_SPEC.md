# S4 SPEC — Hindsight-Ceiling Pass

**2026-08-06 · Pre-registered before S4 computes · EXECUTION_HANDOVER.md §5**
**Authorised by STOP_GATE_DECISIONS.md D1 and the D1.2 resolution: APPROVED at the
measured 17.1 A100-hours, both judges, full matrix.**
**Truncation parameters below are fixed HERE, before any prompt is built — the
resolution requires it, and a truncation rule tuned after seeing results is not a
truncation rule.**

## Purpose

A30's keystone. Same judge, same steps, two evidence conditions: **online** (banked,
reused — no new inference) and **hindsight** (full trajectory + episode outcome).
Converts the construct taxonomy from argument into measurement.

## Scope

Judges: Llama-3.3-70B-Instruct and Qwen3.6-35B-A3B (both, per D1.2). All 11 in-matrix
arms. 38,513 steps per judge, **77,026 assessments**. Sizing constant:
`manifest.throughput_hindsight` = **375 assessments / 5 min / A100, measured**, not the
inherited 3,300 — that one was measured on online-length prompts and is 8.8× optimistic
here.

## Prompt construction

Per step: the banked online prompt (task + history + proposed reasoning/action),
then the hindsight block — every step's completion in the episode, then
`EPISODE OUTCOME: SUCCEEDED|FAILED|UNKNOWN`, then the same Yes/No question the
banked P(True) probe asks. First-token top-20 logprobs stored, so decision-framed
P(True) comes free.

## Overflow policy (D1.2 hybrid; option (c) drop is REJECTED)

Three routes, in order. Every step records `route` and `truncated`.

1. **Main pass** — served context 32,768, `max-num-seqs` 128 (Qwen: hybrid Mamba
   cache-block limit) / 64 (Llama). Steps whose assembled prompt fits go here.
2. **Long-context sub-pass** — steps over the main window are re-run on a dedicated
   server at `max-model-len` **36,864** with `max-num-seqs` **16** and
   `gpu-memory-utilization` 0.95. Reduced batch because KV cache scales with context ×
   sequences; 128 sequences at 36k does not fit in 80 GB.
3. **Fallback, only if the sub-pass is infeasible** (OOM at batch 1, or steps still
   over 36,864): **middle-out truncation**, parameters fixed now —
   - Token budget `B = 34,000` for the assembled prompt.
   - **Always kept**: the entire online prompt; the `EPISODE OUTCOME` line; the
     question.
   - Trajectory block: keep the **first 2 steps** (task framing) and then as many
     **trailing** steps as fit in `B`, dropping the middle.
   - Elision marker inserted verbatim: `... [N steps elided from the middle] ...`
   - Token counting: the served tokenizer, not a character heuristic.
   - `truncated = 1` and `n_elided = N` recorded per step.

A step that cannot be scored by any route is recorded with `route = "failed"` and
counted in coverage. It is never silently dropped — that is what option (c) was and it
was rejected.

## Outputs

`result/hindsight/<dataset>/<model>/hindsight.<judge>.jsonl` — one record per step:
`task_id`, `step_idx`, `U`, `first_token_top`, `route`, `truncated`, `n_elided`,
`prompt_tokens`.
`tables_S4/S4_coverage.csv` — per cell: steps, scored, by route, truncated count,
over-length count, failed count. **Every downstream table carries per-cell coverage
and over-length flags** (D1.2).

## Analyses (D1.3 — all constructs, L2)

1. **Hindsight − online ΔAUROC per cell** (the §8.vi figure). Episode-clustered
   bootstrap, seed 13, 2000 draws. Paired over shared episodes: same judge, same steps.
2. **Agreement with OUTCOME labels**: hindsight-judge vs online-judge. If hindsight
   closes the gap to outcome labels, the ensemble/outcome divergence is an
   information gap and is measured rather than argued — this completes A30.
3. **R3 decomposition**: per flagged cell, the share of movement attributable to
   construct vs information. Construct share is the L1→L2 movement at fixed evidence;
   information share is the online→hindsight movement at fixed labels. Reported as
   shares of the total observed movement, with the residual shown rather than absorbed.

## Pre-registered predictions

- **P-h1**: hindsight beats online on the `outcome` construct in a majority of capable
  cells, CI excluding 0. Hindsight sees the outcome the label encodes.
- **P-h2**: hindsight does **not** beat online on `violation` by more than 0.01 —
  violations are ex-ante detectable and hindsight adds nothing. If hindsight helps
  violations substantially, the violation/outcome split is less clean than A30 claims
  and that must be written down.
- **P-h3**: the information share of R3 movement exceeds the construct share on
  outcome strata and is smaller on violation strata.

## Failure policy

Ground rule 12 applies. If the online condition recomputed here disagrees with the
banked crossprobe AUROC beyond 0.001, emit `DISCREPANCY_S4.md` and halt — the online
side is banked and must reproduce.
