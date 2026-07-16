"""E1b contamination ablation analysis (PRE-REGISTERED, 2026-07-16 handoff §3.2.6).

Compares decoupled thoughts generated WITH vs WITHOUT the in-generation confidence
instruction (same tasks, same seeds; configs/e1b_contamination.yaml) to empirically bound
the "self-grading changes the thought" contamination. Trajectories may diverge after the
first differing action, so the comparison is DISTRIBUTIONAL, not step-paired: thought
length, thought MTE, and the executed-action verb distribution (total variation distance).
"""
from __future__ import annotations

import json

import numpy as np


def _stats(values: list[float]) -> dict:
    a = np.asarray(values, dtype=float)
    return {"n": len(a), "mean": float(a.mean()) if len(a) else None,
            "sd": float(a.std(ddof=1)) if len(a) > 1 else None}


def _verb_dist(records: list[dict]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for r in records:
        v = (r.get("action_parsed") or {}).get("verb") or "?"
        counts[v] = counts.get(v, 0) + 1
    total = sum(counts.values()) or 1
    return {k: c / total for k, c in counts.items()}


def compare(records_with: list[dict], records_without: list[dict]) -> dict:
    out = {}
    for name, recs in (("with_confidence", records_with), ("without_confidence", records_without)):
        out[name] = {
            "n_steps": len(recs),
            "thought_len_chars": _stats([len(r["thought_text"]) for r in recs]),
            "thought_mte": _stats([r["probes"]["thought_mte"] for r in recs
                                   if r["probes"]["thought_mte"] is not None]),
            "verb_dist": _verb_dist(recs),
        }
    verbs = set(out["with_confidence"]["verb_dist"]) | set(out["without_confidence"]["verb_dist"])
    tv = 0.5 * sum(abs(out["with_confidence"]["verb_dist"].get(v, 0.0)
                       - out["without_confidence"]["verb_dist"].get(v, 0.0)) for v in verbs)
    out["action_dist_total_variation"] = round(tv, 4)
    return out


def compare_files(path_with: str, path_without: str) -> dict:
    def load(p):
        with open(p, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    return compare(load(path_with), load(path_without))
