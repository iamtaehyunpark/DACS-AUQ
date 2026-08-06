#!/usr/bin/env python3
"""Gate-1 Phase 4 — assemble the label file of record.

Inputs
  reports/gate1/tier_a_steps.csv       Phase 1 (every step, every arm)
  reports/gate1/tier_b_alfworld.csv    Phase 3 replay (ALFWorld only)

Labels
  y_env      PRIMARY. Tier A union Tier B. Tier A wins on conflict; every conflict is
             counted and reported. 1 = incorrect, 0 = correct, blank = not labelable.
  y_suffix   SECONDARY, sensitivity only. Every step after the last productive step of
             a FAILED episode. Computed in Phase 1.
  y_ensemble SECONDARY. The existing 3-judge label, never deleted.

HotpotQA Tier B is partial by Phase 0's STOP finding: `supporting_facts` are not present
in the vendored corpus and exist nowhere on the machine, so the search-step rule
("retrieved a gold supporting document") cannot be evaluated and those steps are left
unlabelable with an explicit reason. The ANSWER-step rule is unaffected and is applied
here: a `Finish[...]` step is correct iff the episode's exact match is 1.

  gate1_assemble.py [--out-csv reports/gate1/labels_gate1.csv] [--parquet ...]
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

_FINISH_RE = re.compile(r"^finish\[", re.IGNORECASE)

OUT_COLUMNS = [
    # keys
    "run_id", "task_id", "step_idx", "dataset", "model", "in_matrix", "action_parsed",
    # primary label + provenance
    "y_env", "y_env_source", "y_env_conflict",
    # tier A provenance
    "y_tier_a", "A1", "A2", "A3", "A4", "tier_a_rules",
    # tier B provenance
    "y_tier_b", "b_reason", "plan_len_before", "plan_len_after", "replay_diverged",
    # secondary labels
    "y_suffix", "y_ensemble", "judge_frac_correct", "judge_n_valid", "judge_present",
    # coverage
    "labelable_env", "unlabelable_reason",
    # environment context carried for downstream filtering
    "U_verbalized", "in_admissible", "obs_changed", "loop_flag", "skip_reasons",
    "episode_present", "episode_success", "terminal_reason", "episode_em", "episode_f1",
    "productive",
]


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _truthy(v):
    """`em` is logged as a JSON bool in some arms and 0/1 in others; both reach the
    CSV as text. Returns None when the value is absent or unrecognised."""
    s = str(v).strip().lower()
    if s in ("true", "1", "1.0"):
        return 1
    if s in ("false", "0", "0.0"):
        return 0
    return None


def hotpot_tier_b(row):
    """(y, reason) for a HotpotQA step under the rules that survive Phase 0's STOP."""
    action = (row.get("action_parsed") or "").strip()
    if _FINISH_RE.match(action):
        em = _truthy(row.get("episode_em", ""))
        if em is None:
            return "", "B_hotpot_answer_no_episode_record"
        # Exact match is the pre-registered answer rule; F1 travels in the file as
        # episode_f1 for anyone who wants the graded version.
        return (0 if em == 1 else 1), "B_hotpot_answer_em"
    if not action:
        return "", "B_hotpot_empty_action"
    # Search / Lookup: blocked by the missing gold supporting-fact ids.
    return "", "B_hotpot_search_blocked_no_gold_supporting_facts"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier-a", default="reports/gate1/tier_a_steps.csv")
    ap.add_argument("--tier-b", default="reports/gate1/tier_b_alfworld.csv")
    ap.add_argument("--out-csv", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--parquet", default="reports/gate1/labels_gate1.parquet")
    ap.add_argument("--out-json", default="reports/gate1/phase4_coverage.json")
    args = ap.parse_args()

    a_rows = read_csv(args.tier_a)
    b_index = {}
    if os.path.exists(args.tier_b):
        for r in read_csv(args.tier_b):
            b_index[(r["dataset"], r["model"], r["task_id"], int(r["step_idx"]))] = r
    else:
        sys.stderr.write("WARNING: no Tier-B file at %s\n" % args.tier_b)

    out = []
    stats = collections.defaultdict(collections.Counter)
    for r in a_rows:
        key = (r["dataset"], r["model"], str(r["task_id"]), int(r["step_idx"]))
        arm = "%s/%s" % (r["dataset"], r["model"])
        b = b_index.get(key)

        ya = 1 if r["y_tier_a"] == "1" else None
        if r["dataset"] == "alfworld":
            if b is None:
                yb, breason = None, "B_no_replay_row"
            else:
                yb = int(b["y_tier_b"]) if b["y_tier_b"] != "" else None
                breason = b["b_reason"]
        else:
            yb_raw, breason = hotpot_tier_b(r)
            yb = None if yb_raw == "" else int(yb_raw)

        # A overrides B. A conflict is A=incorrect while B=correct; it is logged, and
        # A's verdict stands, because A is a direct environment rejection while B is
        # an inference from plan length.
        conflict = int(ya == 1 and yb == 0)
        if ya is not None:
            y, src = ya, ("both" if yb is not None else "tier_a")
        elif yb is not None:
            y, src = yb, "tier_b"
        else:
            y, src = None, ""

        if y is None:
            unlabelable = breason or "no_rule_fired"
        else:
            unlabelable = ""

        stats[arm]["steps"] += 1
        stats[arm]["labelled"] += int(y is not None)
        stats[arm]["incorrect"] += int(y == 1)
        stats[arm]["correct"] += int(y == 0)
        stats[arm]["conflicts"] += conflict
        stats[arm]["src_" + (src or "none")] += 1
        if y is None:
            stats[arm]["unlab_" + unlabelable] += 1

        row = dict(r)
        row.update({
            "y_env": "" if y is None else y,
            "y_env_source": src,
            "y_env_conflict": conflict,
            "y_tier_b": "" if yb is None else yb,
            "b_reason": breason,
            "plan_len_before": (b or {}).get("plan_len_before", ""),
            "plan_len_after": (b or {}).get("plan_len_after", ""),
            "replay_diverged": (b or {}).get("replay_diverged", ""),
            "labelable_env": int(y is not None),
            "unlabelable_reason": unlabelable,
        })
        out.append({k: row.get(k, "") for k in OUT_COLUMNS})

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        w.writeheader()
        w.writerows(out)

    with open(args.out_json, "w") as f:
        json.dump({k: dict(v) for k, v in sorted(stats.items())}, f, indent=2)

    wrote_parquet = write_parquet(out, args.parquet)
    print("%-42s %7s %7s %7s %7s %6s" % ("arm", "steps", "lab", "inc", "cor", "confl"))
    for arm, c in sorted(stats.items()):
        print("%-42s %7d %7d %7d %7d %6d" % (
            arm, c["steps"], c["labelled"], c["incorrect"], c["correct"], c["conflicts"]))
    print("wrote %s (%d rows)%s" % (args.out_csv, len(out),
                                    " and " + args.parquet if wrote_parquet else
                                    " — parquet SKIPPED (no pyarrow/pandas)"))


def write_parquet(rows, path):
    try:
        import pandas as pd
    except ImportError:
        return False
    df = pd.DataFrame(rows)
    # Keep the label columns nullable-integer rather than float, so a blank stays a
    # blank instead of becoming NaN that later reads as 0.0.
    for c in ("y_env", "y_tier_a", "y_tier_b", "y_suffix", "y_ensemble", "A1", "A2",
              "A3", "A4", "in_matrix", "labelable_env", "y_env_conflict", "step_idx",
              "judge_present", "episode_present", "episode_success", "productive",
              "replay_diverged", "plan_len_before", "plan_len_after", "episode_em"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in ("judge_frac_correct", "judge_n_valid", "U_verbalized", "episode_f1"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    try:
        df.to_parquet(path, index=False)
    except Exception as e:
        sys.stderr.write("parquet write failed (%s); csv is authoritative\n" % e)
        return False
    return True


if __name__ == "__main__":
    main()
