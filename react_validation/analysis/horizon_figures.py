"""Figures for the P(True) hindsight-horizon sweep (result/ctxrule/ptrue_horizon_e1b.jsonl).

  fig1_curves   mean U(k) per (step label x trajectory outcome) cell, with SEM bands
  fig2_auroc    step-level AUROC at each horizon — where does lookahead stop paying?
  fig3_deltas   per-step ΔK distribution by cell (the hypothesis under test)
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import ptrue_horizon_probe as H
import ptrue_context_rule_probe as P

CELLS = [(1, False, "INCORRECT step / episode FAILED", "#c0392b", "-"),
         (1, True, "INCORRECT step / episode SUCCEEDED", "#e67e22", "--"),
         (0, False, "correct step / episode FAILED", "#8e44ad", "-"),
         (0, True, "correct step / episode SUCCEEDED", "#2471a3", "--")]


def _sem(v):
    return statistics.stdev(v) / (len(v) ** 0.5) if len(v) > 1 else 0.0


def fig_curves(U, meta, keys, ks, out):
    fig, ax = plt.subplots(figsize=(9.4, 5.8))
    for lab, succ, name, col, ls in CELLS:
        g = [x for x in keys if meta[x]["label"] == lab and meta[x]["success"] == succ]
        m, e = [], []
        for k in ks:
            v = [U[(x, k)] for x in g if (x, k) in U]
            m.append(statistics.fmean(v) if v else np.nan)
            e.append(_sem(v))
        m, e = np.array(m), np.array(e)
        ax.plot(ks, m, color=col, ls=ls, lw=2.4, marker="o", ms=5, label="%s (n=%d)" % (name, len(g)))
        ax.fill_between(ks, m - e, m + e, color=col, alpha=0.13)
    ax.set_xlabel("k = number of subsequent trajectory steps shown to the probe")
    ax.set_ylabel("mean U = 1 − P(True) for the step under evaluation")
    ax.set_title("Uncertainty about a FIXED step as its future is revealed\n"
                 "every cell drifts upward — including correct steps in successful episodes",
                 fontsize=11)
    ax.axvline(0, color="black", lw=0.8, alpha=0.4)
    ax.text(0.02, 0.02, "k=0 is the only causally available reading", transform=ax.transAxes,
            fontsize=8.5, color="#555555")
    ax.legend(fontsize=8.8, frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


def fig_auroc(U, meta, keys, ks, out):
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    aus, los, his = [], [], []
    for k in ks:
        pairs, by_task = [], {}
        for x in keys:
            if (x, k) in U:
                pairs.append((U[(x, k)], meta[x]["label"]))
                by_task.setdefault(x[0], []).append((U[(x, k)], meta[x]["label"]))
        au = P._auroc(pairs)
        lo, hi = P._auroc_ci(by_task)
        aus.append(au); los.append(lo); his.append(hi)
    aus, los, his = np.array(aus), np.array(los), np.array(his)
    ax.plot(ks, aus, color="#1a5276", lw=2.4, marker="o", ms=6)
    ax.fill_between(ks, los, his, color="#1a5276", alpha=0.15)
    best = int(np.argmax(aus))
    ax.scatter([ks[best]], [aus[best]], s=150, facecolor="none", edgecolor="#c0392b", lw=2, zorder=5)
    ax.annotate("peak at k=%d (%.3f)\none step of hindsight" % (ks[best], aus[best]),
                (ks[best], aus[best]), textcoords="offset points", xytext=(18, -6),
                fontsize=9, color="#c0392b")
    ax.axhline(aus[0], color="#7f8c8d", ls="--", lw=1.2)
    ax.text(ks[-1], aus[0] - 0.012, "k=0 baseline (%.3f)" % aus[0], ha="right", va="top",
            fontsize=8.6, color="#7f8c8d")
    ax.axhline(0.5, color="black", ls=":", lw=1)
    ax.set_xlabel("k = subsequent steps shown")
    ax.set_ylabel("AUROC for the judge's step label")
    ax.set_title("How much lookahead is worth buying?\n"
                 "discrimination peaks at one step and decays after", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


def fig_deltas(U, meta, keys, ks, out):
    K = max(ks)
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    data, labels, cols = [], [], []
    for lab, succ, name, col, _ls in CELLS:
        g = [x for x in keys if meta[x]["label"] == lab and meta[x]["success"] == succ]
        d = [U[(x, K)] - U[(x, 0)] for x in g if (x, K) in U and (x, 0) in U]
        data.append(d); labels.append(name.replace(" / ", "\n")); cols.append(col)
    bp = ax.boxplot(data, patch_artist=True, widths=0.55, showmeans=True)
    for patch, c in zip(bp["boxes"], cols):
        patch.set_facecolor(c); patch.set_alpha(0.35)
    for i, d in enumerate(data, 1):
        ax.scatter(np.random.default_rng(0).normal(i, 0.055, len(d)), d, s=11,
                   color=cols[i - 1], alpha=0.65, zorder=3)
    ax.axhline(0, color="black", lw=1)
    ax.set_xticklabels(labels, fontsize=8.4)
    ax.set_ylabel("ΔK = U_K − U_0  (per step)")
    ax.set_title("The hypothesis under test: does Δ separate on-path from off-path?\n"
                 "It does not — the largest upward drift is in CORRECT steps of SUCCESSFUL episodes",
                 fontsize=11)
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", default="result/ctxrule/ptrue_horizon_e1b.jsonl")
    ap.add_argument("--outdir", default="result/ctxrule/figures_horizon")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    U, meta, ks = H.load(a.records)
    keys = sorted(meta)
    print("loaded %d steps, horizons %s" % (len(keys), ks))
    for name, fn in [("fig1_curves", fig_curves), ("fig2_auroc", fig_auroc),
                     ("fig3_deltas", fig_deltas)]:
        p = os.path.join(a.outdir, name + ".png")
        fn(U, meta, keys, ks, p)
        print("wrote", p)


if __name__ == "__main__":
    main()
