"""E1b analyses: in-generation vs post-hoc rank agreement (Kendall tau-b), and the
round-number clustering histogram (runs on BOTH U_T_verbalized and U_T_posthoc_numeric).

Headline E1b contrast (2026-07-16 handoff §3.2.5): rank agreement between Probe V and the
post-hoc probes, per cell (B and D). High agreement -> the distinction is philosophical and
either protocol works; low agreement -> the two protocols measure different objects. Either
way it is a finding, reported not adjudicated.

Steps enter a pairwise comparison only if BOTH probes parsed on that step (exclude-never-
impute), and the exclusion count is reported alongside tau.
"""
from __future__ import annotations

from collections import Counter

import numpy as np


def kendall_tau_b(x, y) -> float:
    """Kendall's tau-b (tie-adjusted). O(n^2) pairwise — fine at E1 scale (~2k steps)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < 2:
        return float("nan")
    iu = np.triu_indices(n, 1)
    dx = np.sign(x[:, None] - x[None, :])[iu]
    dy = np.sign(y[:, None] - y[None, :])[iu]
    s = float((dx * dy).sum())                 # concordant - discordant (ties contribute 0)
    n0 = n * (n - 1) / 2.0
    tx = float((dx == 0).sum())
    ty = float((dy == 0).sum())
    denom = np.sqrt((n0 - tx) * (n0 - ty))
    return s / denom if denom > 0 else float("nan")


def rank_agreement(records: list[dict], key_a: str, key_b: str) -> dict:
    """Kendall tau-b between two probe readings over the steps where BOTH parsed."""
    xs, ys, excluded = [], [], 0
    for r in records:
        a, b = r["probes"].get(key_a), r["probes"].get(key_b)
        if a is None or b is None:
            excluded += 1
            continue
        xs.append(a)
        ys.append(b)
    return {"probe_a": key_a, "probe_b": key_b, "n": len(xs), "n_excluded": excluded,
            "kendall_tau_b": round(kendall_tau_b(xs, ys), 4) if len(xs) >= 2 else None}


def round_number_histogram(records: list[dict], key: str) -> dict:
    """Counts of raw confidence values (as integer percent, c = 1 - U) — shows the expected
    spikes at 50/70/80/90. Show it, own it, demonstrate ranking survives it (spec E1b)."""
    counts = Counter()
    for r in records:
        u = r["probes"].get(key)
        if u is not None:
            counts[int(round(100 * (1.0 - u)))] += 1
    return {"probe": key, "n": sum(counts.values()),
            "histogram": dict(sorted(counts.items()))}
