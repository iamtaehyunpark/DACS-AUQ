#!/usr/bin/env python3
"""E1 raw per-step diagnostics for visualization. Read-only; JSON to stdout.
Ground-truth failure signal = next step's observation is 'Nothing happens.' (a no-op).
Mechanism taxonomy (decoupled family) comes from extra.action_generation."""
import json, re, sys
from collections import Counter, defaultdict

TRAJ = "data/trajectories"
RUNS = {
    "decoupled":     (f"{TRAJ}/e1_primary_decoupled.jsonl",     "v2 primary · cells C+D"),
    "noconf_v1":     (f"{TRAJ}/e1b_contam_decoupled_noconf.jsonl","v1 anchor"),
    "entangled_auq": (f"{TRAJ}/e1_primary_entangled_auq.jsonl",  "cells A+B"),
}
SP = re.compile(r"<\|[^|>]*\|>")
ECHO = ["available command", "observation:", "your task", "textworld", "exactly one of",
        "alfred", "you are an ai agent", "task description"]

def mechanism(ag):
    """Classify the raw action generation string (decoupled family)."""
    if ag is None:      return "inline"          # entangled: no separate action call
    if ag.strip() == "": return "empty"
    specials = SP.findall(ag)
    core = SP.sub("", ag).strip()
    if core == "" and specials: return "control_only"
    low = ag.lower()
    if specials:                 return "control_mixed"
    if any(m in low for m in ECHO): return "prompt_echo"
    return "clean"

def action_sp(audit):
    lp = (audit or {}).get("logprobs")
    return -sum(lp) if lp else None

def hist(vals, lo, hi, bins):
    if not vals: return []
    w = (hi - lo) / bins; h = [0]*bins
    for x in vals:
        i = int((min(max(x, lo), hi-1e-9)-lo)/w); h[min(i, bins-1)] += 1
    return [{"x0": round(lo+i*w, 2), "x1": round(lo+(i+1)*w, 2), "n": h[i]} for i in range(bins)]

out = {"runs": {}}
for name, (path, subtitle) in RUNS.items():
    try:
        recs = [json.loads(l) for l in open(path) if l.strip()]
    except FileNotFoundError:
        continue
    idx = {}                                     # (task_index, step) -> record
    for d in recs:
        idx[((d.get("extra") or {}).get("task_index"), d.get("step_idx"))] = d

    n = len(recs)
    mech = Counter()
    mech_outcome = defaultdict(lambda: Counter())   # mech -> {noop, effective, terminal}
    finish = Counter(); ftok = Counter(); retry_reason = Counter(); rdeg = Counter()
    special_freq = Counter()
    noop_by_step = defaultdict(lambda: [0, 0])      # step -> [noop, non_terminal_total]
    noop_by_task = defaultdict(lambda: [0, 0])
    ep_len = defaultdict(int)
    sp_eff, sp_noop = [], []
    noop_total = eff_total = term_total = 0
    samples = []                                    # mix of noop + effective for inspector

    for d in recs:
        ex = d.get("extra", {}) or {}
        ag = ex.get("action_generation")
        at = d.get("action_text") or ""
        ti = ex.get("task_index"); step = d.get("step_idx", -1)
        gr = (ex.get("generation_retry", {}) or {}).get("action", {}) or {}
        audit = ex.get("action_stage_audit", {}) or {}
        ep_len[ti] = max(ep_len[ti], step)

        m = mechanism(ag); mech[m] += 1
        for s in SP.findall(ag or ""): special_freq[s] += 1

        fr = gr.get("first_finish_reason")
        if fr is not None or ag is not None: finish[str(fr)] += 1
        ft = gr.get("first_completion_tokens")
        if isinstance(ft, int): ftok[min(ft, 12)] += 1
        rr = gr.get("retry_reason")
        if rr is not None:
            retry_reason[str(rr)] += 1
            rdeg["still_degenerate" if gr.get("retry_degenerate") else "recovered"] += 1

        # ground-truth outcome from THIS record's own observation (logged post-env.step;
        # loops.py:262,273 -> observation_text[t] is the result of action[t]).
        own = d.get("observation_text", "") or ""
        if "Nothing happens" in own:
            outcome = "noop"; noop_total += 1
        else:
            outcome = "effective"; eff_total += 1
        mech_outcome[m][outcome] += 1
        if outcome != "terminal":
            noop_by_step[step][1] += 1; noop_by_step[step][0] += int(outcome == "noop")
            noop_by_task[ti][1] += 1;   noop_by_task[ti][0] += int(outcome == "noop")

        sp = action_sp(audit)
        if sp is not None and outcome != "terminal":
            (sp_noop if outcome == "noop" else sp_eff).append(round(sp, 3))

        if len(samples) < 80 and outcome != "terminal":
            # keep a spread: prioritise noop with mechanism variety, plus some effective
            keep = (outcome == "noop") or (len([s for s in samples if s["outcome"] == "effective"]) < 18)
            if keep:
                samples.append({
                    "task": ti, "step": step, "mech": m, "outcome": outcome,
                    "seed": (d.get("sampling") or {}).get("seed"),
                    "ag": (ag if ag is not None else "—")[:140],
                    "action_text": at[:70],
                    "first_finish": fr, "first_tokens": ft,
                    "retry_reason": rr, "retry_degenerate": gr.get("retry_degenerate"),
                    "tokens": (audit.get("tokens") or [])[:14],
                    "action_sp": round(sp, 3) if sp is not None else None,
                })

    step_curve = [{"step": k, "noop": v[0], "total": v[1], "rate": round(v[0]/v[1], 4)}
                  for k, v in sorted(noop_by_step.items()) if k >= 0 and v[1] >= 5]
    task_detail = [{"task": k, "noop": v[0], "total": v[1], "rate": round(v[0]/v[1], 4),
                    "ep_len": ep_len[k]+1}
                   for k, v in sorted(noop_by_task.items()) if k is not None and v[1] > 0]

    nonterm = noop_total + eff_total
    out["runs"][name] = {
        "subtitle": subtitle, "n": n,
        "noop": noop_total, "effective": eff_total, "terminal": term_total,
        "noop_rate": round(noop_total/nonterm, 4) if nonterm else None,
        "mechanism": dict(mech),
        "mech_outcome": {k: dict(v) for k, v in mech_outcome.items()},
        "finish_reason": dict(finish),
        "ftok_hist": [{"tok": k, "n": ftok[k]} for k in sorted(ftok)],
        "retry_reason": dict(retry_reason),
        "retry_recovery": dict(rdeg),
        "special_freq": special_freq.most_common(14),
        "step_curve": step_curve,
        "task_detail": task_detail,
        "sp_eff_hist": hist(sp_eff, 0, 40, 20),
        "sp_noop_hist": hist(sp_noop, 0, 40, 20),
        "sp_eff_mean": round(sum(sp_eff)/len(sp_eff), 2) if sp_eff else None,
        "sp_noop_mean": round(sum(sp_noop)/len(sp_noop), 2) if sp_noop else None,
        "samples": samples,
    }

json.dump(out, sys.stdout)
