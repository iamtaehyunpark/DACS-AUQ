"""Figures for the P(True) context x rule probe (result/ctxrule/ptrue_ctxrule_e1b.jsonl).

Five figures, each answering one question the sweep was built to answer:

  fig1_separation      per-condition separation Delta, context ladder vs rule cells
  fig2_dumbbell        mean U on incorrect vs correct steps — WHERE a Delta comes from
  fig3_heatmap         the raw 20 x 11 matrix; at n=20 this is the primary artifact
  fig4_hindsight       paired per-step slopes C3->C5 and C3->C6, colored by judge label
  fig5_rule_stratum    rule effect per stratum against the decoy floor (the false-positive test)

Usage: python ctxrule_figures.py [--records ...] [--outdir ...]
Stdlib + numpy + matplotlib only; reads the frozen sweep records, computes nothing new.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

CONDS = [("C0", "R0"), ("C1", "R0"), ("C2", "R0"), ("C3", "R0"), ("C4", "R0"),
         ("C5", "R0"), ("C6", "R0"), ("C3", "R1"), ("C3", "R2"), ("C3", "R3"), ("C0", "R2")]
LADDER = CONDS[:7]
RULECELLS = CONDS[7:]
REF = ("C3", "R0")
SHORT = {"C0": "C0\ntask+action", "C1": "C1\n+last obs", "C2": "C2\n+history",
         "C3": "C3\n+reasoning\n(production)", "C4": "C4\nno action",
         "C5": "C5\n+outcome\n(hindsight)", "C6": "C6\n+outcome\n+next step"}
RULE_SHORT = {"R1": "R1 generic\nrubric", "R2": "R2 targeted\n(repeat)",
              "R3": "R3 decoy\n(irrelevant)"}
STRATUM_ORDER = ["loop", "inadmissible", "other", "revisit", "plain"]
C_INC, C_COR, C_REF, C_HL = "#c0392b", "#2471a3", "#7f8c8d", "#e67e22"


def load(path):
    cells, meta = {}, {}
    for line in open(path):
        if not line.strip():
            continue
        r = json.loads(line)
        k = (r["task_id"], r["step_idx"])
        meta[k] = {"label": r["label"], "stratum": r["stratum"]}
        if r.get("parse_ok") and r.get("U") is not None:
            cells[(k, (r["context_id"], r["rule_id"]))] = float(r["U"])
    keys = sorted(meta, key=lambda k: (-meta[k]["label"],
                                       STRATUM_ORDER.index(meta[k]["stratum"]), str(k)))
    return cells, meta, keys


def _mean(xs):
    return statistics.fmean(xs) if xs else float("nan")


def means(cells, meta, keys, cond):
    inc = [cells[(k, cond)] for k in keys if meta[k]["label"] == 1 and (k, cond) in cells]
    cor = [cells[(k, cond)] for k in keys if meta[k]["label"] == 0 and (k, cond) in cells]
    return _mean(inc), _mean(cor)


def paired(cells, keys, ca, cb, pred=None):
    d = [cells[(k, ca)] - cells[(k, cb)] for k in keys
         if (pred is None or pred(k)) and (k, ca) in cells and (k, cb) in cells]
    return (statistics.median(d) if d else float("nan"),
            sum(1 for x in d if x > 0), len(d))


# --------------------------------------------------------------------------- fig 1

def fig_separation(cells, meta, keys, out):
    fig, ax = plt.subplots(figsize=(11, 5.2))
    deltas, labels, colors = [], [], []
    for c in LADDER:
        mi, mc = means(cells, meta, keys, c)
        deltas.append(mi - mc)
        labels.append(SHORT[c[0]])
        colors.append(C_REF if c == REF else (C_HL if c[0] in ("C5", "C6") else C_INC))
    deltas.append(np.nan); labels.append(""); colors.append("none")      # visual gap
    for c in RULECELLS:
        mi, mc = means(cells, meta, keys, c)
        deltas.append(mi - mc)
        labels.append(RULE_SHORT.get(c[1], "") + ("\non C0 (control)" if c[0] == "C0" else ""))
        colors.append(C_COR)

    x = np.arange(len(deltas))
    ax.bar(x, deltas, color=colors, width=0.68, edgecolor="black", linewidth=0.4)
    base = deltas[LADDER.index(REF)]
    ax.axhline(base, color=C_REF, ls="--", lw=1.2, zorder=0)
    ax.text(len(LADDER), base + 0.006, "production baseline %.3f" % base,
            ha="center", va="bottom", fontsize=8.5, color=C_REF)
    for xi, d in enumerate(deltas):
        if not np.isnan(d):
            ax.text(xi, d + 0.008, "%.3f" % d, ha="center", fontsize=9,
                    fontweight="bold" if d > base else "normal")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.2)
    ax.set_ylabel("separation  Δ = mean U(incorrect) − mean U(correct)")
    ax.set_title("P(True) separation by probe condition — %d ALFWorld steps, Qwen3.6-35B-A3B\n"
                 "left: what the probe SEES   |   right: a decision rule added to the production prompt"
                 % len(keys), fontsize=11)
    ax.set_ylim(0, max(d for d in deltas if not np.isnan(d)) * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(handles=[Patch(facecolor=C_INC, label="context ablation"),
                       Patch(facecolor=C_HL, label="pre-hindsight (needs the outcome)"),
                       Patch(facecolor=C_REF, label="production prompt"),
                       Patch(facecolor=C_COR, label="rule injection")],
              fontsize=8.5, frameon=False, ncol=4, loc="upper left")
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


# --------------------------------------------------------------------------- fig 2

def fig_dumbbell(cells, meta, keys, out):
    """A Delta can grow two ways: the probe gets more suspicious of ERRORS (good), or it gets
    more suspicious of everything and the errors merely move further (much less good). The
    dumbbell shows which one each condition did."""
    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    ys = np.arange(len(CONDS))[::-1]
    for y, c in zip(ys, CONDS):
        mi, mc = means(cells, meta, keys, c)
        ax.plot([mc, mi], [y, y], color="#bbbbbb", lw=2.2, zorder=1)
        ax.scatter([mc], [y], color=C_COR, s=62, zorder=2)
        ax.scatter([mi], [y], color=C_INC, s=62, zorder=2)
        ax.text(max(mi, mc) + 0.018, y, "Δ %.3f" % (mi - mc), va="center", fontsize=8.6,
                fontweight="bold" if c in (("C5", "R0"), ("C3", "R2")) else "normal")
    ax.set_yticks(ys)
    ax.set_yticklabels(["%s/%s" % c for c in CONDS], fontsize=9)
    ax.set_xlabel("mean U   (0 = certain the step is right, 1 = certain it is wrong)")
    allm = [v for c in CONDS for v in means(cells, meta, keys, c)]
    ax.set_xlim(min(allm) - 0.05, max(allm) + 0.16)      # data-driven: a fixed lower bound clipped points
    ax.axhline(len(CONDS) - 7.5, color="black", lw=0.7, ls=":")
    ref_i, ref_c = means(cells, meta, keys, REF)
    c5_i, c5_c = means(cells, meta, keys, ("C5", "R0"))
    c6_i, c6_c = means(cells, meta, keys, ("C6", "R0"))
    ax.set_title("Where each condition's separation comes from\n"
                 "vs production: C5 moves errors %+.3f / correct %+.3f | "
                 "C6 moves errors %+.3f / correct %+.3f"
                 % (c5_i - ref_i, c5_c - ref_c, c6_i - ref_i, c6_c - ref_c), fontsize=11)
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=C_INC, label="judge-incorrect steps"),
                       plt.Line2D([], [], marker="o", ls="", color=C_COR, label="judge-correct steps")],
              fontsize=9, frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


# --------------------------------------------------------------------------- fig 3

def fig_heatmap(cells, meta, keys, out):
    M = np.array([[cells.get((k, c), np.nan) for c in CONDS] for k in keys])
    fig, ax = plt.subplots(figsize=(10.5, 7.4))
    im = ax.imshow(M, cmap="RdYlBu_r", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(CONDS)))
    ax.set_xticklabels(["%s/%s" % c for c in CONDS], fontsize=8.6, rotation=45, ha="right")
    big = len(keys) > 40           # per-cell numbers and per-row labels stop being legible
    if big:
        # label the stratum bands instead of every row
        ax.set_yticks([])
        start = 0
        for s in STRATUM_ORDER:
            n = sum(1 for k in keys if meta[k]["stratum"] == s)
            if not n:
                continue
            ax.text(-0.62, start + n / 2 - 0.5, "%s (n=%d)" % (s, n), rotation=90,
                    va="center", ha="center", fontsize=8.5, family="monospace",
                    color=C_INC if s in ("loop", "inadmissible", "other") else C_COR)
            if start:
                ax.axhline(start - 0.5, color="black", lw=0.6, alpha=0.5)
            start += n
    else:
        ax.set_yticks(range(len(keys)))
        ax.set_yticklabels(["%-13s %s" % (meta[k]["stratum"], str(k[0])[:22]) for k in keys],
                           fontsize=7.2, family="monospace")
        for i in range(len(keys)):
            for j in range(len(CONDS)):
                if not np.isnan(M[i, j]):
                    ax.text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=6.4,
                            color="white" if (M[i, j] > 0.72 or M[i, j] < 0.18) else "black")
    n_inc = sum(1 for k in keys if meta[k]["label"] == 1)
    ax.axhline(n_inc - 0.5, color="black", lw=2)
    ax.axvline(6.5, color="black", lw=1.6, ls=":")
    # colour the row labels by judge verdict instead of writing rotated text into the margin,
    # which collided with the task names
    if not big:
        for i, t in enumerate(ax.get_yticklabels()):
            t.set_color(C_INC if meta[keys[i]]["label"] == 1 else C_COR)
    if not big:                     # at large n the band labels occupy this margin instead
        ax.set_ylabel("judge-INCORRECT (red)  /  judge-CORRECT (blue)", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.72, label="U = 1 − P(True)   (higher = more uncertain)")
    ax.set_title("Every step, every condition (n=%d x %d)%s"
                 % (len(keys), len(CONDS),
                    ", grouped by stratum" if big else ". Read this before the means."),
                 fontsize=11)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


# --------------------------------------------------------------------------- fig 4

def fig_hindsight(cells, meta, keys, out):
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 5.4), sharey=True)
    for ax, tgt, title in zip(axes, [("C5", "R0"), ("C6", "R0")],
                              ["C5 — production + the action's OUTCOME",
                               "C6 — C5 + the agent's own next step"]):
        for k in keys:
            if (k, REF) not in cells or (k, tgt) not in cells:
                continue
            lab = meta[k]["label"]
            dense = len(keys) > 40
            ax.plot([0, 1], [cells[(k, REF)], cells[(k, tgt)]],
                    color=C_INC if lab else C_COR, alpha=0.14 if dense else 0.55,
                    lw=0.7 if dense else 1.3, marker="" if dense else "o", ms=3.6)
        for lab, col in ((1, C_INC), (0, C_COR)):
            a = _mean([cells[(k, REF)] for k in keys if meta[k]["label"] == lab])
            b = _mean([cells[(k, tgt)] for k in keys if meta[k]["label"] == lab])
            ax.plot([0, 1], [a, b], color=col, lw=3.6, marker="o", ms=8, zorder=5)
            ax.text(1.04, b, "%+.3f" % (b - a), color=col, fontsize=10, fontweight="bold",
                    va="center")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["production\n(C3/R0)", title.split(" — ")[0]])
        ax.set_xlim(-0.18, 1.30)
        ax.set_title(title, fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("U = 1 − P(True)")
    fig.suptitle("Pre-hindsight: showing the probe what the action actually produced\n"
                 "thick lines = stratum means, annotated with the mean shift; the useful "
                 "condition is the one that moves RED much more than BLUE", fontsize=11)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


# --------------------------------------------------------------------------- fig 5

def fig_rule_stratum(cells, meta, keys, out):
    fig, ax = plt.subplots(figsize=(10.2, 5.4))
    rules = ["R1", "R2", "R3"]
    w = 0.26
    x = np.arange(len(STRATUM_ORDER))
    for i, rl in enumerate(rules):
        vals = [paired(cells, keys, ("C3", rl), REF,
                       pred=lambda k, s=s: meta[k]["stratum"] == s)[0] for s in STRATUM_ORDER]
        ax.bar(x + (i - 1) * w, vals, width=w, label=RULE_SHORT[rl].replace("\n", " "),
               color=["#95a5a6", "#c0392b", "#f1c40f"][i], edgecolor="black", linewidth=0.4)
    decoy = paired(cells, keys, ("C3", "R3"), REF)[0]
    ax.axhline(decoy, color="#f39c12", ls="--", lw=1.4)
    ax.text(len(STRATUM_ORDER) - 0.55, decoy - 0.006,
            "decoy floor (%.3f) — the effect of merely STATING a rule" % decoy,
            ha="right", va="top", fontsize=8.6, color="#b9770e")
    ax.set_xticks(x)
    ax.set_xticklabels(["%s\n(%s)" % (s, "incorrect" if s in ("loop", "inadmissible", "other")
                                      else "CORRECT") for s in STRATUM_ORDER], fontsize=9)
    ax.set_ylabel("median per-step ΔU vs production prompt")
    # Subtitle computed from the data: at n=20 R2 moved revisits MORE than loops, at n=300 it is
    # the other way round. A hardcoded claim here would have silently become false.
    r2_loop = paired(cells, keys, ("C3", "R2"), REF, pred=lambda k: meta[k]["stratum"] == "loop")[0]
    r2_rev = paired(cells, keys, ("C3", "R2"), REF, pred=lambda k: meta[k]["stratum"] == "revisit")[0]
    ax.set_title("Rule injection by error type — the false-positive test\n"
                 "R2 (\"repeats are probably wrong\"): loop errors %+.3f, but legitimate "
                 "revisits — which are CORRECT — %+.3f" % (r2_loop, r2_rev), fontsize=11)
    ax.axhline(0, color="black", lw=0.8)
    ax.legend(fontsize=9, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


# --------------------------------------------------------------------------- fig 6

def _probe_module():
    """Reuse the sweep's own AUROC / clustered-bootstrap code rather than reimplementing it
    (module-level imports there are stdlib only; openai is imported inside the run command)."""
    import importlib.util
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src",
                     "ptrue_context_rule_probe.py")
    spec = importlib.util.spec_from_file_location("ctxrule_probe", os.path.normpath(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def paired_dauroc(M, cells, meta, keys, ca, cb, n_boot=2000, seed=7):
    """CI on AUROC(ca) − AUROC(cb) with the SAME resampled episodes in both arms."""
    import random as _r
    by = {}
    for k in keys:
        by.setdefault(k[0], []).append(k)
    tasks, rng, out = sorted(by), _r.Random(seed), []
    for _ in range(n_boot):
        ks = []
        for _ in range(len(tasks)):
            ks.extend(by[tasks[rng.randrange(len(tasks))]])
        a = M._auroc([(cells[(k, ca)], meta[k]["label"]) for k in ks if (k, ca) in cells])
        b = M._auroc([(cells[(k, cb)], meta[k]["label"]) for k in ks if (k, cb) in cells])
        if a is not None and b is not None:
            out.append(a - b)
    out.sort()
    return statistics.fmean(out), out[int(0.025 * len(out))], out[int(0.975 * len(out))]


def fig_auroc(cells, meta, keys, out):
    M = _probe_module()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6),
                                   gridspec_kw={"width_ratios": [1.15, 1]})

    ys = np.arange(len(CONDS))[::-1]
    for y, c in zip(ys, CONDS):
        pairs, by_task = [], {}
        for k in keys:
            if (k, c) in cells:
                pairs.append((cells[(k, c)], meta[k]["label"]))
                by_task.setdefault(k[0], []).append((cells[(k, c)], meta[k]["label"]))
        au = M._auroc(pairs)
        lo, hi = M._auroc_ci(by_task)
        col = C_HL if c[0] in ("C5", "C6") else (C_REF if c == REF else
                                                 (C_COR if c[1] != "R0" else C_INC))
        ax1.errorbar([au], [y], xerr=[[au - lo], [hi - au]], fmt="o", color=col,
                     ms=7, capsize=3.5, lw=1.6)
        ax1.text(hi + 0.008, y, "%.3f" % au, va="center", fontsize=8.4)
    ax1.axvline(0.5, color="black", ls="--", lw=1, zorder=0)
    ax1.text(0.5, len(CONDS) - 0.4, "chance", ha="center", fontsize=8.4)
    ax1.set_yticks(ys); ax1.set_yticklabels(["%s/%s" % c for c in CONDS], fontsize=9)
    ax1.set_xlabel("AUROC (positive class = judge-incorrect)")
    ax1.set_title("Ranking performance, 95% trajectory-clustered CI", fontsize=10.5)
    ax1.spines[["top", "right"]].set_visible(False); ax1.grid(axis="x", alpha=0.25)

    comps = [(("C6", "R0"), REF, "C6 − production"), (("C5", "R0"), REF, "C5 − production"),
             (("C3", "R2"), REF, "R2 − production"), (("C3", "R1"), REF, "R1 − production"),
             (("C3", "R2"), ("C3", "R3"), "R2 − decoy R3"),
             (("C6", "R0"), ("C5", "R0"), "C6 − C5"),
             (("C3", "R3"), REF, "decoy R3 − production"),
             (("C2", "R0"), REF, "C2 − production")]
    ys2 = np.arange(len(comps))[::-1]
    for y, (ca, cb, name) in zip(ys2, comps):
        d, lo, hi = paired_dauroc(M, cells, meta, keys, ca, cb)
        sig = lo > 0 or hi < 0
        ax2.errorbar([d], [y], xerr=[[d - lo], [hi - d]], fmt="o",
                     color="#1e8449" if sig else "#7f8c8d", ms=7, capsize=3.5, lw=1.6)
        ax2.text(hi + 0.006, y, "%+.3f%s" % (d, "  *" if sig else ""), va="center", fontsize=8.4,
                 fontweight="bold" if sig else "normal")
    ax2.axvline(0, color="black", lw=1.1)
    ax2.set_yticks(ys2); ax2.set_yticklabels([c[2] for c in comps], fontsize=9)
    ax2.set_xlabel("Δ AUROC (paired, same episodes resampled)")
    ax2.set_title("Paired differences — * = 95% CI excludes 0", fontsize=10.5)
    ax2.spines[["top", "right"]].set_visible(False); ax2.grid(axis="x", alpha=0.25)
    fig.suptitle("Does the prompt change discrimination? (n=%d steps)" % len(keys), fontsize=12)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", default="result/ctxrule/ptrue_ctxrule_e1b.jsonl")
    ap.add_argument("--outdir", default="result/ctxrule/figures")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    cells, meta, keys = load(a.records)
    print("loaded %d steps, %d filled cells" % (len(keys), len(cells)))
    for name, fn in [("fig1_separation", fig_separation), ("fig2_dumbbell", fig_dumbbell),
                     ("fig3_heatmap", fig_heatmap), ("fig4_hindsight", fig_hindsight),
                     ("fig5_rule_stratum", fig_rule_stratum), ("fig6_auroc", fig_auroc)]:
        p = os.path.join(a.outdir, name + ".png")
        fn(cells, meta, keys, p)
        print("wrote", p)


if __name__ == "__main__":
    main()
