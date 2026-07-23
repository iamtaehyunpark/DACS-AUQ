"""E0 agreement analysis: Cohen's kappa human-human and judge-human, raw agreement %, and a
confusion breakdown by tau cell (spec E0.4). Label space everywhere: 1 = good, 0 = bad
(the judge's native space; record label.judge maps correct->1, incorrect->0).
"""
from __future__ import annotations

import csv
import json

from src.e0.sample_steps import step_uid, tau_cell


def cohen_kappa(a: list[int], b: list[int]) -> float:
    assert len(a) == len(b) and a, "aligned non-empty label lists required"
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)


def load_human_csv(path: str) -> dict[str, int]:
    out: dict[str, int] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("label") in ("0", "1"):
                out[row["uid"]] = int(row["label"])
    return out


def load_judge_labels(labeled_jsonl: str) -> tuple[dict[str, int], dict[str, str]]:
    """Returns ({uid: 0|1}, {uid: tau_cell}) from a judge-labeled records file."""
    labels: dict[str, int] = {}
    cells: dict[str, str] = {}
    with open(labeled_jsonl, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            uid = step_uid(r)
            cells[uid] = tau_cell(r)
            j = r["label"]["judge"]
            if j in ("correct", "incorrect"):
                labels[uid] = 1 if j == "correct" else 0
    return labels, cells


def _pairwise(a: dict[str, int], b: dict[str, int]) -> dict:
    uids = sorted(set(a) & set(b))
    if not uids:
        return {"n": 0}
    x = [a[u] for u in uids]
    y = [b[u] for u in uids]
    return {"n": len(uids), "kappa": round(cohen_kappa(x, y), 4),
            "raw_agreement": round(sum(1 for p, q in zip(x, y) if p == q) / len(uids), 4)}


def agreement_report(judge_labeled_jsonl: str, human_csvs: list[str]) -> dict:
    judge, cells = load_judge_labels(judge_labeled_jsonl)
    humans = {f"human_{i + 1}": load_human_csv(p) for i, p in enumerate(human_csvs)}

    report: dict = {"pairs": {}, "by_tau_cell": {}}
    names = list(humans)
    if len(names) >= 2:
        report["pairs"]["human_human"] = _pairwise(humans[names[0]], humans[names[1]])
    for name, h in humans.items():
        report["pairs"][f"judge_{name}"] = _pairwise(judge, h)

    # confusion by tau cell: judge vs each human, counts of (judge,human) label pairs
    for name, h in humans.items():
        for uid in set(judge) & set(h):
            cell = cells.get(uid, "untagged")
            key = report["by_tau_cell"].setdefault(cell, {})
            pair = f"j{judge[uid]}h{h[uid]}"
            key[pair] = key.get(pair, 0) + 1
    return report
