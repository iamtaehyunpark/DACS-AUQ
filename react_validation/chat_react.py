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

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
_TEMP = float(os.environ.get("REACT_TEMPERATURE", "0.7"))
_TOP_P = float(os.environ.get("REACT_TOP_P", "0.95"))
_N = int(os.environ.get("REACT_N_EPISODES", "10"))
_CAP = os.environ.get("REACT_CAPTURE")

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
    for i in range(1, 50):
        cmds = admissible(info)
        cmd_block = "\n".join(cmds)
        thought = chat(REASONING_PROMPT.format(DESCRIPTION=task, HISTORY=history, COMMANDS=cmd_block), 512).strip()
        thought = strip_think(thought).strip()
        raw_action = chat(ACTION_PROMPT.format(DESCRIPTION=task, HISTORY=history, THOUGHTS=thought, COMMANDS=cmd_block), 128)
        action = first_line(raw_action)
        obs, reward, done, info = env.step([action])
        obs = obs[0]; won = bool(info["won"][0]); done = bool(done[0])
        in_adm = action in cmds
        print("[step %d] THOUGHT: %s\n         ACTION: %r (admissible=%s)\n         OBS: %s"
              % (i, thought, action, in_adm, obs)); sys.stdout.flush()
        if _CAP:
            with open(_CAP, "a") as f:
                f.write(json.dumps({"step": i, "task": task, "thought": thought,
                                    "action_raw": raw_action, "action": action,
                                    "in_admissible": in_adm, "obs": obs}) + "\n")
        history += "\n> %s\n%s" % (action, obs)
        if done:
            return 1 if won else 0
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
