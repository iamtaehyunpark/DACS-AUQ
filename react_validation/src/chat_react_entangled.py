"""Entangled chat-harness ALFWorld agent — one joint call/step, format-native confidence (v4).

The joint call emits, in one generation and in this exact order, three plain labels:
    THOUGHT: <reasoning>
    ACTION: <exactly one AVAILABLE COMMAND>
    CONFIDENCE: <0.00-1.00>
ONE in-gen confidence — the AUQ ĉ, after the action (roster #5, joint; stored U_verbalized = 1 - ĉ).
A joint generation has no separable pre-action epistemic locus, so there is deliberately NO
thought-side in-gen confidence (that, and per-stage granularity, come from the post-hoc probes on
both stages, plus token-intrinsic entropy over each span). Decoupled, by contrast, has a separable
thought stage and carries the targeted u(q_t). Parsed leniently, never blocks. No XML.

History retention: ACTION + OBSERVATION only, matching the decoupled arm (both arms symmetric).
AUQ full-retention (thought + ĉ persisted into history, AUQ System-1 propagation) is shelved
behind REACT_HISTORY_MODE=full, for a later comparison run only if needed.
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
_HIST_MODE = os.environ.get("REACT_HISTORY_MODE", "action_obs")  # "action_obs" (default) | "full" (AUQ retention)
_SB = {"top_k": _TOP_K, "min_p": _MIN_P, "repetition_penalty": _REP_PEN}
if _UQLOG:
    from uqlog import instrumented_chat, content_span

PROMPT = """You are an AI agent solving a task in an interactive environment.
TASK DESCRIPTION:
{DESCRIPTION}
ENVIRONMENT HISTORY:
{HISTORY}
AVAILABLE COMMANDS:
{COMMANDS}
Think about the current situation, then choose your next action. Respond in EXACTLY this format, each label on its own line:
THOUGHT: your step-by-step reasoning about what to do next
ACTION: exactly one line, which must be EXACTLY one of the AVAILABLE COMMANDS
CONFIDENCE: a number from 0.00 to 1.00 — your confidence that the action you chose is correct
"""

# Entangled emits ONE in-gen confidence (the AUQ ĉ, after the action; roster #5, joint). A joint
# generation has no separable pre-action epistemic locus, so there is NO thought-side in-gen
# confidence — that (and per-stage granularity) comes from the post-hoc probes on both stages.
_THOUGHT_RE = re.compile(r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", re.IGNORECASE | re.DOTALL)
_CONF_RE = re.compile(r"CONFIDENCE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)  # any *CONFIDENCE:; take last


def _log(rec):
    with open(_UQLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def strip_think(t):
    return t.split("</think>", 1)[-1] if "</think>" in t else t


def _clip(c):
    return c if (c is not None and 0.0 <= c <= 1.0) else None


def _conf(regex, text):
    m = regex.search(text or "")
    return _clip(float(m.group(1))) if m else None


def _fmt(c):
    return "%.2f" % c if c is not None else "n/a"


def parse_all(text):
    """THOUGHT / ACTION / CONFIDENCE (single AUQ ĉ), lenient. The action is the ACTION: line;
    the confidence is the LAST *CONFIDENCE: number (the post-action ĉ)."""
    t = strip_think(text)
    tm = _THOUGHT_RE.search(t)
    thought = tm.group(1).strip() if tm else ""
    acts = re.findall(r"ACTION:\s*(.+)", t, re.IGNORECASE)
    action = acts[-1].strip() if acts else ""
    action = action.splitlines()[0].strip().strip("`").strip() if action else ""
    action = re.split(r"CONFIDENCE:", action, flags=re.IGNORECASE)[0].strip()
    nums = _CONF_RE.findall(t)
    conf = _clip(float(nums[-1])) if nums else None
    return thought, action, conf


def gen_joint(prompt, seed):
    if not _UQLOG:
        r = client.chat.completions.create(model="qwen", messages=[{"role": "user", "content": prompt}],
                                           temperature=_TEMP, top_p=_TOP_P, max_tokens=1024,
                                           presence_penalty=_PRES_PEN,
                                           extra_body={"chat_template_kwargs": {"enable_thinking": False}, **_SB})
        return (r.choices[0].message.content or ""), None
    content, rec = instrumented_chat(client, [{"role": "user", "content": prompt}], model="qwen",
                                     tokenizer_path=_TOK_PATH, temperature=_TEMP, top_p=_TOP_P,
                                     top_k=_TOP_K, min_p=_MIN_P, presence_penalty=_PRES_PEN,
                                     repetition_penalty=_REP_PEN, max_tokens=1024, seed=seed,
                                     enable_thinking=False)
    return strip_think(content), rec


config = yaml.safe_load(open("base_config.yaml"))
env = alfworld.agents.environment.get_environment(config["env"]["type"])(config, train_eval=os.environ.get("REACT_SPLIT", "eval_out_of_distribution"))
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
        try:
            full, rec = gen_joint(prompt, base + i * 100)
        except Exception as e:
            if "context length" not in str(e).lower() and "context_length" not in str(e).lower():
                raise
            # graceful per-episode overflow guard: end the episode, never crash the run.
            print("[step %d] CONTEXT OVERFLOW — ending episode" % i); sys.stdout.flush()
            if _UQLOG:
                _log({"kind": "episode", "run_id": _RUN_ID, "task_id": name, "success": False,
                      "terminal_reason": "context_overflow", "n_steps": i - 1,
                      "loop_collapse_fraction": round(loops / max(1, i - 1), 3)})
            return 0
        thought, action, conf = parse_all(full)
        if conf is None:
            skips.append("confidence_parse_failed")
        U_verbalized = None if conf is None else round(1.0 - conf, 4)   # single AUQ ĉ (roster #5, joint)
        obs, reward, done, info = env.step([action])
        obs = obs[0]; won = bool(info["won"][0]); done = bool(done[0])
        in_adm = action in cmds
        tau = tau_dict(action)
        if tau is None and action:
            skips.append("tau_unrecognized_action")
        print("[step %d] THOUGHT: %s\n         ACTION: %r U=%s adm=%s | OBS: %s"
              % (i, thought[:130], action, U_verbalized, in_adm, obs)); sys.stdout.flush()
        pair = (action, obs); loop_flag = pair in seen; loops += loop_flag; seen.add(pair)
        if _UQLOG and rec is not None:
            g, raw = rec["gen_logprobs"], rec["completion_raw"]
            # stage entropy spans exclude labels + the trailing ĉ number: thought = THOUGHT: content
            # up to ACTION:; action = ACTION: content up to the trailing CONFIDENCE:.
            thought_span = content_span(g, raw, "thought:", ["action:"])
            action_span = content_span(g, raw, "action:", ["confidence:"])
            rec.update({"kind": "call", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                        "call_kind": "joint", "spans": {"thought": thought_span, "action": action_span}})
            _log(rec)
            _log({"kind": "step", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                  "action_parsed": action, "obs": obs, "obs_changed": obs != prev_obs,
                  "admissible": cmds, "in_admissible": in_adm, "loop_flag": loop_flag,
                  "state_hash": hashlib.sha1(obs.encode()).hexdigest()[:16], "tau": tau,
                  "thought_text": thought, "U_verbalized": U_verbalized, "skip_reasons": skips})
        prev_obs = obs
        # Retain action + observation only (default), same as the decoupled arm. REACT_HISTORY_MODE=full
        # restores AUQ System-1 propagation (thought + the single ĉ persisted) for a later comparison.
        if _HIST_MODE == "full":
            history += "\n> THOUGHT: %s\n> ACTION: %s\n> CONFIDENCE: %s\n%s" % (
                thought, action, _fmt(conf), obs)
        else:
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
    r = run_episode(e - 1)
    succ += r
    print("EPISODE %d: %s | running success %d/%d = %.3f" % (e, "SUCCESS" if r else "fail", succ, e, succ / e))
    sys.stdout.flush()
print("\nFINAL: %d/%d = %.3f" % (succ, _N, succ / _N))
