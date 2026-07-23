"""Environment-side loop-step diagnostic (pre-registered 2026-07-20, pre E0-full data).

A LOOP STEP is a step whose executed (action_text, observation_text) pair already
occurred at an earlier step of the same episode — a repeated environment transition.
The definition is deliberately ENVIRONMENT-DERIVED: it depends on no probe under
evaluation (not thought text, not confidence, not entropy), so loop/fresh
stratification and covariates stay independent of every probe being scored; and it
survives the per-step seed policy, under which repeated thoughts drift in wording
while the repeated env transition remains exact.

Uses (all pre-registered):
1. per-episode loop-collapse fraction, reported as a covariate;
2. loop/fresh stratification of the E0 annotation sample (src/e0/sample_steps.py);
3. the sensitivity analysis collapsing loop steps to one representative per
   repeated state (the first occurrence, which by definition is not a loop step).
"""
from __future__ import annotations

from collections import defaultdict


def _episode_key(rec: dict) -> tuple:
    return (rec.get("run_id"), rec.get("task_id"))


def _state_key(rec: dict):
    """Repeated-transition identity. A step with no executed action string can never
    be a loop repeat (nor seed one) — it carries no environment transition."""
    a = rec.get("action_text")
    if not isinstance(a, str) or not a.strip():
        return None
    return (a, rec.get("observation_text"))


def loop_step_uids(records: list[dict]) -> set[tuple]:
    """(run_id, task_id, step_idx) of every loop step, per the definition above."""
    by_ep: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        by_ep[_episode_key(r)].append(r)
    out: set[tuple] = set()
    for ep in by_ep.values():
        seen: set = set()
        for r in sorted(ep, key=lambda r: r["step_idx"]):
            k = _state_key(r)
            if k is None:
                continue
            if k in seen:
                out.add((r.get("run_id"), r.get("task_id"), r["step_idx"]))
            else:
                seen.add(k)
    return out


def loop_fraction_by_episode(records: list[dict]) -> dict[tuple, dict]:
    """{(run_id, task_id): {n_steps, n_loop, fraction}} — the reported covariate."""
    loops = loop_step_uids(records)
    by_ep: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        by_ep[_episode_key(r)].append(r)
    return {
        ep: {"n_steps": len(rs),
             "n_loop": sum(1 for r in rs
                           if (r.get("run_id"), r.get("task_id"), r["step_idx"]) in loops),
             "fraction": sum(1 for r in rs
                             if (r.get("run_id"), r.get("task_id"), r["step_idx"]) in loops)
                         / len(rs)}
        for ep, rs in by_ep.items()
    }


def collapse_loop_steps(records: list[dict]) -> list[dict]:
    """Sensitivity-analysis view: drop every loop step, keeping the first occurrence
    of each repeated state. Input order preserved."""
    loops = loop_step_uids(records)
    return [r for r in records
            if (r.get("run_id"), r.get("task_id"), r["step_idx"]) not in loops]
