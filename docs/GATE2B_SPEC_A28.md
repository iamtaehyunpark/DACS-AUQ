# GATE-2b SPEC (A28) — Cut Transfer: Can the Decision Boundary Move Without Labels?
## V · S-LOTO-raw · S-LOTO-quantile · S-fitted, on banked P(True) values

**2026-08-06 · Pre-registered before any arm is computed. Commit to repo before running.**
**Depends on: gate-2 b1 results (banked). Blocks: §6d deployment-claim wording; boss briefing.**

## Question

Gate-2 b1 established (preview labels): reading the probability beats reading
the model's answer in 55/60 cells (+0.065 balanced accuracy OOS), but the
winning cut was fitted with labeled episodes *from the same target*. The open
question is who pays for those labels on a new target. This gate tests whether
the cut can be obtained from *other* targets — i.e., whether "characterize
once, deploy across targets" holds at the decision level, label-free with
respect to the deployment target.

The verdict-vs-value contest is a cut-vs-cut contest on one channel: the
argmax verdict IS the value at a fixed semantic cut (0.5 renormalized). This
gate asks whether that boundary can be beaten using no labels from the target.

## Data

Banked per-step P(True) values (same source that produced
`verdict_vs_value.csv`), all (assessor × target × dataset) cells, scope
AGG-true primary (other scopes as sensitivity if cheap). No new inference.
Labels: L1 (3-judge ensemble) — PREVIEW; rerun under L2 (gate-1
environment-anchored) for the record. No conclusion freezes on L1.

## Arms (per cell; held-out target = the cell's target)

- **V** — argmax verdict = fixed cut at 0.5 on renormalized True/False mass.
  Black-box floor; no logprobs, no labels, no transfer.
- **S-LOTO-raw** — cut fitted (balanced-accuracy-optimal) on the pooled
  labeled data of all *other* targets of the same assessor × dataset, applied
  as a raw score threshold to the held-out target. Labels used: other targets
  only. Tests raw-threshold transfer — predicted to FAIL (pre-registered:
  §7.1, uncertainty levels move 5–30× across targets); its failure is the
  impossibility claim demonstrated at decision level.
- **S-LOTO-quantile** — the same other-target fit expressed as a *percentile*,
  mapped through the held-out target's own UNLABELED score distribution to a
  raw cut. Uses from the held-out target: raw scores only, zero labels. This
  is the characterization claim as a decision procedure. NOTE (honesty
  label): uses the full frozen score distribution of the target — the BATCH
  version of the online rule; the sequential/prequential variant is paper
  work, out of scope for this gate.
- **S-fitted** — per-target labeled cut, episode-split OOS (= existing
  `value_out`). The ~200-label calibrated ceiling. Reused, not recomputed.

Fitting details, fixed now: cut criterion = balanced accuracy on the fitting
pool; pooling across other targets is per-step (weighted by n) with a
per-target-macro sensitivity variant; deepseek and the n≤2 assessors
(Qwen3.5-4B/9B) are included as held-out targets where they have cells but
excluded from fitting pools smaller than 3 targets; any cell whose fitting
pool has < 3 targets is reported but excluded from the pass/fail count.

## Metrics

Per cell: balanced accuracy for each arm (TPR/TNR reported). Headline:
- **Capture ratio** = (S-LOTO-quantile − V) / (S-fitted − V), per cell and
  aggregated (cells with S-fitted − V ≤ 0.01 excluded from the ratio,
  reported separately as saturated).
- Regret vs S-fitted for each arm.
- Cross-target sd of each arm's balanced accuracy (transfer stability).
Raw accuracy prohibited as a primary metric (base rates 0.15–0.89).

## Pre-registered predictions and decision rules

- P-raw: S-LOTO-raw < S-fitted by a wide margin and < V in a substantial
  minority of cells (raw transfer fails). If S-LOTO-raw ≈ S-fitted instead,
  §7.1's practical-bite framing must be softened — write that down too.
- P-quantile: S-LOTO-quantile ≥ V in ≥ 80% of countable cells.
- **G2b-R1 (PASS):** P-quantile holds AND aggregate capture ratio ≥ 0.5 →
  "characterize once, deploy label-free" stands at decision level; §6d keeps
  its deployment claim (batch-validated, sequential variant still owed).
- **G2b-R2 (PARTIAL):** P-quantile holds but capture ratio < 0.5 → label-free
  transfer works but local labels matter; §6d is rewritten around the
  ~200-label calibration tier as the primary mode, label-free as degraded
  fallback.
- **G2b-R3 (FAIL):** P-quantile fails (< 80%) → the label-free deployment
  claim does not survive; the paper's machinery is repositioned as
  labeled-calibration tooling; this outcome is written down now so it cannot
  be argued away later.
- Capable-judge stratum (Llama-70B, Qwen-35B assessors) reported separately;
  rules are evaluated on ALL judges and on the capable stratum — divergence
  between the two is a qualification (§6c) finding, not a discrepancy.

## Sequencing & cost

Runs now on L1 (preview for the advisor briefing), rerun on L2 when gate-1
lands (pass of record). ~50-line extension of the script that produced
`verdict_vs_value.csv` (fold by target; add percentile mapping). Zero
inference; an afternoon.

## Deliverables

`tables_gate2b/` per-cell four-arm table + capture ratios (both label
passes); `GATE2B_SUMMARY.md` — one page: P-raw, P-quantile, G2b-R1..R3 with
PASS/PARTIAL/FAIL and the deciding numbers; one figure: per-cell V →
LOTO-raw → LOTO-quantile → fitted ladder. The advisor-facing artifact is the
one-line-per-cell table: V | LOTO-raw | LOTO-quantile | fitted, plus the
aggregate capture ratio.
