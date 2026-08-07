#!/usr/bin/env python3
"""S3 / b2 — decision-framed verdict.

Spec: docs/specs/S3_SPEC.md.

Prompt construction, which is the whole lesson of the S4 failure: the banked
`prompt_templated` already CLOSES the user turn and OPENS the assistant turn, so
appending text to it asks the model nothing -- it just continues the agent's
completion.  b2 therefore rebuilds the evidence as a chat MESSAGE and lets the server
apply its own template.

Blocking audit: after the first AUDIT_N records of a cell, the top-1 token must be
Yes/No in >= AUDIT_MIN of them, else the run halts.  A pass whose answers are not
answers is worse than no pass, because it looks like data.
"""
import argparse
import json
import math
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

try:
    from openai import OpenAI
except ImportError:                                   # pragma: no cover
    sys.exit("S3: openai client not installed")

AUDIT_N = 200
AUDIT_MIN = 0.90
QUESTION = ("Should this action be executed? Answer with a single word: Yes or No.")
YES = {"yes", "Yes", "YES", "yes.", "Yes."}
NO = {"no", "No", "NO", "no.", "No."}

# The banked prompt is a full chat template.  Strip the template scaffolding back to
# the human-readable context so it can be re-sent as a proper user message.
_TAGS = re.compile(r"<\|[^>]*\|>")


def context_of(prompt_templated):
    """Recover the evidence text from a templated prompt, dropping chat scaffolding."""
    t = _TAGS.sub("\n", prompt_templated)
    for marker in ("system", "user", "assistant"):
        t = re.sub(r"^\s*%s\s*$" % marker, "", t, flags=re.M)
    return t.strip()


def build_messages(prompt_templated, completion_raw):
    """A real user turn: evidence + the proposed step + the decision question."""
    ctx = context_of(prompt_templated)
    return [{"role": "user", "content":
             "%s\n\nPROPOSED STEP:\n%s\n\n%s" % (ctx, completion_raw.strip(), QUESTION)}]


def ptrue_from_top(top):
    py = pn = 0.0
    for t in top or []:
        tok = (t.get("token") or "").strip()
        lp = t.get("logprob")
        if lp is None:
            continue
        p = math.exp(lp)
        if tok in YES:
            py += p
        elif tok in NO:
            pn += p
    return None if py + pn <= 0 else pn / (py + pn)


def top1_verdict(top):
    if not top:
        return None
    best = max(top, key=lambda t: t["logprob"])
    tok = (best.get("token") or "").strip()
    return 0 if tok in YES else 1 if tok in NO else None


def load_arm(pivot, ds, model):
    p = os.path.join(pivot, ds, model, "uq.jsonl")
    out = []
    if not os.path.exists(p):
        return out
    for line in open(p):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("call_kind") not in (None, "joint"):
            continue
        if r.get("prompt_templated"):
            out.append((r.get("task_id"), r.get("step_idx", 0),
                        r["prompt_templated"], r.get("completion_raw") or ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--judge", required=True)
    ap.add_argument("--port", default="8095")
    ap.add_argument("--outdir", default="result/b2")
    ap.add_argument("--conc", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    cl = OpenAI(base_url="http://localhost:%s/v1" % a.port, api_key="x")
    import csv as _csv
    in_matrix = set()
    for x in _csv.DictReader(open(a.labels)):
        if x.get("in_matrix") == "1":
            in_matrix.add((x["dataset"], x["model"]))

    arms = []
    for ds in sorted(os.listdir(a.pivot)):
        d = os.path.join(a.pivot, ds)
        if ds == "crossprobe" or not os.path.isdir(d):
            continue
        for m in sorted(os.listdir(d)):
            if (ds, m) in in_matrix and os.path.exists(os.path.join(d, m, "uq.jsonl")):
                arms.append((ds, m))

    t0 = time.time()
    total = 0
    for ds, model in arms:
        outp = os.path.join(a.outdir, ds, model)
        os.makedirs(outp, exist_ok=True)
        path = os.path.join(outp, "b2.%s.jsonl" % a.judge)
        seen = set()
        if os.path.exists(path):
            for line in open(path):
                try:
                    r = json.loads(line)
                    seen.add((r["task_id"], r["step_idx"]))
                except (ValueError, KeyError):
                    pass
        steps = [s for s in load_arm(a.pivot, ds, model)
                 if (s[0], s[1]) not in seen]
        print("[%s] %s/%s: %d to score, %d already done"
              % (a.judge, ds, model, len(steps), len(seen)), flush=True)
        if not steps:
            continue
        fh = open(path, "a")
        lock = threading.Lock()
        audit = {"n": 0, "ok": 0}

        def do_one(s):
            task, sidx, pt, cr = s
            try:
                resp = cl.chat.completions.create(
                    model="probe", messages=build_messages(pt, cr),
                    max_tokens=1, temperature=0.0, logprobs=True, top_logprobs=20)
                lp = getattr(resp.choices[0], "logprobs", None)
                top = ([{"token": t.token, "logprob": t.logprob}
                        for t in lp.content[0].top_logprobs]
                       if lp and getattr(lp, "content", None) else [])
                v = top1_verdict(top)
                return {"task_id": task, "step_idx": sidx, "U": ptrue_from_top(top),
                        "first_token_top": top, "verdict": v,
                        "parse_ok": int(v is not None)}
            except Exception as e:                    # noqa: BLE001
                return {"task_id": task, "step_idx": sidx, "U": None,
                        "first_token_top": [], "verdict": None, "parse_ok": 0,
                        "error": repr(e)[:200]}

        with ThreadPoolExecutor(max_workers=a.conc) as ex:
            for rec in ex.map(do_one, steps):
                with lock:
                    fh.write(json.dumps(rec) + "\n")
                    total += 1
                    if audit["n"] < AUDIT_N:
                        audit["n"] += 1
                        audit["ok"] += rec["parse_ok"]
                        if audit["n"] == AUDIT_N:
                            rate = audit["ok"] / AUDIT_N
                            print("  AUDIT %s/%s: top-1 Yes/No in %.1f%% of first %d"
                                  % (ds, model, 100 * rate, AUDIT_N), flush=True)
                            if rate < AUDIT_MIN:
                                fh.close()
                                sys.exit(
                                    "S3 HALT: %s/%s parse rate %.1f%% < %.0f%%. The "
                                    "model is not answering the question; do not "
                                    "treat these records as data."
                                    % (ds, model, 100 * rate, 100 * AUDIT_MIN))
                    if total % 500 == 0:
                        fh.flush()
                        el = time.time() - t0
                        print("  %s/%s total=%d %.2f/s" % (ds, model, total,
                                                           total / el), flush=True)
                if a.limit and total >= a.limit:
                    break
        fh.close()
        print("[%s] %s/%s complete" % (a.judge, ds, model), flush=True)
    print("S3 b2 %s: %d scored in %.0f min" % (a.judge, total, (time.time() - t0) / 60),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
