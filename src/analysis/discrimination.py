"""Step-level discrimination metrics. Positive class = `incorrect` (label 1), i.e. the probe
should rank steps the judge marked incorrect above correct ones (spec §0.7).

- auroc: rank-based (Mann-Whitney), ties handled by average rank.
- prr:   Prediction Rejection Ratio, ReDAct App. C (arXiv:2604.07036), computed up to 50% rejection.
"""
from __future__ import annotations

import numpy as np


def auroc(scores, labels) -> float:
    """AUROC with positive class = 1. NaN if a class is empty. Higher uncertainty on errors -> >0.5."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=float)
    sorted_s = s[order]
    i = 0
    while i < len(s):  # average-rank tie handling
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def _rejection_quality_curve(unc: np.ndarray, correct: np.ndarray, max_rej: float, order: str):
    """Quality (= accuracy of retained set) as a function of rejection fraction in [0, max_rej].
    `order`: 'unc' rejects highest-uncertainty first; 'oracle' rejects actual errors first;
    'rnd' is the flat base-accuracy line. Returns the area under the quality curve (trapezoid)."""
    n = len(unc)
    if order == "unc":
        idx = np.argsort(-unc, kind="mergesort")          # drop most-uncertain first
    elif order == "oracle":
        idx = np.argsort(correct, kind="mergesort")        # correct=0 (errors) dropped first
    else:  # random -> flat line at base accuracy; area is trivially base_acc * max_rej
        base = float(correct.mean())
        return base * max_rej
    c = correct[idx]
    k_max = int(np.floor(max_rej * n))
    rejs, quals = [], []
    for k in range(0, k_max + 1):
        retained = c[k:]
        rejs.append(k / n)
        quals.append(float(retained.mean()) if len(retained) else 1.0)
    # trapezoidal area, version-independent (np.trapz removed in numpy 2.x)
    x, yq = np.asarray(rejs), np.asarray(quals)
    return float(np.sum((x[1:] - x[:-1]) * (yq[1:] + yq[:-1]) / 2.0)) if len(x) > 1 else 0.0


def prr(scores, labels, max_rejection: float = 0.5) -> float:
    """PRR = (AUC_unc − AUC_rnd) / (AUC_oracle − AUC_rnd), quality = accuracy of non-rejected
    predictions, integrated over rejection in [0, max_rejection] (ReDAct: up to 50%). Higher = better."""
    y = np.asarray(labels, dtype=int)              # 1 = incorrect
    unc = np.asarray(scores, dtype=float)
    correct = 1 - y                                # 1 = correct (the 'quality' being retained)
    if correct.sum() in (0, len(correct)):
        return float("nan")                        # no discrimination possible
    auc_unc = _rejection_quality_curve(unc, correct, max_rejection, "unc")
    auc_rnd = _rejection_quality_curve(unc, correct, max_rejection, "rnd")
    auc_orc = _rejection_quality_curve(unc, correct, max_rejection, "oracle")
    denom = auc_orc - auc_rnd
    if abs(denom) < 1e-12:
        return float("nan")
    return float((auc_unc - auc_rnd) / denom)
