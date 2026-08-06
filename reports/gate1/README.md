# Gate 1 — environment-anchored relabelling and recomputation

Every current result in this repository is scored against a 3-judge LLM ensemble, which
makes judge evaluation circular. Gate 1 rebuilds the step labels from environment
evidence and reports both scorings side by side.

**No model inference, no trajectory regeneration, no GPU.** Everything here is log
scanning, deterministic ALFWorld replay on CPU, and reruns of the existing analysis
scripts with the label input swapped.

## Deliverables

| file | what it is |
|---|---|
| `labels_gate1.parquet` / `.csv` | **the file of record** — one row per (run_id, task_id, step_idx) with `y_env`, `y_suffix`, `y_ensemble`, sub-rule provenance and coverage flags |
| `report_phase0_inventory.md` | field audit, skip-reason taxonomy, Tier-A coverage, the HotpotQA STOP finding |
| `report_phase2_ensemble_audit.md` | ensemble label error on steps the environment had already settled |
| `tables_gate1/` | Phase-5 side-by-side tables, ensemble label vs environment label |
| `GATE1_SUMMARY.md` | R1–R4, each with PASS/FAIL/FLAG and the number that decided it |

Supporting artifacts: `input_manifest.json` (every raw input pinned by size + sha256),
`tier_a_steps.csv`, `tier_b_alfworld.csv`, `tier_b_alfworld_summary.json`,
`phase4_coverage.json`, `replay_progress.log`, `replay_shards/`.

## Reproducing

Order matters — each step consumes the previous one's output.

```bash
export PYTHONPATH=analysis
P=/opt/anaconda3/envs/Jagent/bin/python          # ALFWorld + TextWorld live here
Y=/opt/anaconda3/envs/yllm/bin/python            # pyarrow lives here, for the parquet

$P analysis/gate1_manifest.py                    # pin the inputs (do this FIRST)
$P analysis/gate1_inventory.py                   # phase 0
$P analysis/gate1_tier_a.py                      # phases 1 + 2
ALFWORLD_DATA=/home/user/.cache/alfworld \
  $P analysis/gate1_replay_alfworld.py --jobs 24 --timeout 900    # phase 3
$Y analysis/gate1_assemble.py                    # phase 4
$P analysis/gate1_phase5.py                      # phase 5
$P analysis/gate1_summary.py                     # R1-R4
```

`gate1_manifest.py --verify` re-checks that no pinned prefix changed.
`gate1_inventory.py --from-json` re-renders the Phase-0 markdown without rescanning.
The replay is resumable: completed episodes are kept as shards in `replay_shards/` and
skipped on a rerun.

## Determinism

The corpus is live — a `judge_hotpot.py` process and eight `run_probes.py` workers were
appending to the `Qwen3.5-*` arms while gate 1 ran. Every input is therefore pinned to a
recorded byte length and hash, and every reader takes only that prefix, so a concurrent
append cannot move a number. Verified: a judge file grew by 139 KB mid-run and the
Phase-1 output was byte-identical across the runs that straddled it.

## What the labels mean

`y_env` is **1 = incorrect, 0 = correct, blank = not labelable**. Blank is not a
correct label — Tier A only ever produces incorrect labels, and coverage is partial by
construction. Every blank carries an `unlabelable_reason`.

Two known limits, both reported rather than papered over:

- **HotpotQA search steps cannot get a Tier-B label.** The vendored corpus has no
  `supporting_facts`, so "retrieved a gold supporting document" is not evaluable. The
  HotpotQA *answer*-step rule (exact match) is applied; Tier A is unaffected. See
  Phase 0 §0.1.
- **A3 reproduces the logged loop detector exactly.** `state_hash` is a hash of the
  post-action observation, so `(state_hash, action)` is the `(obs, action)` pair the
  drivers already track as `loop_flag`. A3 adds no independent evidence and cannot see a
  revisit to the same world state that produced a different observation.
