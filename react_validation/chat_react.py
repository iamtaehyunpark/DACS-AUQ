"""Chat-harness ALFWorld agent — ReDAct's decoupled two-call design (chat API).

Fixes the raw-completion harness's failure modes by stating the turn contract explicitly
and letting the chat template enforce the boundary:
  - Call 1 (reasoning): produce a thought, given task + history + available commands.
  - Call 2 (action): output EXACTLY ONE line that is one of the available commands.
No few-shot document to over-complete (zero-shot + admissible list), no stop-string crutch.
The model answers "what is my next action?" instead of "continue this transcript."

Config (env): REACT_N_EPISODES (10), REACT_TEMPERATURE (0.7), REACT_TOP_P (0.95),
REACT_CAPTURE (path -> JSONL of every reasoning+action call).
Run under an interpreter with alfworld + openai; ALFWORLD_DATA set. vLLM server serving "qwen".
"""
import os, re, json, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from openai import OpenAI
import yaml, alfworld, alfworld.agents.environment

import time, hashlib
client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
_TEMP = float(os.environ.get("REACT_TEMPERATURE", "0.7"))
_TOP_P = float(os.environ.get("REACT_TOP_P", "0.95"))
_N = int(os.environ.get("REACT_N_EPISODES", "10"))
_CAP = os.environ.get("REACT_CAPTURE")

# Phase-1 UQ instrumentation (gated, pure observation). REACT_UQLOG=<path> -> JSONL of
# per-call ground truth (logprobs+top20+spans+config+timing) + per-step + per-episode records.
_UQLOG = os.environ.get("REACT_UQLOG")
_TOK_PATH = os.environ.get("REACT_TOKENIZER", "Qwen/Qwen3.6-35B-A3B")
_SEED_BASE = int(os.environ.get("REACT_SEED_BASE", "1000"))
_RUN_ID = os.environ.get("REACT_RUN_ID", "decoupled")
if _UQLOG:
    from uqlog import instrumented_chat


def _log(rec):
    with open(_UQLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")

REASONING_PROMPT = """You are an AI agent solving a task in an interactive environment.
TASK DESCRIPTION:
{DESCRIPTION}
ENVIRONMENT HISTORY:
{HISTORY}
AVAILABLE COMMANDS:
{COMMANDS}
Think step by step about the current situation and consider what action to take next.
Your thought process:"""

ACTION_PROMPT = """You are an AI agent solving a task in an interactive environment.
TASK DESCRIPTION:
{DESCRIPTION}
ENVIRONMENT HISTORY:
{HISTORY}
YOUR CURRENT REASONING:
{THOUGHTS}
AVAILABLE COMMANDS:
{COMMANDS}
OUTPUT RULES:
- Output exactly ONE line.
- That line must be EXACTLY one of the AVAILABLE COMMANDS.
- Do NOT output reasoning, explanation, punctuation, or extra words.
Now output your chosen action (one line only):"""


def chat(prompt, max_tokens):
    r = client.chat.completions.create(
        model="qwen",
        messages=[{"role": "user", "content": prompt}],
        temperature=_TEMP, top_p=_TOP_P, max_tokens=max_tokens,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    return r.choices[0].message.content or ""


def gen(prompt, max_tokens, call_kind, task_id, step_idx):
    """One generation. Plain chat() unless UQ logging is on, in which case the seeded,
    instrumented call is used and its ground-truth record is written. Decoupled: a thought
    call's whole response is the thought span; an action call's whole response is the action
    span (the two stages are already separate calls)."""
    if not _UQLOG:
        return chat(prompt, max_tokens)
    seed = _SEED_BASE + step_idx * 100 + (0 if call_kind == "thought" else 1)
    content, rec = instrumented_chat(
        client, [{"role": "user", "content": prompt}], model="qwen",
        tokenizer_path=_TOK_PATH, temperature=_TEMP, top_p=_TOP_P,
        max_tokens=max_tokens, seed=seed, enable_thinking=False)
    n = len(rec["gen_logprobs"])
    rec.update({"kind": "call", "run_id": _RUN_ID, "task_id": task_id, "step_idx": step_idx,
                "call_kind": call_kind,
                "spans": {"thought": [0, n], "action": None} if call_kind == "thought"
                else {"thought": None, "action": [0, n]}})
    _log(rec)
    return content


def strip_think(t):
    # robustness: if the model still emits a <think>...</think> block, drop it
    return t.split("</think>", 1)[-1] if "</think>" in t else t


def first_line(t):
    for ln in strip_think(t).splitlines():
        s = ln.strip()
        if s:
            return s
    return ""


def admissible(info):
    a = info.get("admissible_commands")
    if not a:
        return []
    return a[0] if isinstance(a[0], (list, tuple)) else a


config = yaml.safe_load(open("base_config.yaml"))
env = alfworld.agents.environment.get_environment(config["env"]["type"])(config, train_eval="eval_out_of_distribution")
env = env.init_env(batch_size=1)


def run_episode():
    ob, info = env.reset()
    ob = "\n".join(ob[0].split("\n\n")[1:])
    m = re.search(r"Your task is to:\s*(.*)", ob)
    task = m.group(1).strip() if m else ob
    history = ob[:m.start()].strip() if m else ob   # initial room description
    name = "/".join(info["extra.gamefile"][0].split("/")[-3:-1])
    print("\n==== %s ====\nTASK: %s" % (name, task)); sys.stdout.flush()
    seen, loops, prev_obs = set(), 0, ob
    for i in range(1, 50):
        cmds = admissible(info)
        cmd_block = "\n".join(cmds)
        thought = gen(REASONING_PROMPT.format(DESCRIPTION=task, HISTORY=history, COMMANDS=cmd_block), 512, "thought", name, i).strip()
        thought = strip_think(thought).strip()
        raw_action = gen(ACTION_PROMPT.format(DESCRIPTION=task, HISTORY=history, THOUGHTS=thought, COMMANDS=cmd_block), 128, "action", name, i)
        action = first_line(raw_action)
        obs, reward, done, info = env.step([action])
        obs = obs[0]; won = bool(info["won"][0]); done = bool(done[0])
        in_adm = action in cmds
        print("[step %d] THOUGHT: %s\n         ACTION: %r (admissible=%s)\n         OBS: %s"
              % (i, thought, action, in_adm, obs)); sys.stdout.flush()
        pair = (action, obs)
        loop_flag = pair in seen
        loops += loop_flag
        seen.add(pair)
        if _CAP:
            with open(_CAP, "a") as f:
                f.write(json.dumps({"step": i, "task": task, "thought": thought,
                                    "action_raw": raw_action, "action": action,
                                    "in_admissible": in_adm, "obs": obs}) + "\n")
        if _UQLOG:
            _log({"kind": "step", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                  "action_parsed": action, "action_raw": raw_action, "obs": obs,
                  "obs_changed": obs != prev_obs, "admissible": cmds, "in_admissible": in_adm,
                  "loop_flag": loop_flag, "state_hash": hashlib.sha1(obs.encode()).hexdigest()[:16]})
        prev_obs = obs
        history += "\n> %s\n%s" % (action, obs)
        if done:
            if _UQLOG:
                _log({"kind": "episode", "run_id": _RUN_ID, "task_id": name, "success": won,
                      "terminal_reason": "success" if won else "done", "n_steps": i,
                      "loop_collapse_fraction": round(loops / i, 3)})
            return 1 if won else 0
    if _UQLOG:
        _log({"kind": "episode", "run_id": _RUN_ID, "task_id": name, "success": False,
              "terminal_reason": "step_cap", "n_steps": 49, "loop_collapse_fraction": round(loops / 49, 3)})
    return 0


prefixes = {"pick_and_place": "put", "pick_clean_then_place": "clean", "pick_heat_then_place": "heat",
            "pick_cool_then_place": "cool", "look_at_obj": "examine", "pick_two_obj": "puttwo"}
succ = 0
for e in range(1, _N + 1):
    r = run_episode()
    succ += r
    print("EPISODE %d: %s | running success %d/%d = %.3f" % (e, "SUCCESS" if r else "fail", succ, e, succ / e))
    sys.stdout.flush()
print("\nFINAL: %d/%d = %.3f" % (succ, _N, succ / _N))
