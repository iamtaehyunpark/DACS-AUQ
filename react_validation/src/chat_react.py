"""Decoupled chat-harness ALFWorld agent (ReDAct-style, two calls/step) — v4 (A8-A13).

Format-native elicitation (no XML): plain trailing labels in the same style as the turn, parsed
leniently and NEVER blocking. The thought call is the TARGETED reading u(q_t) (roster #6, §0.5/A16):
`THOUGHT_TARGET:` declares the claim q_t the next decision turns on, `THOUGHT_CONFIDENCE:` is the
confidence that q_t is true. The action call emits `ACTION:` + `ACTION_CONFIDENCE:` = u_A(g_t).
Recorded as U = 1 - c (0 certain, 1 uncertain): q_t_text, U_T_targeted_ingen, U_A_targeted_ingen. (The generic
in-gen verbalized row lives only in the entangled arm; here it is post-hoc.)
(Rationale: keep the validation harness free of the tag-contract fragility the PI left the
src/agent build to escape; enable_thinking=False already precludes </think> leakage.)

A8  thought contract has NO action vocabulary; the thought span is defensively trimmed of any
    trailing line equal to an admissible command (thought_trimmed logged).
A9/A10 strip-before-pass invariant preserved: the action call sees the confidence-free thought;
    env.step sees the bare command; post-hoc probes see the trimmed thought_clean.
A12 every step record carries tau:{I,W,R,C} from action_parsed (tau_map, unit-tested).
A13 seed = 1000 + task_index*100000 + step_idx*100 + call_offset; probe/skip reasons logged.

Config (env): REACT_N_EPISODES, REACT_UQLOG (path), sampling knobs, REACT_SEED_BASE, REACT_RUN_ID.
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
_RUN_ID = os.environ.get("REACT_RUN_ID", "decoupled")
_SB = {"top_k": _TOP_K, "min_p": _MIN_P, "repetition_penalty": _REP_PEN}
if _UQLOG:
    from uqlog import instrumented_chat, char_to_token_span, content_span

THOUGHT_PROMPT = open("prompts/decoupled_thought_v4.txt").read()
ACTION_PROMPT = open("prompts/decoupled_action_v4.txt").read()

# format-native labels (no XML) — parsed leniently, never blocking. The decoupled thought elicits
# the TARGETED reading u(q_t): a declared THOUGHT_TARGET claim + THOUGHT_CONFIDENCE that the claim is
# true (roster #6, §0.5/A16); the action elicits u_A(g_t). Both thought labels stripped before pass.
_TTARGET_RE = re.compile(r"THOUGHT_TARGET:\s*(.+)", re.IGNORECASE)
_TCONF_RE = re.compile(r"THOUGHT_CONFIDENCE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
_ACONF_RE = re.compile(r"ACTION_CONFIDENCE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
_THOUGHT_TAIL = re.compile(r"\n?[ \t>]*(?:THOUGHT_TARGET:|THOUGHT_CONFIDENCE:)", re.IGNORECASE)
_ACONF_SPLIT = re.compile(r"\n?[ \t>]*ACTION_CONFIDENCE:", re.IGNORECASE)


def _log(rec):
    with open(_UQLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower()).strip(" .")


def strip_think(t):
    return t.split("</think>", 1)[-1] if "</think>" in t else t


def _is_overflow(e):
    s = str(e).lower()
    return "context length" in s or "context_length" in s


def trim_trailing_commands(text, cmds):
    """A8.2: drop trailing lines that exactly match an admissible command (normalized).
    Returns (trimmed_text, trimmed_bool)."""
    cset = {_norm(c) for c in cmds}
    lines = text.rstrip().split("\n")
    trimmed = False
    while lines and _norm(lines[-1]) in cset:
        lines.pop(); trimmed = True
    return "\n".join(lines).rstrip(), trimmed


def _clip(c):
    """Clamp a parsed confidence into [0,1]; drop nonsense (e.g. a stray 100)."""
    return c if (c is not None and 0.0 <= c <= 1.0) else None


def parse_conf(text, regex):
    m = regex.search(text or "")
    return _clip(float(m.group(1))) if m else None


def parse_target(text):
    """THOUGHT_TARGET: the declared q_t claim (one line). None if absent."""
    m = _TTARGET_RE.search(text or "")
    if not m:
        return None
    q = re.split(r"THOUGHT_CONFIDENCE:", m.group(1), flags=re.IGNORECASE)[0].strip()
    return q or None


def _chat_call(prompt, max_tokens, seed):
    """Instrumented chat when logging, else plain. Returns (content, rec-or-None)."""
    if _UQLOG:
        return instrumented_chat(client, [{"role": "user", "content": prompt}], model="qwen",
                                 tokenizer_path=_TOK_PATH, temperature=_TEMP, top_p=_TOP_P,
                                 top_k=_TOP_K, min_p=_MIN_P, presence_penalty=_PRES_PEN,
                                 repetition_penalty=_REP_PEN, max_tokens=max_tokens, seed=seed,
                                 enable_thinking=False)
    r = client.chat.completions.create(model="qwen", messages=[{"role": "user", "content": prompt}],
                                       temperature=_TEMP, top_p=_TOP_P, max_tokens=max_tokens,
                                       presence_penalty=_PRES_PEN,
                                       extra_body={"chat_template_kwargs": {"enable_thinking": False}, **_SB})
    return (r.choices[0].message.content or ""), None


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
        cmds = admissible(info); cmd_block = "\n".join(cmds)
        skips = []
        # ---- THOUGHT call (no action vocab; ends with plain THOUGHT_CONFIDENCE:) ----
        tp = THOUGHT_PROMPT.replace("{DESCRIPTION}", task).replace("{HISTORY}", history)
        try:
            content, trec = _chat_call(tp, 512, base + i * 100 + 0)
        except Exception as e:            # graceful per-episode overflow guard — never crash the run
            if not _is_overflow(e):
                raise
            print("[step %d] CONTEXT OVERFLOW — ending episode" % i); sys.stdout.flush()
            if _UQLOG:
                _log({"kind": "episode", "run_id": _RUN_ID, "task_id": name, "success": False,
                      "terminal_reason": "context_overflow", "n_steps": i - 1,
                      "loop_collapse_fraction": round(loops / max(1, i - 1), 3)})
            return 0
        content = strip_think(content)
        q_t = parse_target(content)                        # THOUGHT_TARGET (the declared claim / q_t)
        if q_t is None:
            skips.append("thought_target_parse_failed")
        c_t = parse_conf(content, _TCONF_RE)               # confidence q_t is true -> targeted u(q_t)
        if c_t is None:
            skips.append("thought_confidence_parse_failed")
        U_T_targeted_ingen = None if c_t is None else round(1.0 - c_t, 4)
        # clean reasoning = everything before the first THOUGHT_TARGET/THOUGHT_CONFIDENCE label; then
        # trim trailing commands. Strips BOTH elicited labels before the action call + probe span.
        reasoning = _THOUGHT_TAIL.split(content, maxsplit=1)[0].rstrip()
        thought_clean, thought_trimmed = trim_trailing_commands(reasoning, cmds)
        # ---- ACTION call (sees tag-free, trimmed thought; ends with ACTION_CONFIDENCE:) ----
        ap = (ACTION_PROMPT.replace("{DESCRIPTION}", task).replace("{HISTORY}", history)
              .replace("{THOUGHTS}", thought_clean).replace("{COMMANDS}", cmd_block))
        try:
            acontent, arec = _chat_call(ap, 96, base + i * 100 + 1)
        except Exception as e:
            if not _is_overflow(e):
                raise
            print("[step %d] CONTEXT OVERFLOW (action) — ending episode" % i); sys.stdout.flush()
            if _UQLOG:
                _log({"kind": "episode", "run_id": _RUN_ID, "task_id": name, "success": False,
                      "terminal_reason": "context_overflow", "n_steps": i - 1,
                      "loop_collapse_fraction": round(loops / max(1, i - 1), 3)})
            return 0
        acontent = strip_think(acontent)
        c_a = parse_conf(acontent, _ACONF_RE)
        if c_a is None:
            skips.append("action_confidence_parse_failed")
        U_A_targeted_ingen = None if c_a is None else round(1.0 - c_a, 4)
        # action = first non-empty line before the ACTION_CONFIDENCE: line, stripped of an ACTION: label
        pre = _ACONF_SPLIT.split(acontent, maxsplit=1)[0]
        action = next((ln.strip() for ln in pre.splitlines() if ln.strip()), "")
        action = re.sub(r"^ACTION:\s*", "", action, flags=re.IGNORECASE).strip().strip("`").strip()
        obs, reward, done, info = env.step([action])
        obs = obs[0]; won = bool(info["won"][0]); done = bool(done[0])
        in_adm = action in cmds
        tau = tau_dict(action)
        if tau is None and action:
            skips.append("tau_unrecognized_action")
        print("[step %d] THOUGHT(%s): %s\n         q_t=%r U_T=%s | ACTION: %r U_A=%s adm=%s\n         OBS: %s"
              % (i, "trim" if thought_trimmed else "-", thought_clean[:120], q_t, U_T_targeted_ingen,
                 action, U_A_targeted_ingen, in_adm, obs)); sys.stdout.flush()
        pair = (action, obs); loop_flag = pair in seen; loops += loop_flag; seen.add(pair)
        if _UQLOG:
            # completion_raw stays the INITIAL generation (what gen_logprobs covers). Stage entropy
            # spans EXCLUDE the trailing confidence label+number. Thought call has no label and its
            # reasoning precedes THOUGHT_CONFIDENCE:, so [0, len(thought_clean)] is the clean prefix;
            # the action call now carries an ACTION: label, so span the command via content_span.
            if trec is not None:
                g = trec["gen_logprobs"]
                t_end = char_to_token_span(g, 0, min(len(thought_clean), len(trec["completion_raw"])))[1]
                trec.update({"kind": "call", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                             "call_kind": "thought",
                             "spans": {"thought": [0, t_end] if thought_clean else None, "action": None}})
                _log(trec)
            if arec is not None:
                g = arec["gen_logprobs"]
                a_span = content_span(g, arec["completion_raw"], "action:", ["action_confidence:"])
                arec.update({"kind": "call", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                             "call_kind": "action", "spans": {"thought": None, "action": a_span}})
                _log(arec)
            _log({"kind": "step", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                  "action_parsed": action, "obs": obs, "obs_changed": obs != prev_obs,
                  "admissible": cmds, "in_admissible": in_adm, "loop_flag": loop_flag,
                  "state_hash": hashlib.sha1(obs.encode()).hexdigest()[:16], "tau": tau,
                  "thought_clean": thought_clean, "thought_trimmed": thought_trimmed,
                  "q_t_text": q_t, "U_T_targeted_ingen": U_T_targeted_ingen, "U_A_targeted_ingen": U_A_targeted_ingen,
                  "skip_reasons": skips})
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
    r = run_episode(e - 1)
    succ += r
    print("EPISODE %d: %s | running success %d/%d = %.3f" % (e, "SUCCESS" if r else "fail", succ, e, succ / e))
    sys.stdout.flush()
print("\nFINAL: %d/%d = %.3f" % (succ, _N, succ / _N))
