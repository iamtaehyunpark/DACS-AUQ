"""E0 v3 (A14) — adjudicated three-judge ensemble labeler.

Labels every step of a generated corpus with THREE API judges (three families, disjoint from the
Qwen agent), using the Fig-9 v2 rendering: ACTIONS + OBSERVATIONS ONLY, no thoughts (A7,
architecture-invariant). Per-judge votes are stored; unanimous -> ensemble label; any disagreement
(2-1 included) -> needs_human=True (adjudicated separately). AUROC convention: incorrect = positive.

Judges (Azure AI, one endpoint+key): grok-4.3, DeepSeek-V4-Pro via chat.completions; gpt-5.6-sol
via the responses API (it locks temperature=1.0, so no T sent). T=0 for the first two; one retry
at T=0.2 on unparseable output; then vote null (counted). Resumable: skips (task,step) already in
the output.

Config (env):
  JUDGE_INPUT   (required)  generated uq_log jsonl (step + call records)
  JUDGE_OUTPUT  (required)  judge-log jsonl (append; resumable)
  AZURE_JUDGE_ENDPOINT (https://.../openai/v1)   AZURE_JUDGE_KEY
  JUDGE_MODELS  (grok-4.3,DeepSeek-V4-Pro,gpt-5.6-sol)
  JUDGE_MAX_STEPS (unset -> all)

NOTE: the exact ReDAct Fig-9 rubric text is not in the repo; the prompt below is a faithful
step-correctness rendering and is FLAGGED for PI review (prompt_version 'fig9_v2_draft').
"""
import json, os, re, sys, time
from openai import OpenAI

ENDPOINT = os.environ.get("AZURE_JUDGE_ENDPOINT", "https://llmjudgejul20-resource.services.ai.azure.com/openai/v1")
KEY = os.environ.get("AZURE_JUDGE_KEY", "")
MODELS = [m.strip() for m in os.environ.get("JUDGE_MODELS", "grok-4.3,DeepSeek-V4-Pro,gpt-5.6-sol").split(",") if m.strip()]
RESPONSES_API = {"gpt-5.6-sol"}          # uses client.responses.create, locks temperature
PROMPT_VERSION = "fig9_v2_draft"
client = OpenAI(base_url=ENDPOINT, api_key=KEY)

_VERDICT = re.compile(r"\b(INCORRECT|CORRECT)\b", re.IGNORECASE)


def render(steps_sorted, upto_idx):
    """Fig-9 v2 rendering: actions + observations only, no thoughts, through step upto_idx."""
    lines = []
    for k, s in enumerate(steps_sorted[:upto_idx + 1], 1):
        lines.append("Step %d:\n  Action: %s\n  Observation: %s" % (
            k, (s.get("action_parsed") or "").strip(), (s.get("obs") or "").strip()))
    return "\n".join(lines)


def judge_prompt(task, rendered, step_no):
    return (
        "You are an expert evaluator of an agent solving a household task in a text-based "
        "environment. You see only the actions the agent took and the environment's observations "
        "(no private reasoning).\n\n"
        "TASK: %s\n\n"
        "TRAJECTORY SO FAR (actions and observations only):\n%s\n\n"
        "Evaluate ONLY the action taken at Step %d. Given the task and everything observed up to "
        "and including that step, was that action a correct and appropriate step toward "
        "accomplishing the task?\n"
        "Answer with exactly one word: CORRECT or INCORRECT." % (task, rendered, step_no))


def ask(model, prompt, temperature):
    if model in RESPONSES_API:
        r = client.responses.create(model=model, input=prompt)
        return getattr(r, "output_text", None) or _extract_responses_text(r)
    kw = {} if model in RESPONSES_API else {"temperature": temperature}
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}],
                                       max_tokens=8, **kw)
    return r.choices[0].message.content or ""


def _extract_responses_text(r):
    try:
        out = r.output[0]
        c = getattr(out, "content", None)
        if isinstance(c, list) and c:
            return getattr(c[0], "text", "") or ""
        return str(out)
    except Exception:
        return ""


def verdict(model, prompt):
    txt = ""
    for temp in (0.0, 0.2):
        try:
            txt = ask(model, prompt, temp)
        except Exception as e:
            sys.stderr.write("judge %s error: %r\n" % (model, e))
            time.sleep(2)
            continue
        m = _VERDICT.search(txt or "")
        if m:
            return 1 if m.group(1).upper() == "INCORRECT" else 0, (txt or "").strip()[:60]
        if model in RESPONSES_API:
            break  # temperature-locked; retry won't differ
    return None, (txt or "").strip()[:60]


def main():
    inp, out = os.environ.get("JUDGE_INPUT"), os.environ.get("JUDGE_OUTPUT")
    if not inp or not out:
        sys.exit("JUDGE_INPUT and JUDGE_OUTPUT required")
    if not KEY:
        sys.exit("AZURE_JUDGE_KEY not set")
    recs = [json.loads(l) for l in open(inp)]
    steps = [r for r in recs if r.get("kind") == "step"]
    # group by episode (task_id), ordered by step_idx, to render trajectories
    by_task = {}
    for s in steps:
        by_task.setdefault(s["task_id"], []).append(s)
    for t in by_task:
        by_task[t].sort(key=lambda s: s.get("step_idx", 0))

    done = set()
    if os.path.exists(out):
        for l in open(out):
            try:
                r = json.loads(l)
                done.add((r["task_id"], r["step_idx"]))
            except Exception:
                pass
    max_steps = os.environ.get("JUDGE_MAX_STEPS")
    max_steps = int(max_steps) if max_steps else None

    n = 0
    with open(out, "a") as fo:
        for task_id, seq in by_task.items():
            task = _task_of(recs, task_id)
            for i, s in enumerate(seq):
                key = (task_id, s.get("step_idx"))
                if key in done:
                    continue
                if max_steps is not None and n >= max_steps:
                    break
                if not (s.get("action_parsed") or "").strip():
                    continue
                rendered = render(seq, i)
                prompt = judge_prompt(task, rendered, i + 1)
                votes = {}
                for mdl in MODELS:
                    v, raw = verdict(mdl, prompt)
                    votes[mdl] = {"incorrect": v, "raw": raw}
                vals = [votes[m]["incorrect"] for m in MODELS if votes[m]["incorrect"] is not None]
                unanimous = len(set(vals)) == 1 and len(vals) == len(MODELS)
                ensemble = vals[0] if unanimous else None
                rec = {"kind": "judge", "run_id": s.get("run_id"), "task_id": task_id,
                       "step_idx": s.get("step_idx"), "action_parsed": s.get("action_parsed"),
                       "prompt_version": PROMPT_VERSION, "votes": votes,
                       "n_valid": len(vals), "unanimous": unanimous,
                       "ensemble_incorrect": ensemble, "needs_human": not unanimous}
                fo.write(json.dumps(rec) + "\n"); fo.flush()
                n += 1
                if n % 20 == 0:
                    print("judged %d steps..." % n); sys.stdout.flush()
    print("DONE: judged %d new steps -> %s" % (n, out))


def _task_of(recs, task_id):
    # recover the task description from any thought/joint call's prompt for this episode
    import probes
    for r in recs:
        if r.get("kind") == "call" and r.get("task_id") == task_id and r.get("prompt_templated"):
            task, _ = probes.parse_task_history(r["prompt_templated"])
            if task:
                return task
    return task_id


if __name__ == "__main__":
    main()
