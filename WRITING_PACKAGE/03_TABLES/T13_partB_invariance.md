# T13 — GATE-4 Part B: conditional invariance ratios

**Caption-of-record.** Criterion: median within-class between-target 1-Wasserstein < 1/3 of the class-separation distance, self-cells excluded. Conditional invariance holds on hotpotqa (0.162, 0.151) and fails on alfworld (0.809, 0.364). Part A also failed; **the two results are reported side by side and are not reconciled** (spec §3). Verdict: SPLIT.

- Labels: L2 · construct: violation+judgment · claim: C-invariance
- source: direct copy of `tables_gate4/B_invariance_verdict.csv`; pairwise distances in F3 (`tables_gate4/B_wasserstein_pairs.csv`)

| env | judge | within-median | class separation | ratio | CI supported |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B | 6.375 | 7.880 | 0.809 | **no** |
| alfworld | Qwen3.6-35B | 1.239 | 3.404 | 0.364 | **no** |
| hotpotqa | Llama-3.3-70B | 1.850 | 11.410 | 0.162 | **yes** |
| hotpotqa | Qwen3.6-35B | 0.585 | 3.869 | 0.151 | **yes** |
