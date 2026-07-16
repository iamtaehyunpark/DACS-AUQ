"""Judge labeling pipeline — ReDAct Fig. 9 protocol: the judge sees the WHOLE trajectory in
one call and returns per-step JSON {"step i": {"label": 0|1, "reason": ...}}, i starting at 1.
label 1 = good/helpful, 0 = bad. Our record stores label.judge = "correct"/"incorrect";
the AUROC positive class downstream is `incorrect`.

Parse policy mirrors elicitation (E1★.6): an unparseable judge response is retried once at
temperature 0.2; if still unparseable, every step of that trajectory gets label None and the
trajectory counts toward a reported unparsed rate. Never guess labels.

Output is a NEW labeled file — no experiment mutates another's data files (spec, Sequencing).
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict

from src.agent.llm import VLLMClient
from src.agent.prompts import fill
from src.schema import write_jsonl

_STEP_KEY_RE = re.compile(r"step\s*(\d+)", re.IGNORECASE)


def format_trajectory(task: str, steps: list[dict], *, include_thought: bool = False) -> str:
    """Render one trajectory for the judge. Step numbering starts at 1 to match the judge's
    "step i" keys. Thought EXCLUDED by default (decision 2026-07-16, pre-data): entangled and
    decoupled thoughts differ systematically in style/length, so a thought-visible judge
    produces label distributions that differ by architecture — the 2x2's rows would be scored
    against different standards. Labels come from an architecture-invariant rendering
    (actions + observations only). This may diverge from ReDAct's unspecified {TRAJECTORY}
    format — one more reason the anchor is context, never a gate."""
    lines = [f"Task: {task}"]
    for i, s in enumerate(steps, 1):
        lines.append(f"step {i}:")
        if include_thought and s.get("thought_text"):
            lines.append(f"thought: {s['thought_text']}")
        lines.append(f"action: {s['action_text']}")
        lines.append(f"observation: {s['observation_text']}")
    return "\n".join(lines)


def parse_judge_json(text: str) -> dict[int, tuple[int, str]] | None:
    """Extract {step_idx(0-based): (label, reason)} from a judge response. None if no valid
    JSON object with at least one 'step i' key can be recovered."""
    if not text:
        return None
    t = re.sub(r"```(?:json)?", "", text).strip()
    lo, hi = t.find("{"), t.rfind("}")
    if lo < 0 or hi <= lo:
        return None
    try:
        obj = json.loads(t[lo:hi + 1])
    except json.JSONDecodeError:
        return None
    out: dict[int, tuple[int, str]] = {}
    for k, v in obj.items():
        m = _STEP_KEY_RE.search(str(k))
        if not m or not isinstance(v, dict) or v.get("label") not in (0, 1):
            continue
        out[int(m.group(1)) - 1] = (int(v["label"]), str(v.get("reason", "")))
    return out or None


def group_by_trajectory(records: list[dict]) -> "OrderedDict[tuple, list[dict]]":
    groups: OrderedDict[tuple, list[dict]] = OrderedDict()
    for r in records:
        groups.setdefault((r["run_id"], r["task_id"]), []).append(r)
    for g in groups.values():
        g.sort(key=lambda r: r["step_idx"])
    return groups


def judge_records(records: list[dict], client: VLLMClient, judge_prompt_template: str, *,
                  include_thought: bool = True, judge_name: str = "judge") -> dict:
    """Label all records in place (label.judge / label.judge_raw). Returns a stats dict."""
    stats = {"judge": judge_name, "model": client.model, "n_traj": 0, "n_steps": 0,
             "n_labeled": 0, "n_correct": 0, "n_incorrect": 0, "unparsed_trajs": []}
    for (run_id, task_id), steps in group_by_trajectory(records).items():
        stats["n_traj"] += 1
        stats["n_steps"] += len(steps)
        task = (steps[0].get("extra") or {}).get("task", "")
        prompt = fill(judge_prompt_template,
                      {"TRAJECTORY": format_trajectory(task, steps, include_thought=include_thought)})
        labels = None
        for temperature in (0.0, 0.2):  # one retry, slightly off-greedy (E1★.6 policy)
            resp = client.chat([{"role": "user", "content": prompt}], temperature=temperature)
            labels = parse_judge_json(resp)
            if labels:
                break
        if labels is None:
            stats["unparsed_trajs"].append(f"{run_id}|{task_id}")
            continue
        for s in steps:
            got = labels.get(s["step_idx"])
            if got is None:
                continue
            label, reason = got
            s["label"]["judge"] = "correct" if label == 1 else "incorrect"
            s["label"]["judge_raw"] = reason
            stats["n_labeled"] += 1
            stats["n_correct" if label == 1 else "n_incorrect"] += 1
    return stats


def judge_file(in_path: str, out_path: str, client: VLLMClient, judge_prompt_template: str, *,
               include_thought: bool = True, judge_name: str = "judge") -> dict:
    with open(in_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    stats = judge_records(records, client, judge_prompt_template,
                          include_thought=include_thought, judge_name=judge_name)
    write_jsonl(out_path, records)
    return stats
