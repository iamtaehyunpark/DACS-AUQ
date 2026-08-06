# S0 SUMMARY — repo/state inventory

Spec: `docs/specs/S0_SPEC.md` (sha256 `71d1bb9bb392b332`)

**Status: OK**

## Cells

| family | cells |
|---|---|
| self | 16 |
| cross | 45 |
| **total** | **61** |

147 score files, 31.4 GB, 1,222,292 lines. 1008 worker shards recorded as provenance only.

## Labels

`reports/gate1/labels_gate1.csv` — 62,065 rows, 39 columns, required provenance columns ALL PRESENT.

| arm | steps | in_matrix | violation | outcome | judgment |
|---|---|---|---|---|---|
| alfworld/Llama-3.3-70B-Instruct | 4765 | 4765 | 1714 | 4366 | 4142 |
| alfworld/Mistral-7B-Instruct-v0.3 | 6482 | 6482 | 4616 | 5913 | 5866 |
| alfworld/Phi-4-mini-instruct | 6611 | 6611 | 4109 | 6029 | 5682 |
| alfworld/Qwen3.5-27B | 3445 | 0 | 967 | 3190 | 0 |
| alfworld/Qwen3.5-4B | 4602 | 0 | 2464 | 4266 | 3475 |
| alfworld/Qwen3.5-9B | 4590 | 0 | 1840 | 4133 | 3663 |
| alfworld/Qwen3.6-35B-A3B | 3342 | 3342 | 1157 | 3140 | 2707 |
| alfworld/deepseek-v4-flash | 3313 | 3313 | 779 | 2945 | 2981 |
| alfworld/gemma-3-4b-it | 6790 | 6790 | 5538 | 6408 | 6372 |
| hotpotqa/Llama-3.3-70B-Instruct | 2530 | 2530 | 139 | 1054 | 1845 |
| hotpotqa/Mistral-7B-Instruct-v0.3 | 3224 | 3224 | 899 | 2140 | 2607 |
| hotpotqa/Phi-4-mini-instruct | 2716 | 2716 | 843 | 1558 | 2229 |
| hotpotqa/Qwen3.5-4B | 2479 | 0 | 279 | 1279 | 1912 |
| hotpotqa/Qwen3.5-9B | 2376 | 0 | 218 | 1231 | 1136 |
| hotpotqa/Qwen3.6-35B-A3B | 2235 | 2235 | 92 | 1075 | 1784 |
| hotpotqa/gemma-3-4b-it | 2565 | 2565 | 835 | 1281 | 2229 |

Construct counts overlap by construction (a step can be both a violation and an outcome); they are an inventory, not a partition.

## Capacity

| gpu | name | free MiB | util pct |
|---|---|---|---|
| 0 | NVIDIA A100 80GB PCIe | 81158 | 0 |
| 1 | NVIDIA A100 80GB PCIe | 81158 | 0 |
| 2 | NVIDIA A100 80GB PCIe | 81158 | 0 |
| 3 | NVIDIA A100 80GB PCIe | 81158 | 0 |
| 4 | NVIDIA A100 80GB PCIe | 81158 | 0 |

Throughput constant 3300 assessments / 5 min / A100 is INHERITED and **unverified** — §1 requires a 500-step probe before any GPU stage sizes itself against it.

## STOP

None. Conditions checked: (1) label provenance columns present; (2) every cell referenced by `figures/tables_gate2b1/gate2b1_cells_AGG-true_full.csv` has a score file on disk.


`runs/manifest.json` written (141 env lines in `runs/env.txt`). Later stages record their spec sha256 under `specs_recorded`.

