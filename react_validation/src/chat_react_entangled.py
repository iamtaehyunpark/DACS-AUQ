"""Entangled chat-harness ALFWorld agent — one joint call/step, AUQ System-1 (v4, A9/A12/A13).

A9.2 AUQ verbatim: the joint prompt carries AUQ's A.6.2 elicitation suffix; the model emits
     THOUGHT/ACTION then <confidence>/<explanation>. c-hat -> U_T_verbalized = 1 - c-hat
     (uncertainty; primary). explanation logged. Confidence is NOT stripped (AUQ propagates it).
A9.3 entangled history carries prior THOUGHTS and confidences (full Thought/Action/Conf/Obs
     transcript, AUQ System-1). Decoupled stays thought-free; the asymmetry is intentional.
A11 continuation-repair on <confidence> parse failure (same-context tail, <=3x); tag_retries.
A12 tau:{I,W,R,C} per step from action_parsed.  A13 seed = 1000 + task*100000 + step*100.
"""
import os, re, json, sys, time, hashlib
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from openai import OpenAI
import yaml, alfworld, alfworld.agents.environment
from tau_map import tau_dict

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
_TEMP = float(os.environ.get("REACT_TEMPERATURE", "0.7"))
_TOP_P = float(os.environ.get("REACT_TOP_P", "0.80"))
_TOP_K = int(os.environ.get("REACT_TOP_K", "20"))
_MIN_P = float(os.environ.get("REACT_MIN_P", "0.0"))
_PRES_PEN = float(os.environ.get("REACT_PRESENCE_PENALTY", "1.5"))
_REP_PEN = float(os.environ.get("REACT_REPETITION_PENALTY", "1.0"))
_N = int(os.environ.get("REACT_N_EPISODES", "10"))
_UQLOG = os.environ.get("REACT_UQLOG")
_TOK_PATH = os.environ.get("REACT_TOKENIZER", "Qwen/Qwen3.6-35B-A3B")
_SEED_BASE = int(os.environ.get("REACT_SEED_BASE", "1000"))
_RUN_ID = os.environ.get("REACT_RUN_ID", "entangled")
_SB = {"top_k": _TOP_K, "min_p": _MIN_P, "repetition_penalty": _REP_PEN}
if _UQLOG:
    from uqlog import instrumented_chat, char_to_token_span

BASE_PROMPT = """You are an AI agent solving a task in an interactive environment.
TASK DESCRIPTION:
{DESCRIPTION}
ENVIRONMENT HISTORY:
{HISTORY}
AVAILABLE COMMANDS:
{COMMANDS}
Think about the current situation, then choose your next action. Respond in EXACTLY this format:
THOUGHT: <your step-by-step reasoning about what to do next>
ACTION: <exactly one line, which must be EXACTLY one of the AVAILABLE COMMANDS>
"""
AUQ_SUFFIX = open("prompts/entangled_auq_suffix.txt").read().split("# ---")[0].strip()
PROMPT = BASE_PROMPT + AUQ_SUFFIX

_CONF_RE = re.compile(r"<confidence>\s*([0-9]*\.?[0-9]+)\s*</confidence>", re.IGNORECASE | re.DOTALL)
_EXPL_RE = re.compile(r"<explanation>(.*?)</explanation>", re.IGNORECASE | re.DOTALL)


def _log(rec):
    with open(_UQLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def strip_think(t):
    return t.split("</think>", 1)[-1] if "</think>" in t else t


def parse_ta(text):
    t = strip_think(text)
    tm = re.search(r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", t, re.IGNORECASE | re.DOTALL)
    thought = tm.group(1).strip() if tm else ""
    acts = re.findall(r"ACTION:\s*(.+)", t, re.IGNORECASE)
    action = acts[-1].strip() if acts else ""
    action = action.splitlines()[0].strip().strip("`").strip() if action else ""
    # action must stop before any tag if the model runs them together
    action = re.split(r"<confidence>|<explanation>", action, flags=re.IGNORECASE)[0].strip()
    return thought, action


def _continue(prefix, max_tokens, seed):
    r = client.completions.create(model="qwen", prompt=prefix, max_tokens=max_tokens,
                                  temperature=_TEMP, top_p=_TOP_P, presence_penalty=_PRES_PEN,
                                  seed=seed, extra_body=_SB, stop=["</confidence>"])
    return r.choices[0].text


def gen_joint(prompt, task_id, step_idx, seed):
    if not _UQLOG:
        r = client.chat.completions.create(model="qwen", messages=[{"role": "user", "content": prompt}],
                                           temperature=_TEMP, top_p=_TOP_P, max_tokens=1024,
                                           presence_penalty=_PRES_PEN,
                                           extra_body={"chat_template_kwargs": {"enable_thinking": False}, **_SB})
        return (r.choices[0].message.content or ""), None, 0
    content, rec = instrumented_chat(client, [{"role": "user", "content": prompt}], model="qwen",
                                     tokenizer_path=_TOK_PATH, temperature=_TEMP, top_p=_TOP_P,
                                     top_k=_TOP_K, min_p=_MIN_P, presence_penalty=_PRES_PEN,
                                     repetition_penalty=_REP_PEN, max_tokens=1024, seed=seed,
                                     enable_thinking=False)
    content = strip_think(content)
    # A11 continuation-repair for <confidence>
    retries = 0
    full = content
    while _CONF_RE.search(full) is None and retries < 3:
        body = full.split("<confidence>")[0].rstrip()
        tail = _continue(rec["prompt_templated"] + body + "\n<confidence>", 24, seed + 500 + retries)
        full = body + "\n<confidence>" + tail + ("" if tail.rstrip().endswith(">") else "</confidence>")
        retries += 1
    return full, rec, retries


config = yaml.safe_load(open("base_config.yaml"))
env = alfworld.agents.environment.get_environment(config["env"]["type"])(config, train_eval="eval_out_of_distribution")
env = env.init_env(batch_size=1)


def admissible(info):
    a = info.get("admissible_commands")
    if not a:
        return []
    return a[0] if isinstance(a[0], (list, tuple)) else a


def run_episode(task_index):
    ob, info = env.reset()
    ob = "\n".join(ob[0].split("\n\n")[1:])
    m = re.search(r"Your task is to:\s*(.*)", ob)
    task = m.group(1).strip() if m else ob
    history = ob[:m.start()].strip() if m else ob
    name = "/".join(info["extra.gamefile"][0].split("/")[-3:-1])
    print("\n==== %s ====\nTASK: %s" % (name, task)); sys.stdout.flush()
    seen, loops, prev_obs = set(), 0, ob
    base = _SEED_BASE + task_index * 100000
    for i in range(1, 50):
        cmds = admissible(info); skips = []
        prompt = PROMPT.replace("{DESCRIPTION}", task).replace("{HISTORY}", history).replace("{COMMANDS}", "\n".join(cmds))
        full, rec, tr = gen_joint(prompt, name, i, base + i * 100)
        thought, action = parse_ta(full)
        c = _CONF_RE.search(full)
        conf = float(c.group(1)) if c else None
        if conf is None:
            skips.append("confidence_parse_failed")
        U_T_verbalized = None if conf is None else round(1.0 - conf, 4)
        expl_m = _EXPL_RE.search(full)
        explanation = expl_m.group(1).strip() if expl_m else None
        obs, reward, done, info = env.step([action])
        obs = obs[0]; won = bool(info["won"][0]); done = bool(done[0])
        in_adm = action in cmds
        tau = tau_dict(action)
        if tau is None and action:
            skips.append("tau_unrecognized_action")
        print("[step %d] THOUGHT: %s\n         ACTION: %r U_T=%s adm=%s | OBS: %s"
              % (i, thought[:130], action, U_T_verbalized, in_adm, obs)); sys.stdout.flush()
        pair = (action, obs); loop_flag = pair in seen; loops += loop_flag; seen.add(pair)
        if _UQLOG and rec is not None:
            g, raw = rec["gen_logprobs"], rec["completion_raw"]
            low = raw.lower()
            ac = low.find("action:")
            cf = low.find("<confidence>")
            a_start = ac if ac >= 0 else len(raw)
            a_end = cf if cf >= 0 else len(raw)
            thought_span = char_to_token_span(g, 0, a_start)
            action_span = char_to_token_span(g, a_start, a_end) if a_start < a_end else None
            rec.update({"kind": "call", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                        "call_kind": "joint", "spans": {"thought": thought_span, "action": action_span},
                        "tag_retries": tr, "elicited_full": (full if tr else None)})
            _log(rec)
            _log({"kind": "step", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                  "action_parsed": action, "obs": obs, "obs_changed": obs != prev_obs,
                  "admissible": cmds, "in_admissible": in_adm, "loop_flag": loop_flag,
                  "state_hash": hashlib.sha1(obs.encode()).hexdigest()[:16], "tau": tau,
                  "thought_text": thought, "U_T_verbalized": U_T_verbalized,
                  "explanation": explanation, "skip_reasons": skips})
        prev_obs = obs
        # A9.3: AUQ System-1 history — thought + action + confidence + observation persist
        history += "\n> THOUGHT: %s\n> ACTION: %s\n> CONFIDENCE: %s\n%s" % (
            thought, action, "%.2f" % conf if conf is not None else "n/a", obs)
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
    r = run_episode(e - 1)
    succ += r
    print("EPISODE %d: %s | running success %d/%d = %.3f" % (e, "SUCCESS" if r else "fail", succ, e, succ / e))
    sys.stdout.flush()
print("\nFINAL: %d/%d = %.3f" % (succ, _N, succ / _N))
