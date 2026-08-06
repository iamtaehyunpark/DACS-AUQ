#!/usr/bin/env python3
"""S1 label layer — A30 constructs over the gate-1 label file.

Spec: docs/specs/S1_SPEC.md §0.  Every S1 sub-stage joins scores to labels through
here, so the construct definitions exist in exactly one place.

Label convention matches the banked gate-2 code: **y = 1 means INCORRECT** (the
positive class), y = 0 means correct.  load_labels() in gate2b_cut_transfer.py
returns judge_correct_frac and callers test `< 0.5`; this module returns y directly
plus a weight, so soft-weighting stays available where a construct supports it.
"""
import collections
import csv
import os

# Registered in S1_SPEC.md §0.  A stratum varies its POSITIVE class and holds the
# NEGATIVE class fixed: Tier A never emits "correct", so negatives can only come
# from Tier B (or from the ensemble, for judgment-bearing constructs).
CONSTRUCTS = ["violation", "outcome", "judgment", "y_env", "violation+judgment"]

# Constructs whose negative class is Tier-B-correct.  Flagged because they share one
# small pool (<=5,183 corpus-wide) -- the spec accepts their wide CIs in advance.
SMALL_NEGATIVE_POOL = {"violation", "outcome"}


def _viol(x):
    return any(x.get(k) == "1" for k in ("A1", "A2", "A3"))


def label_for(x, construct):
    """(y, weight) for one label row under one construct, or (None, None) if the
    construct does not label this step.  y = 1 means incorrect."""
    tb = x.get("y_tier_b", "")
    ens = x.get("y_ensemble", "")
    v = _viol(x)

    if construct == "violation":
        if v:
            return 1, 1.0
        if tb == "0":
            return 0, 1.0
        return None, None

    if construct == "outcome":
        if x.get("A4") == "1" or tb == "1":
            return 1, 1.0
        if tb == "0":
            return 0, 1.0
        return None, None

    if construct == "judgment":
        if ens == "":
            return None, None
        # Soft weight from the 3-judge vote share where present, mirroring the L1
        # soft-AUROC the banked crossprobe tables use.  frac is P(correct).
        try:
            frac = float(x.get("judge_frac_correct", "") or "")
        except ValueError:
            frac = None
        y = 1 if ens == "1" else 0
        w = 1.0 if frac is None else (1.0 - frac if y == 1 else frac)
        # A zero weight would silently drop the step; keep it labelled but minimal.
        return y, max(w, 1e-6)

    if construct == "y_env":
        ye = x.get("y_env", "")
        if ye == "":
            return None, None
        return (1 if ye == "1" else 0), 1.0

    if construct == "violation+judgment":
        if v:
            return 1, 1.0
        if ens == "":
            return None, None
        return (1 if ens == "1" else 0), 1.0

    raise ValueError("unknown construct %r" % (construct,))


def load(labels_csv, construct, in_matrix_only=True):
    """-> {(dataset, model): {(task_id, step_idx): (y, w)}}

    task_id/step_idx are returned as the SAME types the score loader produces:
    Keys are coerced to the SAME types the score loader produces.  The label CSV is
    all text; the JSONL scores are typed, and the two datasets differ from each other:
    ALFWorld task_id is a string ("look_at_obj_in_light-AlarmClock-.../trial_..."),
    HotpotQA task_id is an int (1009), and step_idx is an int in both.  A str/int
    mismatch joins ZERO rows, and a cell with zero rows simply does not appear -- which
    is how the first S1 run lost all 25 HotpotQA cells and still printed a clean
    31-cell table.  Coerce once, here; callers assert coverage.
    """
    if not os.path.exists(labels_csv):
        raise SystemExit("S1: labels file absent: %s" % labels_csv)
    out = collections.defaultdict(dict)
    with open(labels_csv) as f:
        for x in csv.DictReader(f):
            if in_matrix_only and x.get("in_matrix") != "1":
                continue
            y, w = label_for(x, construct)
            if y is None:
                continue
            try:
                step = int(x["step_idx"])
            except (KeyError, ValueError):
                continue
            t = x["task_id"]
            tid = int(t) if t.lstrip("-").isdigit() else t
            out[(x["dataset"], x["model"])][(tid, step)] = (y, w)
    return out


def coverage(labels_csv, in_matrix_only=True):
    """Per-construct, per-arm (n, n_pos, n_neg) -- inventory for the summary."""
    rows = []
    for c in CONSTRUCTS:
        d = load(labels_csv, c, in_matrix_only)
        for (ds, m), steps in sorted(d.items()):
            pos = sum(1 for y, _ in steps.values() if y == 1)
            rows.append({"construct": c, "dataset": ds, "model": m,
                         "n": len(steps), "n_pos": pos, "n_neg": len(steps) - pos})
    return rows


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--all-arms", action="store_true")
    a = ap.parse_args()
    print("%-20s %-9s %-26s %7s %7s %7s" % ("construct", "dataset", "model",
                                            "n", "n_pos", "n_neg"))
    for r in coverage(a.labels, not a.all_arms):
        print("%-20s %-9s %-26s %7d %7d %7d"
              % (r["construct"], r["dataset"], r["model"][:26], r["n"],
                 r["n_pos"], r["n_neg"]))
