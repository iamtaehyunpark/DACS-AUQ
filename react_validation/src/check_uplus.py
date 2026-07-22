"""check_uplus — exercise the E3 post-transition re-elicitation (u+) JOIN once, on a smoke corpus.

E3's promise check anchors on u_t- (in-gen u(q_t): the declared THOUGHT_TARGET at step t) and
u_t+ = re-elicited confidence in that SAME q_t string AFTER the step-t transition (given S_{t+1}).
Per A19, u+ is a **probe-style, value-excised call** — the SAME template family as the post-hoc
targeted probe (probes.prompt_targeted): environment history through S_{t+1} + the declared q_t
posed as a standalone "how confident this claim is true" question, with NO agent framing and NO
continuation of the agent context. (An earlier agent-context version returned agent prose, not a
confidence — exactly the failure A19 fixes; kept out here on purpose.) The u+ reading is logged
under U_T_targeted_uplus in E3; this script only proves the join wiring + prompt style produce a
clean number. Read-only; never fed back.

Usage: python check_uplus.py <decoupled_uq_log.jsonl> [K]
"""
import json, os, re, sys
from openai import OpenAI
import probes

NUM = re.compile(r"([0-9]*\.?[0-9]+)")
path = sys.argv[1]
K = int(sys.argv[2]) if len(sys.argv) > 2 else 5
recs = [json.loads(l) for l in open(path)]

# the NEXT step's thought call carries the context (history through S_{t+1}) we re-score q_t against
tcall = {(r["task_id"], r["step_idx"]): r for r in recs
         if r.get("kind") == "call" and r.get("call_kind") == "thought"}
steps = {(r["task_id"], r["step_idx"]): r for r in recs if r.get("kind") == "step"}

client = OpenAI(api_key="EMPTY", base_url=os.environ.get("PROBE_BASE_URL", "http://localhost:8000/v1"))
model = os.environ.get("PROBE_MODEL", "qwen")
ok = tot = 0
for (task, si), st in sorted(steps.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
    q = st.get("q_t_text")
    nxt = tcall.get((task, si + 1))
    nstep = steps.get((task, si + 1))
    if not q or nxt is None:
        continue
    if tot >= K:
        break
    tot += 1
    # value-excised probe context at t+1 (A19): reuse the post-hoc targeted template, same q_t string
    task_txt, history = probes.parse_task_history(nxt.get("prompt_templated", ""))
    commands = "\n".join((nstep or {}).get("admissible") or [])
    prompt = probes.prompt_targeted(task_txt, history, commands, q)
    try:
        r = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}], temperature=0, max_tokens=16,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}})
        txt = (r.choices[0].message.content or "").strip()
        m = NUM.search(txt)
        val = float(m.group(1)) if m else None
        good = val is not None and 0.0 <= val <= 1.0
        ok += 1 if good else 0
        print("  u+ %s step %d->%d: q_t=%r -> %r %s" % (task, si, si + 1, q[:45], txt[:16],
                                                        "ok" if good else "UNPARSED/NOT-A-NUMBER"))
    except Exception as e:
        print("  u+ %s step %d ERROR: %r" % (task, si, e))
print("u+ re-elicitation join (probe-style, value-excised): %d/%d clean number" % (ok, tot))
sys.exit(0 if (tot == 0 or ok == tot) else 1)
