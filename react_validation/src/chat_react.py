"""Decoupled chat-harness ALFWorld agent (ReDAct-style, two calls/step) — v4 (A8-A13).

A8  thought contract has NO action vocabulary; the thought span is defensively trimmed of any
    trailing line equal to an admissible command (thought_trimmed logged).
A9/A10 in-generation elicited class: the thought ends with <target>/<confidence>, the action
    line 2 is <confidence>. Both are STRIPPED before pass-through (strip-before-pass invariant):
    the action call sees the tag-free thought; env.step sees the bare command; post-hoc probes
    see the trimmed, tag-free thought. Confidence is recorded as U = 1 - c (0 certain, 1 uncertain).
A11 on tag-parse failure -> continuation-repair (re-sample the SAME context's tail, <=3x), not a
    separate evaluator call; tag_retries logged.
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
    from uqlog import instrumented_chat, char_to_token_span

THOUGHT_PROMPT = open("prompts/decoupled_thought_v4.txt").read()
ACTION_PROMPT = open("prompts/decoupled_action_v4.txt").read()

_TARGET_RE = re.compile(r"<target>(.*?)</target>", re.IGNORECASE | re.DOTALL)
_CONF_RE = re.compile(r"<confidence>\s*([0-9]*\.?[0-9]+)\s*</confidence>", re.IGNORECASE | re.DOTALL)


def _log(rec):
    with open(_UQLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower()).strip(" .")


def strip_think(t):
    return t.split("</think>", 1)[-1] if "</think>" in t else t


def trim_trailing_commands(text, cmds):
    """A8.2: drop trailing lines that exactly match an admissible command (normalized).
    Returns (trimmed_text, trimmed_bool)."""
    cset = {_norm(c) for c in cmds}
    lines = text.rstrip().split("\n")
    trimmed = False
    while lines and _norm(lines[-1]) in cset:
        lines.pop(); trimmed = True
    return "\n".join(lines).rstrip(), trimmed


def parse_conf(text):
    m = _CONF_RE.search(text)
    return float(m.group(1)) if m else None


def parse_target(text):
    m = _TARGET_RE.search(text)
    return m.group(1).strip() if m else None


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


def _continue(templated_prefix, max_tokens, seed):
    """A11 continuation-repair: continue the SAME context (templated prompt + partial completion)
    via /v1/completions, so the conditional distribution is preserved. Returns text."""
    r = client.completions.create(model="qwen", prompt=templated_prefix, max_tokens=max_tokens,
                                  temperature=_TEMP, top_p=_TOP_P, presence_penalty=_PRES_PEN,
                                  seed=seed, extra_body=_SB, stop=["</confidence>"])
    return r.choices[0].text


def elicit_tags(content, rec, seed, need_target):
    """Ensure a parseable <confidence> (and <target> if need_target) via continuation-repair.
    Returns (full_content, conf, target, tag_retries)."""
    retries = 0
    full = content
    while retries < 3:
        conf = parse_conf(full)
        target = parse_target(full) if need_target else "n/a"
        if conf is not None and (target is not None):
            return full, conf, (None if target == "n/a" else target), retries
        if rec is None:
            break  # no templated prompt available (non-logging path) — accept failure
        # build the continuation prefix: templated prompt + reasoning so far + forced tag open
        prefix_body = full.split("<target>")[0].split("<confidence>")[0].rstrip()
        forced = "\n<target>" if need_target else "\n<confidence>"
        tail = _continue(rec["prompt_templated"] + prefix_body + forced, 64, seed + 500 + retries)
        full = prefix_body + forced + tail + ("" if tail.rstrip().endswith(">") else "</confidence>")
        retries += 1
    return full, parse_conf(full), (parse_target(full) if need_target else None), retries


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
        cmds = admissible(info); cmd_block = "\n".join(cmds)
        skips = []
        # ---- THOUGHT call (no action vocab) ----
        tp = THOUGHT_PROMPT.replace("{DESCRIPTION}", task).replace("{HISTORY}", history)
        content, trec = _chat_call(tp, 512, base + i * 100 + 0)
        content = strip_think(content)
        full_t, c_t, q_t, tr_t = elicit_tags(content, trec, base + i * 100 + 0, need_target=True)
        if c_t is None:
            skips.append("thought_confidence_parse_failed")
        U_T_targeted_ingen = None if c_t is None else round(1.0 - c_t, 4)
        # strip tags -> clean reasoning; then trim trailing admissible commands (defensive)
        reasoning = full_t.split("<target>")[0].split("<confidence>")[0].rstrip()
        thought_clean, thought_trimmed = trim_trailing_commands(reasoning, cmds)
        # ---- ACTION call (sees tag-free, trimmed thought) ----
        ap = (ACTION_PROMPT.replace("{DESCRIPTION}", task).replace("{HISTORY}", history)
              .replace("{THOUGHTS}", thought_clean).replace("{COMMANDS}", cmd_block))
        acontent, arec = _chat_call(ap, 96, base + i * 100 + 1)
        acontent = strip_think(acontent)
        full_a, c_a, _, tr_a = elicit_tags(acontent, arec, base + i * 100 + 1, need_target=False)
        if c_a is None:
            skips.append("action_confidence_parse_failed")
        U_A_targeted_ingen = None if c_a is None else round(1.0 - c_a, 4)
        # action = first non-empty line before the <confidence> tag; stripped before env
        pre = full_a.split("<confidence>")[0]
        action = next((ln.strip() for ln in pre.splitlines() if ln.strip()), "")
        obs, reward, done, info = env.step([action])
        obs = obs[0]; won = bool(info["won"][0]); done = bool(done[0])
        in_adm = action in cmds
        tau = tau_dict(action)
        if tau is None and action:
            skips.append("tau_unrecognized_action")
        print("[step %d] THOUGHT(%s): %s\n         q_t=%r U_T=%s | ACTION: %r U_A=%s adm=%s\n         OBS: %s"
              % (i, "trim" if thought_trimmed else "-", thought_clean[:140], q_t, U_T_targeted_ingen,
                 action, U_A_targeted_ingen, in_adm, obs)); sys.stdout.flush()
        pair = (action, obs); loop_flag = pair in seen; loops += loop_flag; seen.add(pair)
        if _UQLOG:
            # per-call ground truth. completion_raw stays the INITIAL generation (what gen_logprobs
            # covers, so spans reconstruct); the tag-elicited full text + retries are logged too.
            # thought span = trimmed tag-free reasoning; action span = the command line.
            for rec, ck, full, span_text, tr in ((trec, "thought", full_t, thought_clean, tr_t),
                                                 (arec, "action", full_a, action, tr_a)):
                if rec is None:
                    continue
                g = rec["gen_logprobs"]
                end = char_to_token_span(g, 0, min(len(span_text), len(rec["completion_raw"])))[1]
                rec.update({"kind": "call", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                            "call_kind": ck,
                            "spans": {"thought": [0, end] if ck == "thought" else None,
                                      "action": [0, end] if ck == "action" else None},
                            "tag_retries": tr, "elicited_full": (full if tr else None)})
                _log(rec)
            _log({"kind": "step", "run_id": _RUN_ID, "task_id": name, "step_idx": i,
                  "action_parsed": action, "obs": obs, "obs_changed": obs != prev_obs,
                  "admissible": cmds, "in_admissible": in_adm, "loop_flag": loop_flag,
                  "state_hash": hashlib.sha1(obs.encode()).hexdigest()[:16], "tau": tau,
                  "thought_clean": thought_clean, "thought_trimmed": thought_trimmed,
                  "q_t_text": q_t, "U_T_targeted_ingen": U_T_targeted_ingen,
                  "U_A_targeted_ingen": U_A_targeted_ingen, "skip_reasons": skips})
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
