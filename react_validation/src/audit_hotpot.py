"""Regeneration gate for HotpotQA decoupled/entangled UQ acquisition logs.

Usage: python audit_hotpot.py <uq_log.jsonl> <decoupled|entangled>
"""
from __future__ import annotations

import json
import os
import sys

from hotpot_common import valid_action
from hotpot_tau_map import tau_dict


def fail_if(condition, message, failures):
    if condition:
        failures.append(message)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[2] not in ("decoupled", "entangled"):
        sys.exit("usage: python audit_hotpot.py <uq_log.jsonl> <decoupled|entangled>")
    path, arm = sys.argv[1], sys.argv[2]
    with open(path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    calls = [r for r in records if r.get("kind") == "call"]
    steps = [r for r in records if r.get("kind") == "step"]
    episodes = [r for r in records if r.get("kind") == "episode"]
    failures = []
    warnings = []

    fail_if(not calls or not steps or not episodes, "missing call/step/episode records", failures)
    fail_if(
        any(r.get("domain") != "hotpotqa" for r in calls + steps + episodes),
        "records missing domain=hotpotqa",
        failures,
    )
    fail_if(
        any(not c.get("prompt_templated") or not c.get("completion_raw") for c in calls),
        "call missing prompt_templated or completion_raw",
        failures,
    )
    fail_if(
        any("seed" not in (c.get("config") or {}) for c in calls),
        "call missing config.seed",
        failures,
    )
    fail_if(
        any(not c.get("gen_logprobs") for c in calls),
        "call missing generated-token logprobs",
        failures,
    )
    fail_if(
        any(
            len(token.get("top") or []) < 20
            for c in calls
            for token in (c.get("gen_logprobs") or [])
        ),
        "generated token has fewer than 20 top-logprob alternatives",
        failures,
    )

    expected_kinds = {"thought", "action"} if arm == "decoupled" else {"joint"}
    grouped_calls = {}
    for call in calls:
        key = (call.get("run_id"), call.get("task_id"), call.get("step_idx"))
        grouped_calls.setdefault(key, set()).add(call.get("call_kind"))
    step_keys = {
        (step.get("run_id"), step.get("task_id"), step.get("step_idx")) for step in steps
    }
    fail_if(
        set(grouped_calls) != step_keys,
        "call groups and step groups are not one-to-one",
        failures,
    )
    fail_if(
        any(kinds != expected_kinds for kinds in grouped_calls.values()),
        "wrong per-step call kinds for %s arm" % arm,
        failures,
    )

    seed_base = int(os.environ.get("REACT_SEED_BASE", "1000"))
    bad_seeds = 0
    for call in calls:
        offset = 1 if call.get("call_kind") == "action" else 0
        expected = (
            seed_base
            + int(call["task_id"]) * 100000
            + int(call["step_idx"]) * 100
            + offset
        )
        bad_seeds += int(call["config"]["seed"] != expected)
    fail_if(bad_seeds > 0, "%d calls violate the deterministic seed formula" % bad_seeds, failures)

    reconstruction_failures = 0
    for call in calls:
        generated = call.get("gen_logprobs") or []
        raw = call.get("completion_raw") or ""
        spans = call.get("spans") or {}
        for stage in ("thought", "action"):
            span = spans.get(stage)
            if not span:
                continue
            text = "".join(token["token"] for token in generated[span[0] : span[1]])
            if text not in raw and not raw.startswith(text):
                reconstruction_failures += 1
    fail_if(
        reconstruction_failures > 0,
        "%d logged spans do not reconstruct into completion_raw" % reconstruction_failures,
        failures,
    )

    tau_mismatches = [
        step
        for step in steps
        if step.get("tau") is not None
        and step.get("tau") != tau_dict(step.get("action_parsed") or "")
    ]
    fail_if(bool(tau_mismatches), "tau mismatch on %d steps" % len(tau_mismatches), failures)
    invalid = [
        step
        for step in steps
        if (step.get("action_parsed") or "").strip()
        and not valid_action(step["action_parsed"])
    ]
    invalid_rate = len(invalid) / max(1, len(steps))
    if invalid:
        warnings.append(
            "invalid-action syntax rate %.1f%% (%d/%d); model errors retained"
            % (100 * invalid_rate, len(invalid), len(steps))
        )
    fail_if(
        invalid_rate > 0.15,
        "invalid-action syntax rate exceeds 15%% (%.1f%%)" % (100 * invalid_rate),
        failures,
    )
    empty_actions = [
        step for step in steps if not (step.get("action_parsed") or "").strip()
    ]
    empty_rate = len(empty_actions) / max(1, len(steps))
    if empty_actions:
        warnings.append(
            "empty-action rate %.1f%% (%d/%d); raw model failures retained"
            % (100 * empty_rate, len(empty_actions), len(steps))
        )
    fail_if(
        empty_rate > 0.10,
        "empty-action rate exceeds 10%% (%.1f%%)" % (100 * empty_rate),
        failures,
    )

    if arm == "decoupled":
        fail_if(
            any(not (step.get("thought_clean") or "").strip() for step in steps),
            "decoupled step has empty thought_clean",
            failures,
        )
        fail_if(
            any(
                step.get("U_T_targeted_ingen") is None
                and "thought_confidence_parse_failed" not in step.get("skip_reasons", [])
                for step in steps
            ),
            "unaccounted thought confidence parse failure",
            failures,
        )
        fail_if(
            any(
                step.get("U_A_targeted_ingen") is None
                and "action_confidence_parse_failed" not in step.get("skip_reasons", [])
                for step in steps
            ),
            "unaccounted action confidence parse failure",
            failures,
        )
    else:
        fail_if(
            any(not (step.get("thought_text") or "").strip() for step in steps),
            "entangled step has empty thought_text",
            failures,
        )
        fail_if(
            any(
                step.get("U_verbalized") is None
                and "confidence_parse_failed" not in step.get("skip_reasons", [])
                for step in steps
            ),
            "unaccounted joint confidence parse failure",
            failures,
        )

    episode_tasks = {r.get("task_id") for r in episodes}
    step_tasks = {r.get("task_id") for r in steps}
    fail_if(
        not step_tasks.issubset(episode_tasks),
        "one or more stepped tasks have no terminal episode record",
        failures,
    )

    print(
        "=== audit_hotpot: %s (%d calls, %d steps, %d episodes) ==="
        % (arm, len(calls), len(steps), len(episodes))
    )
    for warning in warnings:
        print("  ~ " + warning)
    for failure in failures:
        print("  FAIL " + failure)
    print("GATE: %s" % ("FAIL" if failures else "PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
