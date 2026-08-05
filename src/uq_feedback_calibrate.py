"""Calibrate the uncertainty-feedback warning threshold for a (domain, arm).

The threshold is defined as the MEAN U OF JUDGE-INCORRECT STEPS under the arm's own measurement
prompt, so the two feedback arms warn at comparable rates. alfworld/prod, alfworld/c5 and
hotpot/prod already exist (PTRUE_CTXRULE_REPORT n=300 and runs/hotpot_500); hotpot/c5 has never
been measured, because the C5 prompt was only ever run on ALFWorld.

Reads a frozen corpus, re-measures a sample of judged steps with the arm's prompt, prints the
mean for incorrect and correct steps. Nothing is re-run and no agent is touched.

  python uq_feedback_calibrate.py --uq runs/hotpot_500/uq_hotpot_entangled.jsonl \
      --judge runs/hotpot_500/judge_hotpot_entangled.jsonl --domain hotpot --arm c5 --n 150
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import probes
import run_probes
import uq_feedback_common as F
from ptrue_context_rule_probe import _judge_label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uq", required=True)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--domain", required=True, choices=["alfworld", "hotpot"])
    ap.add_argument("--arm", required=True, choices=["prod", "c5"])
    ap.add_argument("--n", type=int, default=150, help="incorrect steps to sample")
    ap.add_argument("--model", default=os.environ.get("PROBE_MODEL", "qwen"))
    ap.add_argument("--tokenizer", default=os.environ.get("PROBE_TOKENIZER", "Qwen/Qwen3.6-35B-A3B"))
    ap.add_argument("--base-url", default=os.environ.get("PROBE_BASE_URL", "http://localhost:8000/v1"))
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--out", default=None, help="optional JSONL of the raw measurements")
    a = ap.parse_args()

    judge = {}
    for line in open(a.judge):
        if line.strip():
            r = json.loads(line)
            if r.get("kind") == "judge":
                judge[(r.get("task_id"), r.get("step_idx"))] = r
    records = [json.loads(l) for l in open(a.uq) if l.strip()]
    # the observation each action produced — needed for the c5 prompt
    obs = {(r.get("task_id"), r.get("step_idx")): r.get("obs")
           for r in records if r.get("kind") == "step"}

    pool = []
    for s in run_probes.group_steps(records):
        k = (s["task_id"], s["step_idx"])
        jr = judge.get(k)
        if jr is None:
            continue
        label, _ni, _nv = _judge_label(jr)
        if label is None or not s["ctx"].get("action") or obs.get(k) is None:
            continue
        pool.append((label, s, obs[k]))

    inc = [p for p in pool if p[0] == 1][:a.n]
    cor = [p for p in pool if p[0] == 0][:a.n]
    print("pool: %d unanimous steps (%d incorrect / %d correct); measuring %d + %d with arm=%s"
          % (len(pool), sum(1 for p in pool if p[0] == 1), sum(1 for p in pool if p[0] == 0),
             len(inc), len(cor), a.arm))

    from openai import OpenAI
    client = OpenAI(api_key="EMPTY", base_url=a.base_url)
    cfg = probes.ProbeConfig(model=a.model, tokenizer_path=a.tokenizer, base_url=a.base_url,
                             temperature=0.0, top_p=1.0, top_k=20, min_p=0.0,
                             presence_penalty=0.0, repetition_penalty=1.0, seed_base=9000)

    def one(item):
        label, s, o = item
        ctx = s["ctx"]
        try:
            U, ok, prompt, _rec = F.measure_u(
                client, cfg, a.domain, a.arm, task=ctx["task"], history=ctx["history"],
                commands=ctx["commands"], thought=ctx["thought"], action=ctx["action"], obs=o,
                seed=9000 + (s["step_idx"] or 0))
        except Exception as e:
            sys.stderr.write("ERROR %s/%s: %r\n" % (s["task_id"], s["step_idx"], e))
            return None
        return {"task_id": s["task_id"], "step_idx": s["step_idx"], "label": label,
                "U": U, "parse_ok": ok, "arm": a.arm, "domain": a.domain}

    with cf.ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        res = [r for r in ex.map(one, inc + cor) if r]
    if a.out:
        with open(a.out, "w") as f:
            for r in res:
                f.write(json.dumps(r) + "\n")

    ui = [r["U"] for r in res if r["label"] == 1 and r["U"] is not None]
    uc = [r["U"] for r in res if r["label"] == 0 and r["U"] is not None]
    print("\nparse_ok %d/%d" % (sum(1 for r in res if r["parse_ok"]), len(res)))
    if ui:
        print("mean U INCORRECT = %.4f  (median %.4f, n=%d)   <- THE THRESHOLD"
              % (statistics.fmean(ui), statistics.median(ui), len(ui)))
    if uc:
        print("mean U correct   = %.4f  (median %.4f, n=%d)"
              % (statistics.fmean(uc), statistics.median(uc), len(uc)))
    if ui and uc:
        print("separation Delta = %.4f" % (statistics.fmean(ui) - statistics.fmean(uc)))
        print("\nSet:  UQFB_THRESH_%s_%s=%.4f" % (a.domain.upper(), a.arm.upper(),
                                                  statistics.fmean(ui)))


if __name__ == "__main__":
    main()
