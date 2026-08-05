"""ALFWorld entangled re-run of originally-FAILED episodes, with P(True) fed back into context.

Same agent, same prompt template, same sampling config as chat_react_entangled.py. The ONLY
change is that in the feedback arms each completed turn carries its measured uncertainty into the
history the agent reads next (see uq_feedback_common for the arms and thresholds).

  UQFB_ARM        control | prod | c5        (required)
  UQFB_TASKS      newline-separated task_id allow-list (the originally-failed episodes)
  UQFB_LOG        output JSONL (required)
  UQFB_SEED_BASE  (2000) shared across arms, so all three arms are identical until the first
                  annotation appears — the tightest possible pairing
  REACT_SPLIT (eval_in_distribution)  REACT_MAX_STEPS (50)  REACT_MODEL/REACT_BASE_URL/REACT_TOKENIZER
  UQFB_NUM_WORKERS / UQFB_WORKER_ID   stride-shard the allow-list across processes

Every step logs the clean and annotated history lengths, U, whether the warning fired, and the
full probe record, so the analysis can ask not just "did it recover" but "did the agent CHANGE
BEHAVIOUR after a warning".
"""
import hashlib
import json
import os
import re
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from openai import OpenAI
import yaml
import alfworld
import alfworld.agents.environment

import probes
import uq_feedback_common as F
from tau_map import tau_dict
from uqlog import instrumented_chat, content_span

_ARM = os.environ.get("UQFB_ARM")
if _ARM not in F.ARMS:
    sys.exit("UQFB_ARM must be one of %s" % (F.ARMS,))
_LOG = os.environ.get("UQFB_LOG") or sys.exit("UQFB_LOG required")
_TASKS_FILE = os.environ.get("UQFB_TASKS") or sys.exit("UQFB_TASKS required")
_SEED_BASE = int(os.environ.get("UQFB_SEED_BASE", "2000"))
_MAX_STEPS = int(os.environ.get("REACT_MAX_STEPS", "50"))
_RUN_ID = os.environ.get("UQFB_RUN_ID", "uqfb_alfworld_%s" % _ARM)
_NW = int(os.environ.get("UQFB_NUM_WORKERS", "1"))
_WID = int(os.environ.get("UQFB_WORKER_ID", "0"))

_MODEL = os.environ.get("REACT_MODEL", "qwen")
_BASE_URL = os.environ.get("REACT_BASE_URL", "http://localhost:8000/v1")
_TOK = os.environ.get("REACT_TOKENIZER", "Qwen/Qwen3.6-35B-A3B")
# agent sampling: identical to the original entangled run
_TEMP, _TOP_P, _TOP_K = 0.7, 0.80, 20
_MIN_P, _PRES_PEN, _REP_PEN = 0.0, 1.5, 1.0

THR = None if _ARM == "control" else F.threshold("alfworld", _ARM)
client = OpenAI(api_key="EMPTY", base_url=_BASE_URL)
# probe calls are deterministic reads, unlike the agent's own sampling
_PCFG = probes.ProbeConfig(model=_MODEL, tokenizer_path=_TOK, base_url=_BASE_URL,
                           temperature=0.0, top_p=1.0, top_k=20, min_p=0.0,
                           presence_penalty=0.0, repetition_penalty=1.0, seed_base=9000)

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

_THOUGHT_RE = re.compile(r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", re.IGNORECASE | re.DOTALL)
_CONF_RE = re.compile(r"CONFIDENCE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)


def _log(rec):
    with open(_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def strip_think(t):
    return t.split("</think>", 1)[-1] if "</think>" in t else t


def _clip(c):
    return c if (c is not None and 0.0 <= c <= 1.0) else None


def parse_all(text):
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
    content, rec = instrumented_chat(client, [{"role": "user", "content": prompt}], model=_MODEL,
                                     tokenizer_path=_TOK, temperature=_TEMP, top_p=_TOP_P,
                                     top_k=_TOP_K, min_p=_MIN_P, presence_penalty=_PRES_PEN,
                                     repetition_penalty=_REP_PEN, max_tokens=1024, seed=seed,
                                     enable_thinking=False)
    return strip_think(content), rec


config = yaml.safe_load(open("base_config.yaml"))
env = alfworld.agents.environment.get_environment(config["env"]["type"])(
    config, train_eval=os.environ.get("REACT_SPLIT", "eval_in_distribution"))
env = env.init_env(batch_size=1)


def admissible(info):
    a = info.get("admissible_commands")
    if not a:
        return []
    return a[0] if isinstance(a[0], (list, tuple)) else a


def run_episode(task_index, wanted):
    """Returns 1/0, or None if this reset landed on a task outside the allow-list (the env only
    walks the split sequentially, so non-target tasks are reset past without any LLM call)."""
    ob, info = env.reset()
    name = "/".join(info["extra.gamefile"][0].split("/")[-3:-1])
    if name not in wanted:
        return None
    ob = "\n".join(ob[0].split("\n\n")[1:])
    m = re.search(r"Your task is to:\s*(.*)", ob)
    task = m.group(1).strip() if m else ob
    head = ob[:m.start()].strip() if m else ob

    # clean = what the probes see (comparable to the frozen corpus / threshold)
    # shown = what the AGENT sees (annotated in the feedback arms)
    history_clean = head
    history_shown = head
    seen, loops, n_warn, n_probe_ok = set(), 0, 0, 0
    base = _SEED_BASE + task_index * 100000

    for i in range(1, _MAX_STEPS + 1):
        cmds = admissible(info)
        prompt = (PROMPT.replace("{DESCRIPTION}", task)
                  .replace("{HISTORY}", history_shown)
                  .replace("{COMMANDS}", "\n".join(cmds)))
        try:
            full, rec = gen_joint(prompt, base + i * 100)
        except Exception as e:
            if "context length" not in str(e).lower() and "context_length" not in str(e).lower():
                raise
            _log({"kind": "episode", "run_id": _RUN_ID, "arm": _ARM, "task_id": name,
                  "success": False, "terminal_reason": "context_overflow", "n_steps": i - 1,
                  "loop_collapse_fraction": round(loops / max(1, i - 1), 3), "n_warnings": n_warn})
            return 0

        thought, action, conf = parse_all(full)
        hist_before = history_clean                     # context the agent HAD for this action
        obs, reward, done, info = env.step([action])
        obs = obs[0]
        won = bool(info["won"][0])
        done = bool(done[0])
        in_adm = action in cmds
        pair = (action, obs)
        loop_flag = pair in seen
        loops += loop_flag
        seen.add(pair)

        # ---- measure this step, then (feedback arms) write it back for the NEXT step
        U, probe_ok, pprompt = None, False, None
        if _ARM != "control":
            try:
                U, probe_ok, pprompt, prec = F.measure_u(
                    client, _PCFG, "alfworld", _ARM, task=task, history=hist_before,
                    commands="\n".join(cmds), thought=thought, action=action, obs=obs,
                    seed=9000 + task_index * 1000 + i)
                n_probe_ok += int(probe_ok)
            except Exception as e:                       # a probe failure must not kill the run
                sys.stderr.write("probe error %s step %d: %r\n" % (name, i, e))
        warned = bool(U is not None and U > THR) if _ARM != "control" else False
        n_warn += int(warned)

        history_clean += "\n> %s\n%s" % (action, obs)
        history_shown += "\n> %s\n%s%s" % (
            action, obs, F.annotation_line(U, THR) if _ARM != "control" else "")

        g, raw = rec["gen_logprobs"], rec["completion_raw"]
        rec.update({"kind": "call", "run_id": _RUN_ID, "arm": _ARM, "task_id": name, "step_idx": i,
                    "call_kind": "joint",
                    "spans": {"thought": content_span(g, raw, "thought:", ["action:"]),
                              "action": content_span(g, raw, "action:", ["confidence:"])}})
        _log(rec)
        _log({"kind": "step", "run_id": _RUN_ID, "arm": _ARM, "task_id": name, "step_idx": i,
              "action_parsed": action, "obs": obs, "admissible": cmds, "in_admissible": in_adm,
              "loop_flag": loop_flag, "tau": tau_dict(action), "thought_text": thought,
              "U_verbalized": None if conf is None else round(1.0 - conf, 4),
              "U_feedback": U, "probe_parse_ok": probe_ok, "warned": warned,
              "threshold": THR, "probe_prompt": pprompt,
              "state_hash": hashlib.sha1(obs.encode()).hexdigest()[:16]})
        print("[%s|%s step %d] %r U=%s warn=%s | %s"
              % (name[:28], _ARM, i, action, "n/a" if U is None else "%.2f" % U, warned, obs[:60]))
        sys.stdout.flush()

        if done:
            _log({"kind": "episode", "run_id": _RUN_ID, "arm": _ARM, "task_id": name,
                  "success": won, "terminal_reason": "success" if won else "done", "n_steps": i,
                  "loop_collapse_fraction": round(loops / i, 3), "n_warnings": n_warn,
                  "n_probe_ok": n_probe_ok})
            return 1 if won else 0

    _log({"kind": "episode", "run_id": _RUN_ID, "arm": _ARM, "task_id": name, "success": False,
          "terminal_reason": "step_cap", "n_steps": _MAX_STEPS,
          "loop_collapse_fraction": round(loops / _MAX_STEPS, 3), "n_warnings": n_warn,
          "n_probe_ok": n_probe_ok})
    return 0


def main():
    wanted = {l.strip() for l in open(_TASKS_FILE) if l.strip()}
    if _NW > 1:                                   # stride-shard the allow-list, disjoint union
        ordered = sorted(wanted)
        wanted = {t for i, t in enumerate(ordered) if i % _NW == _WID}
    print("arm=%s threshold=%s | %d target episodes | log=%s"
          % (_ARM, THR, len(wanted), _LOG))
    sys.stdout.flush()

    done_n, succ = 0, 0
    for e in range(2000):                          # walk the split until every target is covered
        if done_n >= len(wanted):
            break
        try:
            r = run_episode(e, wanted)
        except Exception as exc:
            print("[episode %d] ERROR %r — counted as failure" % (e, exc))
            r = 0
        if r is None:
            continue
        done_n += 1
        succ += r
        print("running: %d/%d succeeded" % (succ, done_n))
        sys.stdout.flush()
    print("\nFINAL[%s arm=%s]: recovered %d/%d = %.3f"
          % (_RUN_ID, _ARM, succ, done_n, succ / done_n if done_n else 0.0))


if __name__ == "__main__":
    main()
