"""HotpotQA entangled re-run of originally-FAILED questions, with P(True) fed back into context.

Same agent, prompt template, sampling config and env plumbing as chat_react_hotpot_entangled.py —
its helpers are imported rather than copied. The ONLY change is that in the feedback arms each
completed turn carries its measured uncertainty into the history the agent reads next.

  UQFB_ARM       control | prod | c5     (required)
  UQFB_TASKS     newline-separated dev-set indices (the originally-failed questions)
  UQFB_LOG       output JSONL (required)
  UQFB_SEED_BASE (2000) shared across arms, so the arms are identical until the first annotation
  REACT_MAX_STEPS (7)   REACT_MODEL / REACT_BASE_URL / REACT_TOKENIZER

Hits LIVE Wikipedia on every search, exactly like the original run.
"""
from __future__ import annotations

import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI

import probes
import uq_feedback_common as F
from chat_react_hotpot_entangled import PROMPT, parse_joint
from hotpot_common import (
    ACTION_SPECS,
    episode_record,
    make_env,
    state_hash,
    step_with_retry,
    task_metadata,
    valid_action,
)
from hotpot_runtime import Runtime
from hotpot_tau_map import tau_dict

DOMAIN = "hotpotqa"
_ARM = os.environ.get("UQFB_ARM")
if _ARM not in F.ARMS:
    sys.exit("UQFB_ARM must be one of %s" % (F.ARMS,))
_LOG = os.environ.get("UQFB_LOG") or sys.exit("UQFB_LOG required")
_TASKS_FILE = os.environ.get("UQFB_TASKS") or sys.exit("UQFB_TASKS required")
_SEED_BASE = int(os.environ.get("UQFB_SEED_BASE", "2000"))

THR = None if _ARM == "control" else F.threshold("hotpot", _ARM)
_MODEL = os.environ.get("REACT_MODEL", "qwen")
_BASE_URL = os.environ.get("REACT_BASE_URL", "http://localhost:8000/v1")
_TOK = os.environ.get("REACT_TOKENIZER", "Qwen/Qwen3.6-35B-A3B")
client = OpenAI(api_key="EMPTY", base_url=_BASE_URL)
_PCFG = probes.ProbeConfig(model=_MODEL, tokenizer_path=_TOK, base_url=_BASE_URL,
                           temperature=0.0, top_p=1.0, top_k=20, min_p=0.0,
                           presence_penalty=0.0, repetition_penalty=1.0, seed_base=9000)


def _log(rec):
    with open(_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def run_episode(env, runtime, task_id):
    question, gold_answer = task_metadata(env, task_id)
    question = question if isinstance(question, str) else str(question)
    history_clean = "(no Wikipedia actions taken yet)"    # what the PROBES see
    history_shown = history_clean                          # what the AGENT sees
    seen, loops, n_warn, n_steps = set(), 0, 0, 0
    last_info = None
    task_seed = _SEED_BASE + task_id * 100000
    from chat_react_hotpot_entangled import _clean_question
    question = _clean_question(env.reset(idx=task_id))
    print("\n==== hotpot/%s [%s] ====\nQUESTION: %s" % (task_id, _ARM, question))
    sys.stdout.flush()

    for step_idx in range(1, runtime.max_steps + 1):
        n_steps = step_idx
        prompt = (PROMPT.replace("{DESCRIPTION}", question)
                  .replace("{HISTORY}", history_shown)
                  .replace("{COMMANDS}", "\n".join(ACTION_SPECS)))
        raw, call_record = runtime.chat(prompt, max_tokens=1024,
                                        seed=task_seed + step_idx * 100)
        thought, action, confidence = parse_joint(raw)
        hist_before = history_clean
        observation, _reward, done, last_info = step_with_retry(env, action)
        observation = observation.replace("\\n", "")
        pair = (action, observation)
        loop_flag = pair in seen
        loops += int(loop_flag)
        seen.add(pair)

        U, probe_ok, pprompt = None, False, None
        if _ARM != "control":
            try:
                U, probe_ok, pprompt, _prec = F.measure_u(
                    client, _PCFG, "hotpot", _ARM, task=question, history=hist_before,
                    commands="\n".join(ACTION_SPECS), thought=thought, action=action,
                    obs=observation, seed=9000 + task_id * 1000 + step_idx)
            except Exception as exc:
                sys.stderr.write("probe error %s step %d: %r\n" % (task_id, step_idx, exc))
        warned = bool(U is not None and U > THR) if _ARM != "control" else False
        n_warn += int(warned)

        turn = "\nAction %d: %s\nObservation %d: %s" % (step_idx, action, step_idx, observation)
        history_clean += turn
        history_shown += turn + (F.annotation_line(U, THR) if _ARM != "control" else "")

        _log({"kind": "step", "domain": DOMAIN, "run_id": runtime.run_id, "arm": _ARM,
              "task_id": task_id, "step_idx": step_idx, "question": question,
              "action_parsed": action, "obs": observation, "admissible": ACTION_SPECS,
              "in_admissible": valid_action(action), "loop_flag": loop_flag,
              "state_hash": state_hash(observation), "tau": tau_dict(action),
              "thought_text": thought,
              "U_verbalized": None if confidence is None else round(1.0 - confidence, 4),
              "U_feedback": U, "probe_parse_ok": probe_ok, "warned": warned,
              "threshold": THR, "probe_prompt": pprompt})
        print("[step %d] %r U=%s warn=%s | %s"
              % (step_idx, action, "n/a" if U is None else "%.2f" % U, warned, observation[:90]))
        sys.stdout.flush()

        if done:
            rec = episode_record(run_id=runtime.run_id, task_id=task_id, question=question,
                                 info=last_info, terminal_reason="done", n_steps=step_idx,
                                 loops=loops, gold_answer=gold_answer)
            rec.update({"arm": _ARM, "n_warnings": n_warn})
            _log(rec)
            return int(bool((last_info or {}).get("em", 0)))

    _observation, _reward, _done, last_info = step_with_retry(env, "Finish[]")
    rec = episode_record(run_id=runtime.run_id, task_id=task_id, question=question,
                         info=last_info, terminal_reason="step_cap", n_steps=n_steps,
                         loops=loops, gold_answer=gold_answer)
    rec.update({"arm": _ARM, "n_warnings": n_warn})
    _log(rec)
    return int(bool((last_info or {}).get("em", 0)))


def main():
    runtime = Runtime("uqfb_hotpot_%s" % _ARM)
    env = make_env(runtime.split)
    task_ids = [int(l.strip()) for l in open(_TASKS_FILE) if l.strip()]
    print("arm=%s threshold=%s | %d target questions | log=%s"
          % (_ARM, THR, len(task_ids), _LOG))
    sys.stdout.flush()
    succ = []
    for task_id in task_ids:
        try:
            succ.append(run_episode(env, runtime, task_id))
        except Exception as exc:
            print("[task %s] ERROR %r — counted as failure" % (task_id, exc))
            succ.append(0)
        print("running: recovered %d/%d" % (sum(succ), len(succ)))
        sys.stdout.flush()
    print("\nFINAL[uqfb_hotpot arm=%s]: recovered %d/%d = %.3f"
          % (_ARM, sum(succ), len(succ), sum(succ) / len(succ) if succ else 0.0))


if __name__ == "__main__":
    main()
