"""Coverage gate for completed HotpotQA probe and judge acquisition outputs.

Usage:
  python audit_hotpot_outputs.py <uq.jsonl> <probes.jsonl> <judge.jsonl> <decoupled|entangled>
"""
from __future__ import annotations

import collections
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    if len(sys.argv) != 5 or sys.argv[4] not in ("decoupled", "entangled"):
        sys.exit(
            "usage: python audit_hotpot_outputs.py "
            "<uq.jsonl> <probes.jsonl> <judge.jsonl> <decoupled|entangled>"
        )
    uq_path, probe_path, judge_path, arm = sys.argv[1:]
    uq, probe_records, judge_records = load(uq_path), load(probe_path), load(judge_path)
    steps = [r for r in uq if r.get("kind") == "step"]
    failures = []

    all_keys = {(r["task_id"], r["step_idx"]) for r in steps}
    action_keys = {
        (r["task_id"], r["step_idx"])
        for r in steps
        if (r.get("action_parsed") or "").strip()
    }

    by_probe = collections.defaultdict(list)
    for record in probe_records:
        key = (
            record.get("probe_kind"),
            record.get("stage"),
            record.get("task_id"),
            record.get("step_idx"),
        )
        by_probe[key].append(record)

    def keys_for(kind, stage):
        return {
            (task_id, step_idx)
            for probe_kind, probe_stage, task_id, step_idx in by_probe
            if probe_kind == kind and probe_stage == stage
        }

    expected = {
        ("ptrue", "thought"): all_keys,
        ("ptrue", "action"): action_keys,
        ("ptrue", "response"): action_keys,
        ("sep_verbalized", "thought"): all_keys,
        ("sep_verbalized", "action"): action_keys,
        ("posthoc_numeric", "thought"): all_keys,
        ("posthoc_numeric", "action"): action_keys,
    }
    if arm == "decoupled":
        expected[("qt_extract", "thought")] = all_keys
        expected[("targeted", "thought")] = all_keys

    for (kind, stage), wanted in expected.items():
        got = keys_for(kind, stage)
        if got != wanted:
            failures.append(
                "%s/%s coverage mismatch: expected %d keys, got %d"
                % (kind, stage, len(wanted), len(got))
            )
        duplicates = [
            key
            for key, values in by_probe.items()
            if key[0] == kind and key[1] == stage and len(values) != 1
        ]
        if duplicates:
            failures.append("%s/%s contains duplicate records" % (kind, stage))

    unexpected_targeted = [
        r
        for r in probe_records
        if arm == "entangled" and r.get("probe_kind") in ("targeted", "qt_extract")
    ]
    if unexpected_targeted:
        failures.append("entangled output contains targeted q_t probes")

    for record in probe_records:
        if record.get("domain") != "hotpotqa":
            failures.append("probe record missing domain=hotpotqa")
            break
        if record.get("probe_kind") == "targeted" and record.get("record") is None:
            # A visible q_t-extraction failure stub is valid and never imputed.
            continue
        nested = record.get("record")
        if not nested or not nested.get("gen_logprobs"):
            failures.append("probe record missing raw generated-token logprobs")
            break
        if any(
            len(token.get("top") or []) < 20
            for token in nested.get("gen_logprobs", [])
        ):
            failures.append("probe token has fewer than 20 top-logprob alternatives")
            break

    response_records = [
        r
        for r in probe_records
        if r.get("probe_kind") == "ptrue" and r.get("stage") == "response"
    ]
    if any(r.get("metric_field") != "U_R_ptrue" for r in response_records):
        failures.append("whole-response P(True) does not use metric_field=U_R_ptrue")

    judge_keys = {
        (r.get("task_id"), r.get("step_idx"))
        for r in judge_records
        if r.get("kind") == "judge"
    }
    if judge_keys != action_keys:
        failures.append(
            "judge coverage mismatch: expected %d non-empty-action steps, got %d"
            % (len(action_keys), len(judge_keys))
        )
    if any(not r.get("votes") for r in judge_records):
        failures.append("judge record missing votes")

    print(
        "=== audit_hotpot_outputs: %s (%d steps, %d probes, %d judge labels) ==="
        % (arm, len(steps), len(probe_records), len(judge_records))
    )
    for failure in failures:
        print("  FAIL " + failure)
    print("GATE: %s" % ("FAIL" if failures else "PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
