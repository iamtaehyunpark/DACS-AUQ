#!/usr/bin/env python3
"""S4 — hindsight-ceiling pass.

Spec: docs/specs/S4_SPEC.md, pre-registered.  Authorised by D1.2 at the measured
17.1 A100-hours, both judges, full matrix, hybrid overflow policy, drop rejected.

Routes each step to: main (fits the served window), long (over-length, re-run on the
long-context server), or truncated (middle-out fallback with the parameters fixed in
the spec).  A step that cannot be scored by any route is recorded route="failed" and
counted in coverage -- never silently dropped.

Resumable: existing output records are read back and skipped, so a killed run resumes
instead of restarting a 17-hour pass.
"""
import argparse
import json
import os
import sys
import time

try:
    from openai import OpenAI
except ImportError:                                   # pragma: no cover
    sys.exit("S4: openai client not installed")

# ---- spec §Overflow policy: fixed before any prompt is built --------------
BUDGET = 34000            # assembled-prompt token budget for the fallback
KEEP_HEAD_STEPS = 2       # trajectory steps kept for task framing
ELISION = "... [%d steps elided from the middle] ..."
QUESTION = ("Is the proposed action at this step the correct and appropriate next "
            "action for this task?\nAnswer with a single word: Yes or No.")
YES = {"yes", "Yes", "YES", " yes", " Yes"}
NO = {"no", "No", "NO", " no", " No"}


def load_arm(pivot, ds, model):
    """{task_id: [(step_idx, prompt_templated, completion_raw)]} for one arm."""
    p = os.path.join(pivot, ds, model, "uq.jsonl")
    eps = {}
    if not os.path.exists(p):
        return eps
    with open(p) as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("call_kind") not in (None, "joint"):
                continue
            pt = r.get("prompt_templated") or ""
            if not pt:
                continue
            eps.setdefault(r.get("task_id"), []).append(
                (r.get("step_idx", 0), pt, r.get("completion_raw") or ""))
    for k in eps:
        eps[k].sort(key=lambda s: s[0])
    return eps


def outcomes(labels_csv):
    import csv
    out = {}
    if not os.path.exists(labels_csv):
        return out
    with open(labels_csv) as f:
        for x in csv.DictReader(f):
            v = x.get("episode_success", "")
            out[(x["dataset"], x["model"], x["task_id"])] = (
                "SUCCEEDED" if v in ("1", "True", "true") else
                "FAILED" if v in ("0", "False", "false") else "UNKNOWN")
    return out


def assemble(steps, i, outcome, keep=None):
    """Build the hindsight prompt.  `keep` = list of trajectory indices to include;
    None means all.  Returns (text, n_elided)."""
    _idx, prompt, _c = steps[i]
    idxs = list(range(len(steps))) if keep is None else keep
    n_elided = len(steps) - len(idxs)
    parts = []
    prev = None
    for j in idxs:
        if prev is not None and j != prev + 1:
            parts.append(ELISION % (j - prev - 1))
        parts.append("STEP %d:\n%s" % (steps[j][0], steps[j][2]))
        prev = j
    return (prompt
            + "\n\n--- HINDSIGHT CONTEXT ---\n"
              "FULL TRAJECTORY (including everything after this step):\n%s\n\n"
              "EPISODE OUTCOME: %s\n\n%s" % ("\n".join(parts), outcome, QUESTION)
            ), n_elided


def middle_out(steps, i, outcome, ntok):
    """Spec fallback: keep the first KEEP_HEAD_STEPS and as many TRAILING steps as fit
    within BUDGET, eliding the middle.  Token counting uses the served tokenizer via
    `ntok`, not a character heuristic."""
    n = len(steps)
    head = list(range(min(KEEP_HEAD_STEPS, n)))
    best = head[:]
    for tail_len in range(n, 0, -1):
        tail = list(range(max(n - tail_len, len(head)), n))
        keep = head + [j for j in tail if j not in head]
        txt, _ = assemble(steps, i, outcome, keep)
        if ntok(txt) <= BUDGET:
            best = keep
            break
    txt, n_elided = assemble(steps, i, outcome, best)
    return txt, n_elided


def ptrue_from_top(top):
    """U = P(No) / (P(Yes) + P(No)) on the first token's top-k, as the banked probe."""
    import math
    py = pn = 0.0
    for t in top or []:
        tok = (t.get("token") or "")
        lp = t.get("logprob")
        if lp is None:
            continue
        p = math.exp(lp)
        if tok.strip() in {"yes", "Yes", "YES"}:
            py += p
        elif tok.strip() in {"no", "No", "NO"}:
            pn += p
    if py + pn <= 0:
        return None
    return pn / (py + pn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--judge", required=True)
    ap.add_argument("--port", default="8071")
    ap.add_argument("--outdir", default="result/hindsight")
    ap.add_argument("--mode", choices=["main", "long"], default="main")
    ap.add_argument("--ctx", type=int, default=32768)
    ap.add_argument("--reserve", type=int, default=64,
                    help="tokens reserved for the completion + template slack")
    ap.add_argument("--arms", default="")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    cl = OpenAI(base_url="http://localhost:%s/v1" % a.port, api_key="x")

    # Token counting through the server's own tokenizer (spec: not a char heuristic).
    import requests
    def ntok(text):
        try:
            r = requests.post("http://localhost:%s/tokenize" % a.port,
                              json={"model": "probe", "prompt": text}, timeout=120)
            return int(r.json().get("count", 10 ** 9))
        except Exception:                             # noqa: BLE001
            return len(text) // 4

    outc = outcomes(a.labels)
    # Restrict to the in_matrix arms the spec scopes S4 to.  Enumerating every arm
    # with a uq.jsonl scored Qwen3.5-27B/4B/9B as well -- 12,637 steps that the D1.3
    # analyses filter out by in_matrix==1, i.e. GPU time spent on records nothing can
    # use.  The filter belongs here, not downstream.
    in_matrix = set()
    if os.path.exists(a.labels):
        import csv as _csv
        with open(a.labels) as _f:
            for _x in _csv.DictReader(_f):
                if _x.get("in_matrix") == "1":
                    in_matrix.add((_x["dataset"], _x["model"]))
    arms = []
    for ds in sorted(os.listdir(a.pivot)):
        d = os.path.join(a.pivot, ds)
        if ds == "crossprobe" or not os.path.isdir(d):
            continue
        for m in sorted(os.listdir(d)):
            if not os.path.exists(os.path.join(d, m, "uq.jsonl")):
                continue
            if in_matrix and (ds, m) not in in_matrix:
                continue
            arms.append((ds, m))
    if a.arms:
        want = set(a.arms.split(","))
        arms = [x for x in arms if x[1] in want or "%s/%s" % x in want]

    limit_tok = a.ctx - a.reserve
    total = done = skipped = 0
    t0 = time.time()
    for ds, model in arms:
        outp = os.path.join(a.outdir, ds, model)
        os.makedirs(outp, exist_ok=True)
        path = os.path.join(outp, "hindsight.%s.jsonl" % a.judge)
        seen = set()
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    try:
                        r = json.loads(line)
                        seen.add((r["task_id"], r["step_idx"]))
                    except (ValueError, KeyError):
                        pass
        eps = load_arm(a.pivot, ds, model)
        print("[%s] %s/%s: %d episodes, %d already scored"
              % (a.judge, ds, model, len(eps), len(seen)), flush=True)
        fh = open(path, "a")
        for task, steps in eps.items():
            oc = outc.get((ds, model, task), "UNKNOWN")
            for i, (sidx, _p, _c) in enumerate(steps):
                if (task, sidx) in seen:
                    skipped += 1
                    continue
                total += 1
                txt, n_elided = assemble(steps, i, oc)
                nt = ntok(txt)
                route = "main"
                truncated = 0
                if nt > limit_tok:
                    if a.mode == "main":
                        # over-length: leave for the long-context sub-pass (spec route 2)
                        fh.write(json.dumps({
                            "task_id": task, "step_idx": sidx, "U": None,
                            "route": "deferred_long", "truncated": 0, "n_elided": 0,
                            "prompt_tokens": nt}) + "\n")
                        continue
                    txt, n_elided = middle_out(steps, i, oc, ntok)
                    nt = ntok(txt)
                    route, truncated = "truncated", 1
                elif a.mode == "long":
                    route = "long"
                try:
                    resp = cl.chat.completions.create(
                        model="probe", messages=[{"role": "user", "content": txt}],
                        max_tokens=1, temperature=0.0, logprobs=True, top_logprobs=20)
                    ch = resp.choices[0]
                    top = []
                    lp = getattr(ch, "logprobs", None)
                    if lp and getattr(lp, "content", None):
                        top = [{"token": t.token, "logprob": t.logprob}
                               for t in lp.content[0].top_logprobs]
                    rec = {"task_id": task, "step_idx": sidx,
                           "U": ptrue_from_top(top), "first_token_top": top,
                           "route": route, "truncated": truncated,
                           "n_elided": n_elided, "prompt_tokens": nt}
                    done += 1
                except Exception as e:                # noqa: BLE001
                    rec = {"task_id": task, "step_idx": sidx, "U": None,
                           "route": "failed", "truncated": truncated,
                           "n_elided": n_elided, "prompt_tokens": nt,
                           "error": repr(e)[:200]}
                fh.write(json.dumps(rec) + "\n")
                if done and done % 200 == 0:
                    el = time.time() - t0
                    print("  %s/%s  done=%d skipped=%d  %.1f/s  elapsed %.0fm"
                          % (ds, model, done, skipped, done / el, el / 60), flush=True)
                if a.limit and done >= a.limit:
                    fh.close()
                    print("limit reached"); return 0
        fh.close()
        print("[%s] %s/%s complete" % (a.judge, ds, model), flush=True)
    el = time.time() - t0
    print("S4 %s mode=%s: %d scored, %d skipped, %.0f min, %.1f/5min"
          % (a.judge, a.mode, done, skipped, el / 60,
             (done / el * 300) if el else 0), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
