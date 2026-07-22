"""Chat-harness ALFWorld agent — ENTANGLED (common ReAct pattern).

Unlike the decoupled ReDAct design (separate reasoning + action calls, chat_react.py), the
common field convention is a SINGLE response that emits the thought and the action together
(e.g. Thought:/Action: labels or <think>/<action> tags; see ReSpAct arXiv:2411.00927 and the
ALFWorld ReAct literature). Here: one chat call per step, forced into

    THOUGHT: <reasoning>
    ACTION: <one admissible command>

We parse the labels (last ACTION: wins) and IGNORE any native <think>...</think> block the
model emits. This is the entangled counterpart of chat_react.py, for the entangled-vs-
decoupled comparison.

Config (env): REACT_N_EPISODES (10), REACT_TEMPERATURE (0.7), REACT_TOP_P (0.95),
REACT_CAPTURE (path -> JSONL). Needs alfworld + openai; ALFWORLD_DATA set; vLLM serving "qwen".
"""
import os, re, json, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from openai import OpenAI
import yaml, alfworld, alfworld.agents.environment

import time, hashlib
client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
# Qwen3.6 official non-thinking (instruct) sampling recommendation.
_TEMP = float(os.environ.get("REACT_TEMPERATURE", "0.7"))
_TOP_P = float(os.environ.get("REACT_TOP_P", "0.80"))
_TOP_K = int(os.environ.get("REACT_TOP_K", "20"))
_MIN_P = float(os.environ.get("REACT_MIN_P", "0.0"))
_PRES_PEN = float(os.environ.get("REACT_PRESENCE_PENALTY", "1.5"))
_REP_PEN = float(os.environ.get("REACT_REPETITION_PENALTY", "1.0"))
_N = int(os.environ.get("REACT_N_EPISODES", "10"))
_CAP = os.environ.get("REACT_CAPTURE")

# Phase-1 UQ instrumentation (gated, pure observation).
_UQLOG = os.environ.get("REACT_UQLOG")
_TOK_PATH = os.environ.get("REACT_TOKENIZER", "Qwen/Qwen3.6-35B-A3B")
_SEED_BASE = int(os.environ.get("REACT_SEED_BASE", "1000"))
_RUN_ID = os.environ.get("REACT_RUN_ID", "entangled")
if _UQLOG:
    from uqlog import instrumented_chat, char_to_token_span, action_span_char


def _log(rec):
    with open(_UQLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")

PROMPT = """You are an AI agent solving a task in an interactive environment.
TASK DESCRIPTION:
{DESCRIPTION}
ENVIRONMENT HISTORY:
{HISTORY}
AVAILABLE COMMANDS:
{COMMANDS}
Think about the current situation, then choose your next action. Respond in EXACTLY this format, and nothing else:
THOUGHT: <your step-by-step reasoning about what to do next>
ACTION: <exactly one line, which must be EXACTLY one of the AVAILABLE COMMANDS>"""


def chat(prompt, max_tokens):
    r = client.chat.completions.create(
        model="qwen",
        messages=[{"role": "user", "content": prompt}],
        temperature=_TEMP, top_p=_TOP_P, max_tokens=max_tokens, presence_penalty=_PRES_PEN,
        extra_body={"chat_template_kwargs": {"enable_thinking": False},
                    "top_k": _TOP_K, "min_p": _MIN_P, "repetition_penalty": _REP_PEN},
    )
    return r.choices[0].message.content or ""


def gen_joint(prompt, max_tokens, task_id, step_idx):
    """One joint call (thought + action together). Plain chat() unless UQ logging is on.
    Entangled span split: thought = tokens before 'ACTION:', action = 'ACTION:' -> content end
    (trailing special tokens excluded)."""
    if not _UQLOG:
        return chat(prompt, max_tokens)
    seed = _SEED_BASE + step_idx * 100
    content, rec = instrumented_chat(
        client, [{"role": "user", "content": prompt}], model="qwen",
        tokenizer_path=_TOK_PATH, temperature=_TEMP, top_p=_TOP_P, top_k=_TOP_K, min_p=_MIN_P,
        presence_penalty=_PRES_PEN, repetition_penalty=_REP_PEN,
        max_tokens=max_tokens, seed=seed, enable_thinking=False)
    g, raw = rec["gen_logprobs"], rec["completion_raw"]
    ac = action_span_char(raw)
    thought_span = char_to_token_span(g, 0, ac)
    action_span = char_to_token_span(g, ac, len(raw)) if ac < len(raw) else None
    rec.update({"kind": "call", "run_id": _RUN_ID, "task_id": task_id, "step_idx": step_idx,
                "call_kind": "joint", "spans": {"thought": thought_span, "action": action_span}})
    _log(rec)
    return content


def parse_thought_action(text):
    # ignore any native <think>...</think> block, then read the THOUGHT: / ACTION: labels
    t = text.split("</think>", 1)[-1] if "</think>" in text else text
    tm = re.search(r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", t, re.IGNORECASE | re.DOTALL)
    thought = tm.group(1).strip() if tm else ""
    acts = re.findall(r"ACTION:\s*(.+)", t, re.IGNORECASE)          # last ACTION: wins
    action = acts[-1].strip() if acts else ""
    # one line, de-noise. If no ACTION: label was emitted (e.g. a rambling THOUGHT ran out
    # of tokens before ACTION), return "" — do NOT grab the truncated thought as the action.
    action = action.splitlines()[0].strip().strip("`").strip() if action else ""
    return thought, action


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
    history = ob[:m.start()].strip() if m else ob
    name = "/".join(info["extra.gamefile"][0].split("/")[-3:-1])
    print("\n==== %s ====\nTASK: %s" % (name, task)); sys.stdout.flush()
    seen, loops, prev_obs = set(), 0, ob
    for i in range(1, 50):
        cmds = admissible(info)
        raw = gen_joint(PROMPT.format(DESCRIPTION=task, HISTORY=history, COMMANDS="\n".join(cmds)), 1024, name, i)
        thought, action = parse_thought_action(raw)
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
                f.write(json.dumps({"step": i, "task": task, "raw": raw, "thought": thought,
                                    "action": action, "in_admissible": in_adm, "obs": obs}) + "\n")
        if _UQLOG:
            _log({"kind": "step", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                  "action_parsed": action, "action_raw": raw, "obs": obs,
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


succ = 0
for e in range(1, _N + 1):
    r = run_episode()
    succ += r
    print("EPISODE %d: %s | running success %d/%d = %.3f" % (e, "SUCCESS" if r else "fail", succ, e, succ / e))
    sys.stdout.flush()
print("\nFINAL: %d/%d = %.3f" % (succ, _N, succ / _N))
