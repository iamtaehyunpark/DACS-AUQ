#!/usr/bin/env python3
"""The label input for the Phase-5 reruns — and nothing else.

`crossprobe_matrix_auroc.py`, `uncertainty_levels.py` and `percentile_consistency.py`
all consume labels through one function that returns

    {(task_id, step_idx): fraction_of_judges_voting_CORRECT}

with the positive class being *incorrect*. Gate 5 must rerun those scripts unmodified
except for the label column, so this module supplies a drop-in replacement producing
the identical shape from `labels_gate1.csv`. Environment labels are hard, so the
fraction is 0.0 (incorrect) or 1.0 (correct); every downstream statistic — soft AUROC,
Youden, lift@k — consumes it exactly as before.

Two coverage modes, per the brief:
  restricted  only steps y_env can label. Unlabelled steps are absent from the dict,
              which the existing callers already skip.
  full        every step. Unlabelled steps enter as the negative class (correct, 1.0)
              — "unlabelled as negative-class-with-noise".
"""
import collections
import csv


def _cast_task_id(dataset, raw):
    """HotpotQA task_ids are ints in the JSONL and strings out of the CSV."""
    if dataset == "hotpotqa":
        try:
            return int(raw)
        except (TypeError, ValueError):
            return raw
    return raw


def load_env_labels(csv_path, dataset, model, mode="restricted", column="y_env"):
    """Judge-shaped label dict for one arm, sourced from the gate-1 label file."""
    if mode not in ("restricted", "full"):
        raise ValueError("mode must be 'restricted' or 'full', got %r" % mode)
    out = {}
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["dataset"] != dataset or r["model"] != model:
                continue
            key = (_cast_task_id(dataset, r["task_id"]), int(r["step_idx"]))
            v = r.get(column, "")
            if v == "" or v is None:
                if mode == "full":
                    out[key] = 1.0        # unlabelled -> negative class (correct)
                continue
            # y_* columns are 1 = incorrect. The judge-shaped value is the
            # complementary fraction-voting-CORRECT.
            out[key] = 0.0 if int(float(v)) == 1 else 1.0
    return out


def load_ensemble_labels(csv_path, dataset, model, mode="restricted", column="y_env"):
    """The existing 3-judge label restricted to the y_env-labelable step universe.

    This exists so the side-by-side comparison is not confounded: scoring the ensemble
    over all judged steps and y_env over its own smaller support would mix a label
    change with a step-set change. Soft fractions are preserved, never thresholded, so
    the statistic is identical to the published one — only the support differs.
    """
    out = {}
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["dataset"] != dataset or r["model"] != model:
                continue
            if mode == "restricted" and r.get(column, "") in ("", None):
                continue
            key = (_cast_task_id(dataset, r["task_id"]), int(r["step_idx"]))
            v = r.get("judge_frac_correct", "")
            if v == "" or v is None:
                if mode == "full":
                    out[key] = 1.0
                continue
            out[key] = float(v)
    return out


def coverage(csv_path, dataset, model, column="y_env"):
    """(n_steps, n_labelled, n_incorrect) for the coverage tables."""
    n = lab = inc = 0
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["dataset"] != dataset or r["model"] != model:
                continue
            n += 1
            v = r.get(column, "")
            if v not in ("", None):
                lab += 1
                inc += int(float(v)) == 1
    return n, lab, inc


def index_by_arm(csv_path):
    """All (dataset, model) pairs present, in file order."""
    seen = collections.OrderedDict()
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            seen.setdefault((r["dataset"], r["model"]), 0)
            seen[(r["dataset"], r["model"])] += 1
    return seen
