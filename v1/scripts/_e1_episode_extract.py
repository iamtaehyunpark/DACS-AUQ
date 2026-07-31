#!/usr/bin/env python3
"""Extract two decoupled episodes into a per-step structure for a raw step viewer.
Read-only. Shows EVERY stage verbatim: prior state -> thought -> raw action gen
(+ token/logprob audit + retry) -> parsed/executed action -> env response."""
import json, re, sys

PATH = "data/trajectories/e1_primary_decoupled copy.jsonl"
rows = [json.loads(l) for l in open(PATH) if l.strip()]

def initial_obs(prompt):
    # step-0 prompt embeds: "ENVIRONMENT HISTORY:\nObservation: <initial>\n..." up to next section
    m = re.search(r"ENVIRONMENT HISTORY:\n(.*?)(?:\nAVAILABLE COMMANDS|\nOUTPUT RULES|$)", prompt or "", re.DOTALL)
    return (m.group(1).strip() if m else "")[:1400]

# group by (task_index) preserving order
eps = {}
for r in rows:
    ti = (r.get("extra") or {}).get("task_index")
    eps.setdefault(ti, []).append(r)

out = {"episodes": []}
for ti, recs in eps.items():
    recs.sort(key=lambda d: d.get("step_idx", 0))
    ex0 = recs[0].get("extra") or {}
    steps = []
    prev_obs = initial_obs(ex0.get("thought_prompt") or ex0.get("action_prompt"))
    ep_init = prev_obs
    for r in recs:
        ex = r.get("extra") or {}
        pr = r.get("probes") or {}
        audit = ex.get("action_stage_audit") or {}
        toks = audit.get("tokens") or []
        lps = audit.get("logprobs") or []
        gr = (ex.get("generation_retry") or {}).get("action") or {}
        obs = r.get("observation_text") or ""
        noop = "Nothing happens" in obs
        span = audit.get("span_tok")
        steps.append({
            "step": r.get("step_idx"),
            "seed": (r.get("sampling") or {}).get("seed"),
            "prior_obs": prev_obs,
            "thought_gen": ex.get("thought_generation") or "",
            "thought_sp": pr.get("thought_sp"), "thought_ppl": pr.get("thought_ppl"),
            "thought_mte": pr.get("thought_mte"),
            "u_t_verbal": pr.get("U_T_verbalized_raw"), "u_t_verbal_val": pr.get("U_T_verbalized"),
            "u_t_posthoc": pr.get("U_T_posthoc_numeric"),
            "action_gen": ex.get("action_generation") if ex.get("action_generation") is not None else "",
            "action_text": r.get("action_text") or "",
            "verb": (r.get("action_parsed") or {}).get("verb"),
            "arg": (r.get("action_parsed") or {}).get("arg"),
            "action_match": ex.get("action_match"),
            "audit_span": span,
            "audit": [{"t": t, "lp": (round(lps[i], 2) if i < len(lps) else None)} for i, t in enumerate(toks)],
            "first_finish": gr.get("first_finish_reason"),
            "first_tokens": gr.get("first_completion_tokens"),
            "retry_reason": gr.get("retry_reason"),
            "retry_seed": gr.get("retry_seed"),
            "retry_degenerate": gr.get("retry_degenerate"),
            "action_sp": pr.get("action_sp"), "action_ppl": pr.get("action_ppl"),
            "u_a_verbal": pr.get("U_A_verbalized_raw"),
            "posthoc_raw": ex.get("posthoc_raw"),
            "repair_raw": ex.get("verbalized_repair_raw"),
            "obs": obs,
            "noop": noop,
            "admissible": ex.get("admissible_commands") or [],
        })
        prev_obs = obs
    out["episodes"].append({
        "task_index": ti,
        "task": ex0.get("task"),
        "task_id": recs[0].get("task_id"),
        "gamefile": ex0.get("gamefile"),
        "initial_obs": ep_init,
        "n_steps": len(steps),
        "n_noop": sum(1 for s in steps if s["noop"]),
        "steps": steps,
    })

# episodes ordered by task_index for stable display
out["episodes"].sort(key=lambda e: e["task_index"])
json.dump(out, sys.stdout)
