"""Trajectory-level bootstrap (spec §0.7). Steps within a trajectory are NOT independent, so all
resampling is at the TRAJECTORY level: resample whole episodes with replacement, then recompute the
statistic on the pooled steps of the resampled episodes. 10k resamples by default.

The headline E1 statistic is the paired difference (spec E1★.4):
    Δ = AUROC(elicited) − AUROC(best entropy probe), on identical steps.
"""
from __future__ import annotations

import numpy as np

from src.analysis.discrimination import auroc


def _group_index(groups) -> tuple[list, dict]:
    """Return (unique_group_ids, {group_id: np.array of row indices})."""
    uniq = list(dict.fromkeys(groups))
    idx: dict = {g: [] for g in uniq}
    for i, g in enumerate(groups):
        idx[g].append(i)
    return uniq, {g: np.asarray(v, dtype=int) for g, v in idx.items()}


def paired_auroc_delta(scores_a, scores_b, labels, groups, *,
                       n_boot: int = 10000, seed: int = 12345, alpha: float = 0.05) -> dict:
    """Δ = AUROC(a) − AUROC(b) with a trajectory-level bootstrap CI and a two-sided p.

    scores_a/scores_b: aligned per-step score arrays (a = elicited, b = best entropy probe).
    labels: per-step 1=incorrect. groups: per-step trajectory/episode id (resampling unit).
    Returns {delta, ci_low, ci_high, p_two_sided, n_boot}.
    """
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    y = np.asarray(labels, dtype=int)
    point = auroc(a, y) - auroc(b, y)

    uniq, gidx = _group_index(groups)
    m = len(uniq)
    rng = np.random.default_rng(seed)
    deltas = np.empty(n_boot, dtype=float)
    filled = 0
    for _ in range(n_boot):
        pick = rng.integers(0, m, size=m)
        rows = np.concatenate([gidx[uniq[p]] for p in pick])
        yy = y[rows]
        if yy.sum() == 0 or yy.sum() == len(yy):
            continue  # degenerate resample (one class) — skip, don't bias the CI with a NaN
        deltas[filled] = auroc(a[rows], yy) - auroc(b[rows], yy)
        filled += 1
    deltas = deltas[:filled]
    lo = float(np.percentile(deltas, 100 * alpha / 2))
    hi = float(np.percentile(deltas, 100 * (1 - alpha / 2)))
    # two-sided p: proportion of resamples on the opposite side of 0 from the point estimate, doubled
    if point >= 0:
        p = 2.0 * float((deltas <= 0).mean())
    else:
        p = 2.0 * float((deltas >= 0).mean())
    return {"delta": float(point), "ci_low": lo, "ci_high": hi,
            "p_two_sided": min(1.0, p), "n_boot": filled}


def bootstrap_ci(values_by_step, labels, groups, stat_fn, *,
                 n_boot: int = 10000, seed: int = 12345, alpha: float = 0.05) -> dict:
    """Generic trajectory-level bootstrap CI for stat_fn(scores, labels) (e.g. auroc or prr)."""
    s = np.asarray(values_by_step, dtype=float)
    y = np.asarray(labels, dtype=int)
    point = stat_fn(s, y)
    uniq, gidx = _group_index(groups)
    m = len(uniq)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.integers(0, m, size=m)
        rows = np.concatenate([gidx[uniq[p]] for p in pick])
        yy = y[rows]
        if yy.sum() == 0 or yy.sum() == len(yy):
            continue
        v = stat_fn(s[rows], yy)
        if v == v:  # drop NaN
            vals.append(v)
    vals = np.asarray(vals, dtype=float)
    return {"point": float(point),
            "ci_low": float(np.percentile(vals, 100 * alpha / 2)),
            "ci_high": float(np.percentile(vals, 100 * (1 - alpha / 2))),
            "n_boot": len(vals)}
