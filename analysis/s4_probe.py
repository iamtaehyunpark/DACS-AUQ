#!/usr/bin/env python3
"""S4 throughput probe — measure the real rate on HINDSIGHT-LENGTH prompts.

STOP_GATE_DECISIONS.md D1.1 makes this condition one of the S4 approval, and
EXECUTION_HANDOVER.md §1 forbids any GPU stage sizing itself against the inherited
constant without it.

Why hindsight length specifically: the inherited 3,300 assessments / 5 min / A100 was
measured on the banked online prompts.  Hindsight prompts append the full trajectory
and the episode outcome, so they are several times longer, and prompt length is what
sets throughput here.  That is the most likely explanation for S4_COST's 1.3-3.9
A100-hours disagreeing with the handover's 6-10, and this probe decides it.

Writes the measured rate and the projected full-pass cost.  Runs no pass.
"""
import json
import os
import random
import sys
import time

try:
    from openai import OpenAI
except ImportError:                                   # pragma: no cover
    sys.exit("S4 probe: openai client not installed")

PORT = os.environ.get("PORT", "8071")
N = int(os.environ.get("N", "500"))
JUDGE = os.environ.get("JUDGE", "?")
OUT = os.environ.get("OUT", "runs/s4_probe.json")
PIVOT = os.environ.get("PIVOT", "result/pivot")
CEILING_HOURS = 10.0          # D1 budget ceiling
FULL_ASSESSMENTS = 77026      # S4_COST exact count
SEED = 13


def build_episodes(pivot, limit_arms=8):
    """{(ds, model, task_id): [(step_idx, prompt_templated, completion_raw)]}

    Reads the banked uq.jsonl.  The schema is prompt_templated / completion_raw /
    task_id / step_idx -- the earlier version of this probe guessed field names that
    do not exist, got empty strings, and timed ~91-token prompts, which is exactly the
    flattering measurement this probe exists to prevent.
    """
    eps = {}
    arms = 0
    for ds in sorted(os.listdir(pivot)):
        d = os.path.join(pivot, ds)
        if ds == "crossprobe" or not os.path.isdir(d):
            continue
        for m in sorted(os.listdir(d)):
            p = os.path.join(d, m, "uq.jsonl")
            if not os.path.exists(p):
                continue
            arms += 1
            if arms > limit_arms:
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
                    cr = r.get("completion_raw") or ""
                    if not pt:
                        continue
                    eps.setdefault((ds, m, r.get("task_id")), []).append(
                        (r.get("step_idx", 0), pt, cr))
    return eps


def hindsight_prompt(steps, i, outcome):
    """Online prompt for step i + the FULL trajectory including everything after it +
    the episode outcome.  Length is the quantity under test."""
    _idx, prompt, _c = steps[i]
    tail = "\n".join("STEP %d:\n%s" % (s[0], s[2]) for s in steps)
    return (prompt
            + "\n\n--- HINDSIGHT CONTEXT ---\n"
              "FULL TRAJECTORY (including everything after this step):\n%s\n\n"
              "EPISODE OUTCOME: %s\n\n"
              "Is the proposed action at this step the correct and appropriate next "
              "action for this task?\nAnswer with a single word: Yes or No."
              % (tail, outcome))


def episode_outcomes(labels_csv):
    """(dataset, model, task_id) -> SUCCEEDED / FAILED / UNKNOWN."""
    import csv as _csv
    out = {}
    if not os.path.exists(labels_csv):
        return out
    with open(labels_csv) as f:
        for x in _csv.DictReader(f):
            v = x.get("episode_success", "")
            out[(x["dataset"], x["model"], x["task_id"])] = (
                "SUCCEEDED" if v in ("1", "True", "true") else
                "FAILED" if v in ("0", "False", "false") else "UNKNOWN")
    return out


def main():
    rng = random.Random(SEED)
    eps = build_episodes(PIVOT)
    outc = episode_outcomes(os.environ.get("LABELS",
                                           "reports/gate1/labels_gate1.csv"))
    keys = [k for k, v in eps.items() if len(v) >= 2]
    if not keys:
        sys.exit("S4 probe: no usable episodes under %s" % PIVOT)
    rng.shuffle(keys)
    prompts = []
    for k in keys:
        steps = sorted(eps[k], key=lambda s: s[0])
        i = rng.randrange(len(steps))
        prompts.append(hindsight_prompt(steps, i, outc.get(k, "UNKNOWN")))
        if len(prompts) >= N:
            break
    approx_tok = [len(p) // 4 for p in prompts]     # ~4 chars/token, for reporting only
    # A hindsight prompt is the online prompt (~330 tokens) plus the whole trajectory.
    # If the mean comes out near the online length, the reconstruction is broken and
    # the measured rate is meaningless -- fail loudly rather than report it.
    if sum(approx_tok) / len(approx_tok) < 600:
        sys.exit("S4 probe: mean prompt %d tokens — that is online length, not "
                 "hindsight. Reconstruction is broken; refusing to report a rate."
                 % (sum(approx_tok) / len(approx_tok)))

    cl = OpenAI(base_url="http://localhost:%s/v1" % PORT, api_key="x")
    t0 = time.time()
    done = err = 0
    for p in prompts:
        try:
            cl.chat.completions.create(
                model="probe", messages=[{"role": "user", "content": p}],
                max_tokens=1, temperature=0.0, logprobs=True, top_logprobs=20)
            done += 1
        except Exception:                            # noqa: BLE001
            err += 1
    dt = time.time() - t0

    rate_5min = (done / dt) * 300.0 if dt > 0 else 0.0
    hours_1gpu = FULL_ASSESSMENTS / (done / dt) / 3600.0 if done and dt else None
    out = {
        "judge": JUDGE, "n_requested": N, "n_ok": done, "n_err": err,
        "seconds": round(dt, 1),
        "assessments_per_5min_per_gpu": round(rate_5min, 1),
        "inherited_constant": 3300,
        "prompt_tokens_approx_mean": int(sum(approx_tok) / len(approx_tok)),
        "prompt_tokens_approx_max": max(approx_tok),
        "full_pass_assessments": FULL_ASSESSMENTS,
        "projected_a100_hours": round(hours_1gpu, 2) if hours_1gpu else None,
        "ceiling_hours": CEILING_HOURS,
    }
    out["within_ceiling"] = (hours_1gpu is not None and hours_1gpu <= CEILING_HOURS)
    out["decision"] = ("PROCEED — projected cost is within the D1 ceiling"
                       if out["within_ceiling"] else
                       "RE-HALT — projected cost exceeds the D1 ceiling; D1.2 requires "
                       "returning to the author with the measured number")
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    for k, v in out.items():
        print("%-34s %s" % (k, v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
