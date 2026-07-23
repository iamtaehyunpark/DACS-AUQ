"""E0 step sampling: 150 steps from the 30-trajectory entangled run, stratified by tau cell
(proportional allocation, min 10 per non-empty cell — spec E0 protocol). Deterministic seed.

Amended 2026-07-20 (pre E0-full data): strata are tau cell x loop/fresh, where a loop
step is a repeated (action, observation) transition within its episode
(src/analysis/loop_steps.py). The E0 smoke showed 83/104 steps inside repeated-thought
groups; without this crossing, human agreement would be measured almost entirely on
repeated states, which are both easier to judge and less informative.
"""
from __future__ import annotations

import json
import random

from src.analysis.loop_steps import loop_step_uids


def tau_cell(rec: dict) -> str:
    tau = rec.get("tau")
    if tau is None:
        return "untagged"
    return f"I{tau['I']}W{tau['W']}R{tau['R']}"


def stratum(rec: dict, loops: set[tuple]) -> str:
    uid = (rec.get("run_id"), rec.get("task_id"), rec["step_idx"])
    return f"{tau_cell(rec)}|{'loop' if uid in loops else 'fresh'}"


def step_uid(rec: dict) -> str:
    return f"{rec['run_id']}|{rec['task_id']}|{rec['step_idx']}"


def stratified_sample(records: list[dict], *, n: int = 150, min_per_cell: int = 10,
                      seed: int = 7) -> list[dict]:
    """Proportional allocation by (tau cell x loop/fresh) stratum with a floor of
    min(min_per_cell, stratum size); largest-remainder rounding; overflow trimmed
    from the largest strata."""
    loops = loop_step_uids(records)
    cells: dict[str, list[dict]] = {}
    for r in records:
        cells.setdefault(stratum(r, loops), []).append(r)
    total = sum(len(v) for v in cells.values())
    n = min(n, total)

    exact = {k: n * len(v) / total for k, v in cells.items()}
    quota = {k: int(exact[k]) for k in cells}
    for k in sorted(cells, key=lambda k: exact[k] - quota[k], reverse=True):
        if sum(quota.values()) >= n:
            break
        quota[k] += 1
    for k, v in cells.items():                       # floor
        quota[k] = min(len(v), max(quota[k], min_per_cell))
    while sum(quota.values()) > n:                   # trim overflow from the largest cells
        k = max(quota, key=lambda k: (quota[k] > min(len(cells[k]), min_per_cell), quota[k]))
        quota[k] -= 1

    rng = random.Random(seed)
    out: list[dict] = []
    for k in sorted(cells):
        out.extend(rng.sample(cells[k], quota[k]))
    return out


def sample_file(in_path: str, out_path: str, **kw) -> dict:
    with open(in_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    picked = stratified_sample(records, **kw)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in picked:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    loops = loop_step_uids(records)     # loop flags need full-episode context, not the sample
    counts: dict[str, int] = {}
    for r in picked:
        k = stratum(r, loops)
        counts[k] = counts.get(k, 0) + 1
    return {"n_sampled": len(picked), "by_cell": counts, "n_source": len(records)}
