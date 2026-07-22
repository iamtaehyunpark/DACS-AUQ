"""check_uplus — exercise the E3 post-transition re-elicitation JOIN once, on a smoke corpus.

E3's promise check anchors on u_t- = in-gen u(q_t) (the declared THOUGHT_TARGET at step t) and
u_t+ = re-elicited confidence in that SAME q_t string AFTER the step-t transition (given S_{t+1}).
This script does NOT compute E3; it only proves the join wiring works — declared q_t at step t is
recoverable and can be re-scored against the next step's context — so a join bug surfaces in the
gate run, not during E3 analysis. Read-only; never fed back into any agent context.

Usage: python check_uplus.py <decoupled_uq_log.jsonl> [K]
  For up to K steps that (a) have a parsed q_t_text and (b) have a following step in the same
  episode, re-elicit P(q_t true | S_{t+1}) using the next thought-call's context (which already
  contains the post-transition observation) and confirm a number in [0,1] parses.
"""
import json, os, re, sys
from openai import OpenAI

NUM = re.compile(r"([0-9]*\.?[0-9]+)")
path = sys.argv[1]
K = int(sys.argv[2]) if len(sys.argv) > 2 else 5
recs = [json.loads(l) for l in open(path)]

# next-step thought call carries the context (history through S_{t+1}) we re-score q_t against
tcall = {(r["task_id"], r["step_idx"]): r for r in recs
         if r.get("kind") == "call" and r.get("call_kind") == "thought"}
steps = {(r["task_id"], r["step_idx"]): r for r in recs if r.get("kind") == "step"}

client = OpenAI(api_key="EMPTY", base_url=os.environ.get("PROBE_BASE_URL", "http://localhost:8000/v1"))
ok = tot = 0
for (task, si), st in sorted(steps.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
    q = st.get("q_t_text")
    nxt = tcall.get((task, si + 1))
    if not q or nxt is None:
        continue
    if tot >= K:
        break
    tot += 1
    ctx = nxt.get("prompt_templated", "")
    prompt = (ctx.rstrip()
              + "\n\nNow, given everything above (including the most recent observation), state your "
                "confidence that the following claim is TRUE:\nCLAIM: %s\n"
                "Answer with a single number from 0.00 to 1.00 and nothing else.\nANSWER:" % q)
    try:
        r = client.chat.completions.create(
            model=os.environ.get("PROBE_MODEL", "qwen"),
            messages=[{"role": "user", "content": prompt}], temperature=0, max_tokens=16,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}})
        txt = (r.choices[0].message.content or "").strip()
        m = NUM.search(txt)
        val = float(m.group(1)) if m else None
        good = val is not None and 0.0 <= val <= 1.0
        ok += 1 if good else 0
        print("  u+ %s step %d->%d: q_t=%r -> %r %s" % (task, si, si + 1, q[:45], txt[:16],
                                                        "ok" if good else "UNPARSED"))
    except Exception as e:
        print("  u+ %s step %d ERROR: %r" % (task, si, e))
print("u+ re-elicitation join: %d/%d parseable" % (ok, tot))
sys.exit(0 if (tot == 0 or ok == tot) else 1)
