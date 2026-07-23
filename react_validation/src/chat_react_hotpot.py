"""Decoupled HotpotQA ReAct acquisition arm.

This is the Hotpot-domain counterpart of chat_react.py: two model calls per step
(reasoning, then action), format-native targeted in-generation confidence, identical
action/observation history retention, full token-logprob instrumentation, and the same
call/step/episode JSONL contract consumed by run_probes.py and the trajectory judge.
"""
from __future__ import annotations

import os
import re
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from hotpot_common import (
    ACTION_SPECS,
    DOMAIN,
    dataset_size,
    episode_record,
    is_overflow,
    make_env,
    parse_action_line,
    parse_confidence,
    sample_indices,
    state_hash,
    step_with_retry,
    strip_think,
    task_metadata,
    valid_action,
)
from hotpot_runtime import Runtime
from hotpot_tau_map import tau_dict


THOUGHT_PROMPT = open("prompts/hotpot_decoupled_thought_v1.txt", encoding="utf-8").read()
ACTION_PROMPT = open("prompts/hotpot_decoupled_action_v1.txt", encoding="utf-8").read()
_TARGET_RE = re.compile(r"THOUGHT_TARGET:\s*(.+)", re.IGNORECASE)
_THOUGHT_CONF_RE = re.compile(r"THOUGHT_CONFIDENCE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
_ACTION_CONF_RE = re.compile(r"ACTION_CONFIDENCE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
_THOUGHT_TAIL = re.compile(
    r"\n?[ \t>]*(?:THOUGHT_TARGET:|THOUGHT_CONFIDENCE:)", re.IGNORECASE
)


def parse_target(text: str) -> str | None:
    match = _TARGET_RE.search(text or "")
    if not match:
        return None
    value = re.split(r"THOUGHT_CONFIDENCE:", match.group(1), flags=re.IGNORECASE)[0].strip()
    return value or None


def _clean_question(reset_observation: str) -> str:
    return (
        reset_observation.split("Question:", 1)[-1].strip()
        if "Question:" in reset_observation
        else reset_observation.strip()
    )


def run_episode(env, runtime: Runtime, task_id: int) -> int:
    question, gold_answer = task_metadata(env, task_id)
    history = "(no Wikipedia actions taken yet)"
    previous_observation = ""
    seen: set[tuple[str, str]] = set()
    loops = 0
    last_info = None
    n_steps = 0
    task_seed = runtime.seed_base + task_id * 100000
    try:
        question = _clean_question(env.reset(idx=task_id))
        print("\n==== hotpot/%s ====\nQUESTION: %s" % (task_id, question))
        sys.stdout.flush()
        for step_idx in range(1, runtime.max_steps + 1):
            n_steps = step_idx
            skip_reasons = []

            thought_prompt = (
                THOUGHT_PROMPT.replace("{DESCRIPTION}", question).replace("{HISTORY}", history)
            )
            try:
                thought_raw, thought_record = runtime.chat(
                    thought_prompt, max_tokens=512, seed=task_seed + step_idx * 100
                )
            except Exception as exc:
                if not is_overflow(exc):
                    raise
                runtime.log(
                    episode_record(
                        run_id=runtime.run_id,
                        task_id=task_id,
                        question=question,
                        info=last_info,
                        terminal_reason="context_overflow",
                        n_steps=step_idx - 1,
                        loops=loops,
                        gold_answer=gold_answer,
                    )
                )
                return 0

            thought_raw = strip_think(thought_raw)
            target = parse_target(thought_raw)
            thought_conf = parse_confidence(thought_raw, _THOUGHT_CONF_RE)
            if target is None:
                skip_reasons.append("thought_target_parse_failed")
            if thought_conf is None:
                skip_reasons.append("thought_confidence_parse_failed")
            uncertainty_thought = (
                None if thought_conf is None else round(1.0 - thought_conf, 4)
            )
            thought = _THOUGHT_TAIL.split(thought_raw, maxsplit=1)[0].rstrip()

            action_prompt = (
                ACTION_PROMPT.replace("{DESCRIPTION}", question)
                .replace("{HISTORY}", history)
                .replace("{THOUGHTS}", thought)
                .replace("{COMMANDS}", "\n".join(ACTION_SPECS))
            )
            try:
                action_raw, action_record = runtime.chat(
                    action_prompt, max_tokens=96, seed=task_seed + step_idx * 100 + 1
                )
            except Exception as exc:
                if not is_overflow(exc):
                    raise
                runtime.log(
                    episode_record(
                        run_id=runtime.run_id,
                        task_id=task_id,
                        question=question,
                        info=last_info,
                        terminal_reason="context_overflow",
                        n_steps=step_idx - 1,
                        loops=loops,
                        gold_answer=gold_answer,
                    )
                )
                return 0

            action_raw = strip_think(action_raw)
            action_conf = parse_confidence(action_raw, _ACTION_CONF_RE)
            if action_conf is None:
                skip_reasons.append("action_confidence_parse_failed")
            uncertainty_action = (
                None if action_conf is None else round(1.0 - action_conf, 4)
            )
            action = parse_action_line(action_raw, "ACTION_CONFIDENCE")
            action_valid = valid_action(action)
            if not action_valid and action:
                skip_reasons.append("invalid_action_syntax")
            tau = tau_dict(action)
            if tau is None and action:
                skip_reasons.append("tau_unrecognized_action")

            observation, _reward, done, last_info = step_with_retry(env, action)
            observation = observation.replace("\\n", "")
            pair = (action, observation)
            loop_flag = pair in seen
            loops += int(loop_flag)
            seen.add(pair)

            if runtime.uqlog:
                from uqlog import char_to_token_span, content_span

                if thought_record is not None:
                    raw_completion = thought_record["completion_raw"]
                    thought_start_char = raw_completion.find(thought) if thought else 0
                    if thought_start_char < 0:
                        thought_start_char = 0
                    thought_span = char_to_token_span(
                        thought_record["gen_logprobs"],
                        thought_start_char,
                        min(
                            thought_start_char + len(thought),
                            len(raw_completion),
                        ),
                    )
                    thought_record.update(
                        {
                            "kind": "call",
                            "domain": DOMAIN,
                            "run_id": runtime.run_id,
                            "task_id": task_id,
                            "step_idx": step_idx,
                            "call_kind": "thought",
                            "spans": {
                                "thought": thought_span if thought else None,
                                "action": None,
                            },
                        }
                    )
                    runtime.log(thought_record)
                if action_record is not None:
                    action_span = content_span(
                        action_record["gen_logprobs"],
                        action_record["completion_raw"],
                        "action:",
                        ["action_confidence:"],
                    )
                    action_record.update(
                        {
                            "kind": "call",
                            "domain": DOMAIN,
                            "run_id": runtime.run_id,
                            "task_id": task_id,
                            "step_idx": step_idx,
                            "call_kind": "action",
                            "spans": {"thought": None, "action": action_span},
                        }
                    )
                    runtime.log(action_record)
                runtime.log(
                    {
                        "kind": "step",
                        "domain": DOMAIN,
                        "run_id": runtime.run_id,
                        "task_id": task_id,
                        "step_idx": step_idx,
                        "question": question,
                        "action_parsed": action,
                        "obs": observation,
                        "obs_changed": observation != previous_observation,
                        "admissible": ACTION_SPECS,
                        "in_admissible": action_valid,
                        "loop_flag": loop_flag,
                        "state_hash": state_hash(observation),
                        "tau": tau,
                        "thought_clean": thought,
                        "thought_trimmed": False,
                        "q_t_text": target,
                        "U_T_targeted_ingen": uncertainty_thought,
                        "U_A_targeted_ingen": uncertainty_action,
                        "skip_reasons": skip_reasons,
                    }
                )

            print(
                "[step %d] THOUGHT: %s\n         q_t=%r U_T=%s | ACTION: %r U_A=%s valid=%s\n"
                "         OBS: %s"
                % (
                    step_idx,
                    thought[:140],
                    target,
                    uncertainty_thought,
                    action,
                    uncertainty_action,
                    action_valid,
                    observation,
                )
            )
            sys.stdout.flush()
            previous_observation = observation
            history += "\nAction %d: %s\nObservation %d: %s" % (
                step_idx,
                action,
                step_idx,
                observation,
            )

            if done:
                success = bool(last_info.get("em", 0))
                runtime.log(
                    episode_record(
                        run_id=runtime.run_id,
                        task_id=task_id,
                        question=question,
                        info=last_info,
                        terminal_reason="success" if success else "done",
                        n_steps=step_idx,
                        loops=loops,
                        gold_answer=gold_answer,
                    )
                )
                return int(success)

        _observation, _reward, _done, last_info = step_with_retry(env, "Finish[]")
        runtime.log(
            episode_record(
                run_id=runtime.run_id,
                task_id=task_id,
                question=question,
                info=last_info,
                terminal_reason="step_cap",
                n_steps=runtime.max_steps,
                loops=loops,
                gold_answer=gold_answer,
            )
        )
        return int(bool(last_info.get("em", 0)))
    except Exception as exc:
        runtime.log(
            episode_record(
                run_id=runtime.run_id,
                task_id=task_id,
                question=question,
                info=last_info,
                terminal_reason="error",
                n_steps=n_steps,
                loops=loops,
                gold_answer=gold_answer,
                error=repr(exc)[:500],
            )
        )
        raise


def main() -> None:
    runtime = Runtime("hotpot_decoupled")
    env = make_env(runtime.split)
    task_ids = sample_indices(
        dataset_size(env),
        runtime.n_episodes,
        runtime.sample_seed,
        runtime.num_workers,
        runtime.worker_id,
    )
    print(
        "HotpotQA decoupled worker %d/%d | seed=%d | shard=%d episodes"
        % (runtime.worker_id, runtime.num_workers, runtime.sample_seed, len(task_ids))
    )
    successes = []
    for task_id in task_ids:
        try:
            success = run_episode(env, runtime, task_id)
        except Exception as exc:
            print("[task %s] ERROR %r — counted as failure" % (task_id, exc))
            success = 0
        successes.append(success)
        print(
            "running EM %d/%d = %.3f"
            % (sum(successes), len(successes), sum(successes) / len(successes))
        )
        sys.stdout.flush()
    print(
        "FINAL[%s]: EM %d/%d = %.4f"
        % (
            runtime.run_id,
            sum(successes),
            len(successes),
            sum(successes) / len(successes) if successes else 0.0,
        )
    )


if __name__ == "__main__":
    main()
