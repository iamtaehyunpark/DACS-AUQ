"""Entangled HotpotQA ReAct acquisition arm.

One joint thought/action/confidence call per step, with the same sampling, task order,
action/observation history, environment, UQ instrumentation, and record schema as the
decoupled Hotpot arm. This is the Hotpot counterpart of chat_react_entangled.py.
"""
from __future__ import annotations

import os
import re
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from hotpot_common import (
    ACTION_SPECS,
    DOMAIN,
    clip_confidence,
    dataset_size,
    episode_record,
    is_overflow,
    make_env,
    sample_indices,
    state_hash,
    step_with_retry,
    strip_think,
    task_metadata,
    valid_action,
)
from hotpot_runtime import Runtime
from hotpot_tau_map import tau_dict


PROMPT = open("prompts/hotpot_entangled_v1.txt", encoding="utf-8").read()
_THOUGHT_RE = re.compile(
    r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", re.IGNORECASE | re.DOTALL
)
_CONF_RE = re.compile(r"CONFIDENCE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)


def parse_joint(text: str):
    text = strip_think(text)
    thought_match = _THOUGHT_RE.search(text)
    thought = thought_match.group(1).strip() if thought_match else ""
    actions = re.findall(r"ACTION:\s*(.+)", text, re.IGNORECASE)
    action = actions[-1].splitlines()[0].strip().strip("`").strip() if actions else ""
    action = re.split(r"CONFIDENCE:", action, flags=re.IGNORECASE)[0].strip()
    confidences = _CONF_RE.findall(text)
    confidence = clip_confidence(float(confidences[-1])) if confidences else None
    return thought, action, confidence


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
            prompt = (
                PROMPT.replace("{DESCRIPTION}", question)
                .replace("{HISTORY}", history)
                .replace("{COMMANDS}", "\n".join(ACTION_SPECS))
            )
            try:
                raw, call_record = runtime.chat(
                    prompt, max_tokens=1024, seed=task_seed + step_idx * 100
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

            thought, action, confidence = parse_joint(raw)
            if not thought:
                skip_reasons.append("thought_parse_failed")
            if confidence is None:
                skip_reasons.append("confidence_parse_failed")
            uncertainty = None if confidence is None else round(1.0 - confidence, 4)
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

            if runtime.uqlog and call_record is not None:
                from uqlog import content_span

                thought_span = content_span(
                    call_record["gen_logprobs"],
                    call_record["completion_raw"],
                    "thought:",
                    ["action:"],
                )
                action_span = content_span(
                    call_record["gen_logprobs"],
                    call_record["completion_raw"],
                    "action:",
                    ["confidence:"],
                )
                call_record.update(
                    {
                        "kind": "call",
                        "domain": DOMAIN,
                        "run_id": runtime.run_id,
                        "task_id": task_id,
                        "step_idx": step_idx,
                        "call_kind": "joint",
                        "spans": {"thought": thought_span, "action": action_span},
                    }
                )
                runtime.log(call_record)
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
                        "thought_text": thought,
                        "U_verbalized": uncertainty,
                        "skip_reasons": skip_reasons,
                    }
                )

            print(
                "[step %d] THOUGHT: %s\n         ACTION: %r U=%s valid=%s\n         OBS: %s"
                % (step_idx, thought[:140], action, uncertainty, action_valid, observation)
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
    runtime = Runtime("hotpot_entangled")
    env = make_env(runtime.split)
    task_ids = sample_indices(
        dataset_size(env),
        runtime.n_episodes,
        runtime.sample_seed,
        runtime.num_workers,
        runtime.worker_id,
    )
    print(
        "HotpotQA entangled worker %d/%d | seed=%d | shard=%d episodes"
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
