"""Phase-2 runner — SEPARATE confidence probes over a frozen Phase-1 UQ log.

Reads a Phase-1 UQ log (the JSONL written by chat_react.py / chat_react_entangled.py under
REACT_UQLOG: interleaved `call` / `step` / `episode` records), reconstructs each agent step's
(task, history, commands, thought, action) from the logged text, runs the Phase-2 probes
(probes.py) as SEPARATE model calls via uqlog.instrumented_chat, and writes a probe-log JSONL.
It NEVER re-runs the agent and NEVER touches the input log.

Reconstruction:
  * decoupled step  -> one `call` with call_kind='thought' (its completion_raw = thought; its
                       prompt_templated carries TASK/HISTORY) + one call_kind='action'
                       (its completion_raw's first content line = action).
  * entangled step  -> one `call` with call_kind='joint' (completion_raw split on ACTION:).
  * commands come from the matching `step` record's `admissible`; if the action call/parse is
    empty, action-stage probes are skipped for that step.

Config (env):
  PROBE_INPUT   (required)  path to the Phase-1 UQ log to read.
  PROBE_OUTPUT  (required)  path to write the probe-log JSONL (choose a name that will NOT
                            collide with any concurrent run's uq_*.jsonl).
  PROBE_MODEL          (qwen)                     served model name
  PROBE_BASE_URL       (http://localhost:8000/v1)
  PROBE_TOKENIZER      (Qwen/Qwen3.6-35B-A3B)
  PROBE_KINDS          (ptrue,sep_verbalized,posthoc_numeric,targeted)
  PROBE_STAGES         (thought,action)  also supports 'response' = the WHOLE step (reasoning +
                       action as one unit), the no-discrimination reading (U_R_*); 'targeted' has
                       no response form (thought-only q_t). To add just the whole-response pass to
                       an existing corpus: PROBE_KINDS=ptrue,sep_verbalized,posthoc_numeric
                       PROBE_STAGES=response, output to a separate *_response.jsonl.
  PROBE_QT_MODE        (llm | heuristic)          q_t extraction for the targeted probe
  PROBE_MAX_STEPS      (unset -> all)             cap total steps probed (keep tests SMALL)
  PROBE_TEMPERATURE (0.7) PROBE_TOP_P (0.80) PROBE_TOP_K (20) PROBE_MIN_P (0.0)
  PROBE_PRESENCE_PENALTY (1.5) PROBE_REPETITION_PENALTY (1.0) PROBE_SEED_BASE (7000)

Run (server): ALFWORLD_DATA / HF_HOME / HF_HUB_OFFLINE=1 set,
  PROBE_INPUT=$PWD/probe_fixture.jsonl PROBE_OUTPUT=$PWD/probe_out.jsonl \
  /opt/anaconda3/envs/Jagent/bin/python run_probes.py
"""
import json
import os
import sys

from openai import OpenAI

import probes


def _load(path):
    recs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def group_steps(records):
    """Group `call` + `step` records by (run_id, task_id, step_idx) and reconstruct the context
    bundle each probe needs. Yields dicts with run_id/task_id/step_idx/source_call_kind and a
    `ctx` = {task, history, commands, thought, action}. Steps whose thought text can't be
    recovered are skipped (logged to stderr)."""
    groups = {}
    for r in records:
        if r.get("kind") not in ("call", "step"):
            continue
        key = (r.get("run_id"), r.get("task_id"), r.get("step_idx"))
        groups.setdefault(key, {"calls": [], "step": None})
        if r["kind"] == "call":
            groups[key]["calls"].append(r)
        else:
            groups[key]["step"] = r

    for (run_id, task_id, step_idx), g in sorted(
            groups.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), kv[0][2] or 0)):
        calls = {c.get("call_kind"): c for c in g["calls"]}
        step = g["step"]
        admissible = (step or {}).get("admissible") or []
        commands = "\n".join(admissible)

        if "joint" in calls:                                  # entangled
            jc = calls["joint"]
            task, history = probes.parse_task_history(jc.get("prompt_templated", ""))
            # A11: prefer the harness-logged clean thought (pre-ACTION); fall back for pre-v4 logs
            thought = (step or {}).get("thought_text") or probes.split_entangled(jc.get("completion_raw", ""))[0]
            action = (step or {}).get("action_parsed") or ""
            source_call_kind = "joint"
        elif "thought" in calls:                              # decoupled
            tc = calls["thought"]
            task, history = probes.parse_task_history(tc.get("prompt_templated", ""))
            # A11 / A8: condition on the CLEAN, trimmed, tag-free thought — the pre-action
            # epistemic state — NOT the raw completion (which contained the committed action
            # in the pilot). source_call_kind reflects that the action is no longer in scope.
            thought = (step or {}).get("thought_clean")
            if thought is None:                               # fallback for pre-v4 corpora
                thought = (tc.get("completion_raw") or "").strip()
                thought = thought.split("</think>", 1)[-1].strip() if "</think>" in thought else thought
            action = (step or {}).get("action_parsed") or ""
            source_call_kind = "thought"
        else:
            sys.stderr.write("skip %s/%s step %s: no thought/joint call\n" % (run_id, task_id, step_idx))
            continue

        if not thought:
            sys.stderr.write("skip %s/%s step %s: empty thought\n" % (run_id, task_id, step_idx))
            continue

        yield {
            "run_id": run_id, "task_id": task_id, "step_idx": step_idx,
            "source_call_kind": source_call_kind,
            "ctx": {"task": task, "history": history, "commands": commands,
                    "thought": thought, "action": action},
        }


def main():
    inp = os.environ.get("PROBE_INPUT")
    out = os.environ.get("PROBE_OUTPUT")
    if not inp or not out:
        sys.exit("PROBE_INPUT and PROBE_OUTPUT are required")
    if os.path.abspath(inp) == os.path.abspath(out):
        sys.exit("PROBE_OUTPUT must differ from PROBE_INPUT")

    kinds = [k.strip() for k in os.environ.get(
        "PROBE_KINDS", "ptrue,sep_verbalized,posthoc_numeric,targeted").split(",") if k.strip()]
    stages = [s.strip() for s in os.environ.get("PROBE_STAGES", "thought,action").split(",") if s.strip()]
    max_steps = os.environ.get("PROBE_MAX_STEPS")
    max_steps = int(max_steps) if max_steps else None

    cfg = probes.ProbeConfig(
        model=os.environ.get("PROBE_MODEL", "qwen"),
        tokenizer_path=os.environ.get("PROBE_TOKENIZER", "Qwen/Qwen3.6-35B-A3B"),
        base_url=os.environ.get("PROBE_BASE_URL", "http://localhost:8000/v1"),
        temperature=float(os.environ.get("PROBE_TEMPERATURE", "0.7")),
        top_p=float(os.environ.get("PROBE_TOP_P", "0.80")),
        top_k=int(os.environ.get("PROBE_TOP_K", "20")),
        min_p=float(os.environ.get("PROBE_MIN_P", "0.0")),
        presence_penalty=float(os.environ.get("PROBE_PRESENCE_PENALTY", "1.5")),
        repetition_penalty=float(os.environ.get("PROBE_REPETITION_PENALTY", "1.0")),
        seed_base=int(os.environ.get("PROBE_SEED_BASE", "7000")),
        qt_mode=os.environ.get("PROBE_QT_MODE", "llm"),
    )
    client = OpenAI(api_key="EMPTY", base_url=cfg.base_url)

    # Optional stride sharding for parallel runs (disjoint step subsets, union = all steps):
    # PROBE_NUM_WORKERS workers, this one is PROBE_WORKER_ID; each takes every NW-th grouped step.
    nw = int(os.environ.get("PROBE_NUM_WORKERS", "1"))
    wid = int(os.environ.get("PROBE_WORKER_ID", "0"))

    records = _load(inp)
    n_steps = n_probes = 0
    parse_ok = parse_tot = 0
    with open(out, "a") as fo:
        for gi, step in enumerate(group_steps(records)):
            if gi % nw != wid:                 # not this worker's shard
                continue
            if max_steps is not None and n_steps >= max_steps:
                break
            n_steps += 1
            try:
                probe_recs = probes.run_step_probes(client, cfg, step, kinds=kinds, stages=stages)
            except Exception as e:                     # never let one step kill a sweep
                sys.stderr.write("ERROR step %s/%s/%s: %r\n" % (
                    step["run_id"], step["task_id"], step["step_idx"], e))
                continue
            # A11 roster relabel: posthoc_numeric (0-100) is THE post-hoc numeric roster row;
            # sep_verbalized (0-1) is its wording variant for the E1b robustness arm (~46%
            # identical to posthoc_numeric full-corpus). Recorded, not dropped.
            _ROLE = {"posthoc_numeric": "roster", "sep_verbalized": "e1b_wording_variant"}
            for pr in probe_recs:
                pr["roster_role"] = _ROLE.get(pr.get("probe_kind"), "roster")
                fo.write(json.dumps(pr) + "\n")
                n_probes += 1
                if pr["probe_kind"] != "qt_extract":
                    parse_tot += 1
                    parse_ok += 1 if pr.get("parse_ok") else 0
            fo.flush()
            print("[step %s/%s #%s] %d probe calls (running parse_ok %d/%d)" % (
                step["task_id"], step["step_idx"], n_steps, len(probe_recs), parse_ok, parse_tot))
            sys.stdout.flush()

    print("\nDONE: %d steps, %d probe records -> %s | parse_ok %d/%d" % (
        n_steps, n_probes, out, parse_ok, parse_tot))


if __name__ == "__main__":
    main()
