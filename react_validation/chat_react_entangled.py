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

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
_TEMP = float(os.environ.get("REACT_TEMPERATURE", "0.7"))
_TOP_P = float(os.environ.get("REACT_TOP_P", "0.95"))
_N = int(os.environ.get("REACT_N_EPISODES", "10"))
_CAP = os.environ.get("REACT_CAPTURE")

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
        temperature=_TEMP, top_p=_TOP_P, max_tokens=max_tokens,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    return r.choices[0].message.content or ""


def parse_thought_action(text):
    # ignore any native <think>...</think> block, then read the THOUGHT: / ACTION: labels
    t = text.split("</think>", 1)[-1] if "</think>" in text else text
    tm = re.search(r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", t, re.IGNORECASE | re.DOTALL)
    thought = tm.group(1).strip() if tm else ""
    acts = re.findall(r"ACTION:\s*(.+)", t, re.IGNORECASE)          # last ACTION: wins
    action = acts[-1].strip() if acts else ""
    if action:
        action = action.splitlines()[0].strip().strip("`").strip()  # one line, de-noise
    else:
        # fallback: last non-empty line (model ignored the format)
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        action = lines[-1] if lines else ""
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
    for i in range(1, 50):
        cmds = admissible(info)
        raw = chat(PROMPT.format(DESCRIPTION=task, HISTORY=history, COMMANDS="\n".join(cmds)), 512)
        thought, action = parse_thought_action(raw)
        obs, reward, done, info = env.step([action])
        obs = obs[0]; won = bool(info["won"][0]); done = bool(done[0])
        in_adm = action in cmds
        print("[step %d] THOUGHT: %s\n         ACTION: %r (admissible=%s)\n         OBS: %s"
              % (i, thought[:200], action, in_adm, obs)); sys.stdout.flush()
        if _CAP:
            with open(_CAP, "a") as f:
                f.write(json.dumps({"step": i, "task": task, "raw": raw, "thought": thought,
                                    "action": action, "in_admissible": in_adm, "obs": obs}) + "\n")
        history += "\n> %s\n%s" % (action, obs)
        if done:
            return 1 if won else 0
    return 0


succ = 0
for e in range(1, _N + 1):
    r = run_episode()
    succ += r
    print("EPISODE %d: %s | running success %d/%d = %.3f" % (e, "SUCCESS" if r else "fail", succ, e, succ / e))
    sys.stdout.flush()
print("\nFINAL: %d/%d = %.3f" % (succ, _N, succ / _N))
