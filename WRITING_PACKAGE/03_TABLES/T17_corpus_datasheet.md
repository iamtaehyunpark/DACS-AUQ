# T17 — Corpus datasheet

**Caption-of-record.** The released corpus: `labels_gate1.csv` has 62,065 rows × 39 columns with required provenance columns all present; the score corpus spans 61 (judge × target × environment) cells (16 self + 45 cross), 147 score files, 31.4 GB, 1,222,292 lines. Per-arm step and per-construct label counts below; construct counts overlap by construction (a step can be both a violation and an outcome) — they are an inventory, not a partition. Label families: violation (A1/A2/A3 deterministic), outcome (A4 + Tier-B replay-derived), judgment (3-judge ensemble), with composites y_env and violation+judgment (registered primary, A30 §5.3).

- Labels: L2 corpus (judgment column is the audited L1 ensemble) · claim: C4-corpus
- source: `S0_SUMMARY.md` (labels inventory table); corpus at `reports/gate1/labels_gate1.csv`

Data: `T17_corpus_datasheet.csv` (16 arms; columns dataset, arm, steps, in_matrix, violation, outcome, judgment).
