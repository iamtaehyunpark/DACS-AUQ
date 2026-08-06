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


def hindsight_prompt(rec):
    """Online prefix + the full trajectory tail + episode outcome.

    The point of the probe is the LENGTH, so this reconstructs a realistic hindsight
    context from the banked record rather than a short stand-in.
    """
    task = rec.get("task") or rec.get("goal") or ""
    hist = rec.get("history") or rec.get("prefix") or ""
    if isinstance(hist, list):
        hist = "\n".join(str(h) for h in hist)
    full = rec.get("full_trajectory") or rec.get("trajectory") or ""
    if isinstance(full, list):
        full = "\n".join(str(h) for h in full)
    thought = rec.get("thought") or ""
    action = rec.get("action_parsed") or rec.get("action") or ""
    outcome = rec.get("episode_success")
    outcome_s = ("SUCCEEDED" if outcome in (1, True, "1", "true")
                 else "FAILED" if outcome is not None else "UNKNOWN")
    return (
        "You are reviewing one step of an agent trajectory, WITH HINDSIGHT.\n\n"
        "TASK:\n%s\n\nHISTORY UP TO THIS STEP:\n%s\n\n"
        "FULL TRAJECTORY (including everything after this step):\n%s\n\n"
        "EPISODE OUTCOME: %s\n\n"
        "AGENT REASONING:\n%s\nPROPOSED ACTION:\n%s\n\n"
        "Is the proposed action above the correct and appropriate next action for "
        "this task?\nAnswer with a single word: Yes or No."
        % (task, hist, full, outcome_s, thought, action))


def sample_records(n, rng):
    """Pull n real step records from the banked uq files, across arms."""
    recs = []
    for ds in sorted(os.listdir(PIVOT)):
        d = os.path.join(PIVOT, ds)
        if ds == "crossprobe" or not os.path.isdir(d):
            continue
        for m in sorted(os.listdir(d)):
            p = os.path.join(d, m, "uq.jsonl")
            if not os.path.exists(p):
                continue
            take = 0
            with open(p) as f:
                for line in f:
                    if take >= max(1, n // 8):
                        break
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if r.get("thought") or r.get("action_parsed"):
                        recs.append(r)
                        take += 1
            if len(recs) >= n * 2:
                break
        if len(recs) >= n * 2:
            break
    rng.shuffle(recs)
    return recs[:n]


def main():
    rng = random.Random(SEED)
    recs = sample_records(N, rng)
    if not recs:
        sys.exit("S4 probe: no usable records under %s" % PIVOT)
    prompts = [hindsight_prompt(r) for r in recs]
    approx_tok = [len(p) // 4 for p in prompts]     # ~4 chars/token, for reporting only

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
