# S0 SPEC — Repo/State Inventory

**2026-08-06 · Pre-registered before S0 computes · EXECUTION_HANDOVER.md §1**
**Blocks: every subsequent stage (all specs record their hash in the manifest S0 builds).**

## Purpose

S0 is the bootstrap. It produces `runs/manifest.json`, the file every later stage
reads to size itself and writes its spec hash into. S0 computes no scientific
quantity and has no decision rule; it inventories and it halts.

## Inputs

`result/pivot/` (banked scores), `reports/gate1/labels_gate1.csv` (labels),
`analysis/` (scripts), `nvidia-smi` (capacity). Read-only throughout: S0 never
writes into `result/`.

## What is recorded

**Cells.** One record per (dataset × target × assessor × scope). Two families:

- *self* — `result/pivot/<dataset>/<model>/`, assessor = target. Files:
  `probes.aggtrue.jsonl` (scope AGG-true), `probes.jsonl` (scopes SPLIT-thought /
  SPLIT-action), `judge.jsonl` (ensemble labels), `uq.jsonl` (generation).
- *cross* — `result/pivot/crossprobe/<dataset>/<target>/ptrue.<assessor>.response.jsonl`
  (scope AGG-true) and `.stages.jsonl` (SPLIT scopes). Per-worker `*.w<N>.jsonl`
  shards are recorded as provenance but never counted as cells.

Per score file: absolute path, bytes, sha256, line count. Size + sha256 are the
pin, following gate-1's `input_manifest.json` convention — later stages verify
against them and halt on drift rather than silently reading a grown file.

**Labels.** Columns present in `labels_gate1.csv`; per arm, the count of steps
carrying each A30 construct — violation (A1/A2/A3), outcome (A4 + Tier-B),
judgment (ensemble) — plus `y_env`, `y_ensemble` coverage and `in_matrix`.
Construct counts are inventory, not analysis: no rate, ratio, or comparison is
computed here.

**Scripts.** Path + sha256 for every analysis script a later stage names.

**Capacity.** `nvidia-smi` GPU inventory and free memory; package versions to
`runs/env.txt`. The ~3,300 assessments / 5 min / A100 throughput constant is
recorded as INHERITED and flagged `unverified` — §1 requires a 500-step probe
before any GPU stage sizes itself, and that probe belongs to the stage that
needs it, not to S0.

## STOP conditions (halt, write the reason into the manifest, run nothing further)

1. Label provenance columns absent from `labels_gate1.csv` — any of
   `A1 A2 A3 A4 y_tier_b y_env y_ensemble in_matrix`.
2. Any banked score file referenced by an existing gate-2 table
   (`figures/tables_gate2b1/gate2b1_cells_AGG-true_full.csv`) missing from disk.

A STOP is recorded as `status: "STOP"` with the offending list. Per ground rule 6
a STOP halts the affected branch only; S0 has no independent branches, so a STOP
here halts the program until the author resolves it.

## Outputs

`runs/manifest.json`, `runs/env.txt`, `S0_SUMMARY.md` (counts, STOP status,
what later stages may now size themselves against). Idempotent: re-running
without `--force` reuses a complete manifest and exits.

## What S0 is not

It does not recompute any banked number, does not touch `result/`, does not
decide anything, and produces no table that could enter the paper.
