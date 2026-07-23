"""E0 v3 (A14) — adjudicated three-judge ensemble, ReDAct Fig-9 WHOLE-TRAJECTORY protocol.

Mirrors the v1 judge (src/judge/pipeline.py), which was fast + calibrated. Each judge sees the
WHOLE trajectory in ONE call and returns per-step JSON {"step i": {"label":0|1,"reason":...}}
(label 1 = good/helpful, 0 = bad). That is ~N_trajectories calls per judge, not ~N_steps — the
reason v1 was quick (a per-step judge is ~25x more calls). Rubric = the transcribed ReDAct Fig-9
(prompts/judge_redact_fig9.txt): exploration counts as good, "do NOT mark all steps 0" — the
calibration my earlier per-step draft lacked (it produced a 40/50/88% incorrect spread).

A14 ensemble: all THREE API judges label every trajectory; per step, unanimous -> ensemble label,
any disagreement (2-1 incl.) -> needs_human. label 0 (bad) -> incorrect=1 (AUROC positive class).
Rendering: actions + observations only, no thoughts (A7). Parallel across trajectories; one retry
at T=0.2 on unparseable (temp-locked judges excepted); unparsed trajectory -> steps null, counted.
Resumable by task_id. Fresh output file (old per-step/bad-rubric labels are discarded).

Config (env): JUDGE_INPUT, JUDGE_OUTPUT, AZURE_JUDGE_ENDPOINT, AZURE_JUDGE_KEY,
  JUDGE_MODELS (grok-4.3,DeepSeek-V4-Pro,gpt-5.6-sol), JUDGE_WORKERS (8), JUDGE_MAX_TRAJ (all).
"""
import json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import probes

ENDPOINT = os.environ.get("AZURE_JUDGE_ENDPOINT", "https://llmjudgejul20-resource.services.ai.azure.com/openai/v1")
KEY = os.environ.get("AZURE_JUDGE_KEY", "")
MODELS = [m.strip() for m in os.environ.get("JUDGE_MODELS", "grok-4.3,DeepSeek-V4-Pro,gpt-5.6-sol").split(",") if m.strip()]
RESPONSES_API = {"gpt-5.6-sol"}
WORKERS = int(os.environ.get("JUDGE_WORKERS", "8"))
PROMPT_VERSION = "redact_fig9_v1text"
RUBRIC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts", "judge_redact_fig9.txt")).read().split("# ---")[0]
client = OpenAI(base_url=ENDPOINT, api_key=KEY)

_STEP_KEY_RE = re.compile(r"step\s*(\d+)", re.IGNORECASE)


def format_trajectory(task, steps):
    """Fig-9 rendering: Task + per-step action/observation, no thoughts (A7). Numbered from 1."""
    lines = ["Task: %s" % task]
    for i, s in enumerate(steps, 1):
        lines.append("step %d:" % i)
        lines.append("action: %s" % (s.get("action_parsed") or "").strip())
        lines.append("observation: %s" % (s.get("obs") or "").strip())
    return "\n".join(lines)


def parse_judge_json(text):
    """{position(1-based): (label, reason)} from a whole-trajectory judge reply; None if none."""
    if not text:
        return None
    t = re.sub(r"```(?:json)?", "", text).strip()
    lo, hi = t.find("{"), t.rfind("}")
    if lo < 0 or hi <= lo:
        return None
    try:
        obj = json.loads(t[lo:hi + 1])
    except json.JSONDecodeError:
        return None
    out = {}
    for k, v in obj.items():
        m = _STEP_KEY_RE.search(str(k))
        if not m or not isinstance(v, dict) or v.get("label") not in (0, 1):
            continue
        out[int(m.group(1))] = (int(v["label"]), str(v.get("reason", "")))
    return out or None


def ask(model, prompt, temperature):
    if model in RESPONSES_API:
        r = client.responses.create(model=model, input=prompt)
        return getattr(r, "output_text", None) or _extract_responses_text(r)
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}],
                                       temperature=temperature, max_tokens=2048)
    return r.choices[0].message.content or ""


def _extract_responses_text(r):
    try:
        out = r.output[-1]
        c = getattr(out, "content", None)
        if isinstance(c, list) and c:
            return getattr(c[0], "text", "") or ""
        return str(out)
    except Exception:
        return ""


def judge_trajectory(model, task, steps):
    """One whole-trajectory call; returns {position: (label, reason)} or None (unparsed)."""
    prompt = RUBRIC.replace("{TRAJECTORY}", format_trajectory(task, steps))
    for temp in (0.0, 0.2):
        try:
            txt = ask(model, prompt, temp)
        except Exception as e:
            sys.stderr.write("judge %s error: %r\n" % (model, e))
            continue
        parsed = parse_judge_json(txt)
        if parsed:
            return parsed
        if model in RESPONSES_API:
            break
    return None


def label_one(task_id, task, steps):
    """All judges label this trajectory; return per-step ensemble records."""
    per_model = {m: judge_trajectory(m, task, steps) for m in MODELS}
    recs = []
    for pos, s in enumerate(steps, 1):
        if not (s.get("action_parsed") or "").strip():
            continue
        votes = {}
        for m in MODELS:
            lab = (per_model[m] or {}).get(pos)
            # label 1 = good -> incorrect 0 ; label 0 = bad -> incorrect 1
            votes[m] = {"incorrect": (1 - lab[0]) if lab else None, "reason": lab[1][:80] if lab else None}
        vals = [votes[m]["incorrect"] for m in MODELS if votes[m]["incorrect"] is not None]
        unanimous = len(vals) == len(MODELS) and len(set(vals)) == 1
        recs.append({"kind": "judge", "run_id": s.get("run_id"), "task_id": task_id,
                     "step_idx": s.get("step_idx"), "action_parsed": s.get("action_parsed"),
                     "prompt_version": PROMPT_VERSION, "votes": votes, "n_valid": len(vals),
                     "unanimous": unanimous, "ensemble_incorrect": (vals[0] if unanimous else None),
                     "needs_human": not unanimous})
    return recs


def main():
    inp, out = os.environ.get("JUDGE_INPUT"), os.environ.get("JUDGE_OUTPUT")
    if not inp or not out:
        sys.exit("JUDGE_INPUT and JUDGE_OUTPUT required")
    if not KEY:
        sys.exit("AZURE_JUDGE_KEY not set")
    recs = [json.loads(l) for l in open(inp)]
    steps = [r for r in recs if r.get("kind") == "step"]
    by_task = {}
    for s in steps:
        by_task.setdefault(s["task_id"], []).append(s)
    for t in by_task:
        by_task[t].sort(key=lambda s: s.get("step_idx", 0))
    task_text = {}
    for r in recs:
        if r.get("kind") == "call" and r.get("prompt_templated") and r["task_id"] not in task_text:
            tt, _ = probes.parse_task_history(r["prompt_templated"])
            if tt:
                task_text[r["task_id"]] = tt

    done = set()
    if os.path.exists(out):
        for l in open(out):
            try:
                done.add(json.loads(l)["task_id"])
            except Exception:
                pass
    todo = [(t, s) for t, s in by_task.items() if t not in done]
    cap = os.environ.get("JUDGE_MAX_TRAJ")
    if cap:
        todo = todo[:int(cap)]
    print("judging %d trajectories x %d judges (workers=%d, whole-trajectory)" % (len(todo), len(MODELS), WORKERS))
    sys.stdout.flush()

    n_traj = n_rec = 0
    with open(out, "a") as fo, ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(label_one, t, task_text.get(t, t), s): t for t, s in todo}
        for fut in as_completed(futs):
            try:
                for rec in fut.result():
                    fo.write(json.dumps(rec) + "\n"); n_rec += 1
                fo.flush()
            except Exception as e:
                sys.stderr.write("trajectory %s failed: %r\n" % (futs[fut], e))
            n_traj += 1
            if n_traj % 20 == 0:
                print("...%d/%d trajectories (%d step-labels)" % (n_traj, len(todo), n_rec)); sys.stdout.flush()
    print("DONE: %d trajectories, %d step-labels -> %s" % (n_traj, n_rec, out))


if __name__ == "__main__":
    main()
