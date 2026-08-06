#!/usr/bin/env python3
"""Gate-1 Phases 1 and 2 — Tier-A environment labels and the ensemble circularity audit.

Phase 1 (deterministic, log-scan only). Tier A labels a step INCORRECT if any of:
  A1  ALFWorld: in_admissible == false. HotpotQA: the action does not match the
      Search|Lookup|Finish[...] grammar (or in_admissible == false; the two never
      disagree in this corpus — Phase 0 §0.1).
  A2  ALFWorld only: obs_changed == false AND obs == "Nothing happens.". An
      informative-but-static observation is deliberately NOT caught here.
  A3  exact repeat of (state_hash, action_parsed) earlier in the same episode
      (ALFWorld) / of the query text (HotpotQA).
  A4  HotpotQA only: a search that loaded no page ("Could not find ...", or a
      Lookup that returned "No more results.").
Tier A produces ONLY incorrect labels; the absence of a flag is NOT a correct label.
Multi-label is allowed and the firing sub-rules are recorded per step.

Steps the tau pipeline skipped (tau_unrecognized_action, invalid_action_syntax) are
labelled and included: an unrecognized action IS evidence of an incorrect step, and
dropping them would bias the evaluation easy.

Phase 2. Over the Tier-A-incorrect steps — where the environment has already settled
the answer — measure how often the 3-judge ensemble said "correct". That is a direct
read of ensemble label error on steps with certain ground truth.

  gate1_tier_a.py [--pivot DIR] [--out-csv ...] [--out-md ...]
"""
import argparse
import collections
import csv
import json
import os
import sys

import gate1_manifest

from gate1_inventory import (MATRIX_TARGETS, hotpot_zero_result, iter_records,
                             tier_a_flags)

# Written to the per-step table; Phase 4 adds the Tier-B and assembled columns.
COLUMNS = [
    "dataset", "model", "in_matrix", "run_id", "task_id", "step_idx", "action_parsed",
    "A1", "A2", "A3", "A4", "tier_a_rules", "y_tier_a",
    "in_admissible", "obs_changed", "loop_flag", "skip_reasons", "U_verbalized",
    "judge_present", "judge_n_valid", "judge_frac_correct", "y_ensemble",
    "episode_present", "episode_success", "terminal_reason", "episode_em", "episode_f1",
    "productive", "y_suffix",
]


def load_judge(path, limit_bytes=None):
    """(task_id, step_idx) -> (n_valid, frac_correct, ensemble_incorrect)."""
    out = {}
    if not os.path.exists(path):
        return out
    consumed = 0
    for line in open(path):
        if limit_bytes is not None:
            consumed += len(line.encode("utf-8"))
            if consumed > limit_bytes:
                break
        r = json.loads(line)
        votes = [v.get("incorrect") for v in (r.get("votes") or {}).values()]
        votes = [v for v in votes if v is not None]
        if not votes:
            continue
        frac_correct = sum(1 for v in votes if v == 0) / len(votes)
        out[(r["task_id"], r["step_idx"])] = (len(votes), frac_correct,
                                              r.get("ensemble_incorrect"))
    return out


def scan_arm(dataset, model, arm_dir, pins):
    """Return the per-step rows for one arm, in log order."""
    judge = load_judge(os.path.join(arm_dir, "judge.jsonl"), pins.get("judge.jsonl"))
    steps, episodes = [], {}
    per_ep_seen = collections.defaultdict(set)

    for kind, rec in iter_records(os.path.join(arm_dir, "uq.jsonl"), pins.get("uq.jsonl")):
        if kind == "__meta__":
            continue
        if kind == "episode":
            episodes[rec.get("task_id")] = rec
            continue
        tid = rec.get("task_id")
        fired = tier_a_flags(dataset, rec, per_ep_seen[tid])
        j = judge.get((tid, rec.get("step_idx")))
        row = {
            "dataset": dataset, "model": model,
            "in_matrix": int(model in MATRIX_TARGETS.get(dataset, [])),
            "run_id": rec.get("run_id"), "task_id": tid, "step_idx": rec.get("step_idx"),
            "action_parsed": rec.get("action_parsed"),
            "A1": int(any(f.startswith("A1") for f in fired)),
            "A2": int(any(f.startswith("A2") for f in fired)),
            "A3": int(any(f.startswith("A3") for f in fired)),
            "A4": int(any(f.startswith("A4") for f in fired)),
            "tier_a_rules": "|".join(fired),
            "y_tier_a": 1 if fired else "",       # incorrect, or unlabelled by Tier A
            "in_admissible": rec.get("in_admissible"),
            "obs_changed": rec.get("obs_changed"),
            "loop_flag": rec.get("loop_flag"),
            "skip_reasons": "|".join(rec.get("skip_reasons") or []),
            "U_verbalized": rec.get("U_verbalized"),
            "judge_present": int(j is not None),
            "judge_n_valid": j[0] if j else "",
            "judge_frac_correct": j[1] if j else "",
            "y_ensemble": j[2] if j else "",
            # `productive` is the input to the y_suffix sensitivity label only: a step
            # that moved the environment and tripped no Tier-A rule. Stated explicitly
            # because "productive" is not a logged field.
            "productive": int(bool(rec.get("obs_changed")) and not fired),
        }
        steps.append(row)

    # y_suffix: in a FAILED episode, every step after the last productive one.
    # Episodes with no terminal record have no outcome, so y_suffix is left blank.
    by_ep = collections.defaultdict(list)
    for row in steps:
        by_ep[row["task_id"]].append(row)
    for tid, rows in by_ep.items():
        ep = episodes.get(tid)
        for row in rows:
            row["episode_present"] = int(ep is not None)
            row["episode_success"] = "" if ep is None else int(bool(ep.get("success")))
            row["terminal_reason"] = "" if ep is None else ep.get("terminal_reason")
            # HotpotQA only: the episode outcome is what the Tier-B answer-step rule
            # reads (exact match / F1 against gold). ALFWorld episodes carry neither.
            row["episode_em"] = "" if ep is None else ep.get("em", "")
            row["episode_f1"] = "" if ep is None else ep.get("f1", "")
        if ep is None:
            for row in rows:
                row["y_suffix"] = ""
            continue
        if ep.get("success"):
            for row in rows:
                row["y_suffix"] = 0
            continue
        prod = [r["step_idx"] for r in rows if r["productive"]]
        last = max(prod) if prod else -1
        for row in rows:
            row["y_suffix"] = int(row["step_idx"] > last)
    return steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--out-csv", default="reports/gate1/tier_a_steps.csv")
    ap.add_argument("--out-md", default="reports/gate1/report_phase2_ensemble_audit.md")
    ap.add_argument("--manifest", default="reports/gate1/input_manifest.json")
    args = ap.parse_args()

    all_pins = gate1_manifest.load(args.manifest, args.pivot)

    rows = []
    for dataset in ("alfworld", "hotpotqa"):
        d = os.path.join(args.pivot, dataset)
        if not os.path.isdir(d):
            continue
        for model in sorted(os.listdir(d)):
            arm = os.path.join(d, model)
            if not os.path.isfile(os.path.join(arm, "uq.jsonl")):
                continue
            sys.stderr.write("tier A: %s/%s\n" % (dataset, model))
            sys.stderr.flush()
            pins = {f: all_pins[k] for f in ("uq.jsonl", "judge.jsonl")
                    for k in ["%s/%s/%s" % (dataset, model, f)] if k in all_pins}
            rows.extend(scan_arm(dataset, model, arm, pins))

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    write_audit(rows, args.out_md)
    sys.stderr.write("wrote %s (%d steps) and %s\n" % (args.out_csv, len(rows), args.out_md))


def _pct(n, d):
    return "—" if not d else "%.1f%%" % (100.0 * n / d)


def write_audit(rows, path):
    """Phase 2 — ensemble error on steps the environment has already settled."""
    L = []
    A = L.append
    A("# Gate-1 Phase 2 — ensemble circularity audit\n")
    A("Every step below is **Tier-A incorrect**: the environment rejected the action, "
      "returned nothing, repeated a state, or the action was not a legal call at all. "
      "Ground truth on these steps is certain and needs no judgment. The question is "
      "how often the 3-judge ensemble — the label all current results are scored "
      "against — called them **correct**.\n")
    A("Two readings are given. *Discrete* uses the ensemble's own majority label "
      "(`ensemble_incorrect == 0`). *Soft* is the mean fraction of the 3 judges voting "
      "correct, which is the weighting `crossprobe_matrix_auroc.py` actually uses.\n")

    def block(title, sel):
        A("\n## %s\n" % title)
        A("| dataset | model | Tier-A-incorrect steps | judged | ensemble said CORRECT (discrete) | mean judge frac. correct (soft) |")
        A("|---|---|---|---|---|---|")
        by = collections.defaultdict(list)
        for r in rows:
            if sel(r) and r["y_tier_a"] == 1:
                by[(r["dataset"], r["model"])].append(r)
        tot_n = tot_j = tot_c = 0
        tot_soft = 0.0
        for (ds, m), rs in sorted(by.items()):
            judged = [r for r in rs if r["judge_present"]]
            c = sum(1 for r in judged if r["y_ensemble"] == 0)
            soft = sum(r["judge_frac_correct"] for r in judged)
            A("| %s | %s | %d | %d | %d (%s) | %s |" % (
                ds, m, len(rs), len(judged), c, _pct(c, len(judged)),
                "—" if not judged else "%.3f" % (soft / len(judged))))
            tot_n += len(rs); tot_j += len(judged); tot_c += c; tot_soft += soft
        A("| **ALL** | | **%d** | **%d** | **%d (%s)** | **%s** |" % (
            tot_n, tot_j, tot_c, _pct(tot_c, tot_j),
            "—" if not tot_j else "%.3f" % (tot_soft / tot_j)))
        return tot_c, tot_j, (tot_soft / tot_j if tot_j else None)

    c_all, j_all, s_all = block("All arms", lambda r: True)
    block("Matrix arms only (the 56 cells)", lambda r: r["in_matrix"] == 1)

    A("\n## By firing sub-rule (matrix arms)\n")
    A("| rule | steps | judged | ensemble said CORRECT | mean judge frac. correct |")
    A("|---|---|---|---|---|")
    by_rule = collections.defaultdict(list)
    for r in rows:
        if r["in_matrix"] != 1 or r["y_tier_a"] != 1:
            continue
        for rule in r["tier_a_rules"].split("|"):
            by_rule[rule].append(r)
    for rule, rs in sorted(by_rule.items()):
        judged = [r for r in rs if r["judge_present"]]
        c = sum(1 for r in judged if r["y_ensemble"] == 0)
        soft = sum(r["judge_frac_correct"] for r in judged)
        A("| `%s` | %d | %d | %d (%s) | %s |" % (
            rule, len(rs), len(judged), c, _pct(c, len(judged)),
            "—" if not judged else "%.3f" % (soft / len(judged))))

    A("\n## Unanimity on settled steps (matrix arms)\n")
    A("How the 3 judges split on steps the environment had already decided.\n")
    A("| judges voting CORRECT | steps | share |")
    A("|---|---|---|")
    hist = collections.Counter()
    tot = 0
    for r in rows:
        if r["in_matrix"] != 1 or r["y_tier_a"] != 1 or not r["judge_present"]:
            continue
        hist[round(r["judge_frac_correct"] * r["judge_n_valid"])] += 1
        tot += 1
    for k in sorted(hist):
        A("| %d of 3 | %d | %s |" % (k, hist[k], _pct(hist[k], tot)))

    A("\n## R4 — the number\n")
    A("**%s of judged Tier-A-incorrect steps were labelled CORRECT by the 3-judge "
      "ensemble** (%d of %d, all arms). Soft weighting: mean fraction of judges voting "
      "correct on those steps = **%.3f**.\n"
      % (_pct(c_all, j_all), c_all, j_all, s_all or 0.0))
    A("This is a floor on ensemble label error, not an estimate of it: it is measured "
      "only where the environment supplies certain ground truth, which is the subset of "
      "steps where errors are most blatant.\n")

    # Sensitivity, reported not reinterpreted: A4 is the one Tier-A rule where the
    # environment's verdict and a step-quality verdict can honestly come apart — a
    # well-formed query that simply missed. The pre-registered rule stands; this line
    # shows what the headline number is without it.
    m = [r for r in rows if r["in_matrix"] == 1 and r["y_tier_a"] == 1 and r["judge_present"]]
    noa4 = [r for r in m if r["tier_a_rules"] != "A4_zero_result"]
    c1 = sum(1 for r in m if r["y_ensemble"] == 0)
    c2 = sum(1 for r in noa4 if r["y_ensemble"] == 0)
    A("**A4 sensitivity.** A4 is the only sub-rule where the environment's verdict and a "
      "step-quality verdict can legitimately diverge: a well-formed query that happened "
      "to retrieve nothing is a failed step by the pre-registered rule, but a judge may "
      "reasonably call the *action* sound. The rule is not reinterpreted here — both "
      "numbers are simply reported. Matrix arms, judged Tier-A-incorrect steps: "
      "**%s said correct** (%d of %d) as pre-registered; **%s** (%d of %d) after dropping "
      "the %d steps whose only firing rule is A4.\n"
      % (_pct(c1, len(m)), c1, len(m), _pct(c2, len(noa4)), c2, len(noa4),
         len(m) - len(noa4)))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
