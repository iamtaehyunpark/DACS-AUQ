"""P(True) context-ablation × rule-injection probe — a small MECHANISM diagnostic, not a benchmark.

Question: does what the P(True) probe is allowed to SEE (context ablation), and whether the probe
is TOLD a decision rule (rule injection), change the P(True) it reports — and does it change it
*differentially* for judge-incorrect vs judge-correct steps? The readout is the separation

    Delta = mean U(incorrect steps) - mean U(correct steps)      (U = P(No) over {Yes,No} mass)

per condition, plus PAIRED per-step shifts between conditions. No AUROC: at n~20 the paired
per-step movement is the informative quantity, and it needs no bootstrap.

Design — 9 conditions, NOT a 5x4 cross. The two factors are tested separately, each against the
production P(True) prompt, and every step is run in all 9 -> fully paired:

  A. context ladder, no rule ........ C0/R0 C1/R0 C2/R0 C3/R0 C4/R0 C5/R0 C6/R0
  B. rule on the ORIGINAL prompt .... C3/R1  C3/R2  C3/R3      (C3/R0 is the baseline for these)
  control .......................... C0/R2  (repeat-rule with NO history in the prompt)

  CONTEXT (what the probe sees)
    C0  task + action                                   (no history, no reasoning)
    C1  task + last observation + action
    C2  task + full history + action
    C3  task + full history + reasoning + action        <- current production prompt
    C4  task + full history + reasoning                 (no action; thought-stage question)
    C5  C3 + the observation the action actually produced          PRE-HINDSIGHT
    C6  C5 + the agent's own next reasoning and action             PRE-HINDSIGHT (full)

  PRE-HINDSIGHT (C5/C6) costs nothing extra to collect: the step was really taken, so step t+1's
  logged history IS step t's history plus action_t and its resulting observation. "Take one more
  step, then judge the previous one" is a slice of the frozen trajectory, not a re-run.
  C5 gives the ENVIRONMENT's verdict on the action; C6 adds the AGENT's continuation. They are
  split because attribution differs: if U moves under C6 but not C5, the probe is reading the
  agent's own floundering rather than the world's response.
  Deployability: this is a real probe only where actions are reversible (act -> observe ->
  assess -> undo). Where they are not, read C5/C6 as a CEILING — what P(True) could know if the
  outcome were available — not as a candidate probe. Note also that the observed continuation of
  a bad step is itself contaminated by that step; for hindsight that is the point.

  RULE (inserted as EVALUATION GUIDANCE: immediately before the Yes/No question)
    R0  none                                            (plain)
    R1  generic rubric (repeat / absent object / inadmissible)
    R2  targeted single rule: repeats-something-already-tried -> probably wrong
    R3  DECOY rule — plausible, falsifiable, irrelevant  (the control that makes R1/R2 readable)

What makes a rule effect readable:
  * C0/R2 vs C0/R0 — the same repeat-rule where the prompt contains NO history, so there is
    nothing to detect a repeat in. Movement here is compliance with the stated rule, not
    detection. This is the control that C3/R2 has to beat.
  * R2 should move loop-type errors more than non-loop errors. A uniform shift = global pessimism.
  * R2 should NOT move the legitimate-revisit CORRECT steps. If it does, the rule buys separation
    by manufacturing false positives.
  * R3 (decoy) quantifies the pure "a rule was stated" effect that R1/R2 must beat.

Everything reads a FROZEN Phase-1 uq_*.jsonl + its judge_*.jsonl. The agent is never re-run, no
probe value is fed back anywhere. P(True) is one token per call: 20 steps x 9 conditions = 180
single-token calls (~a minute on one GPU).

Held fixed across conditions: temperature 0, top_p 1.0, top_k 20, presence/repetition penalty off,
first-non-whitespace-token top-20 Yes/No mass, parse_ok recorded and NEVER imputed. The Yes/No
question wording is byte-identical everywhere except C4, which necessarily asks the thought-stage
question (there is no action in that context) — that is the one intentional wording change.
AVAILABLE COMMANDS is held PRESENT in every context (including C0), so the ladder varies history
and reasoning only and does not smuggle admissibility information in with the observations;
--no-commands drops it everywhere if you want the stricter ablation.

Usage
  # 1. pick the steps (GPU-free) -> selection JSON, then EDIT IT BY HAND if you want
  python ptrue_context_rule_probe.py select \
      --uq result/e1/e1b/uq_entangled_e1.jsonl --judge result/e1/e1b/judge_entangled_e1.jsonl \
      --out sel.json --n-incorrect 10 --n-correct 10

  # 2. sweep (needs a live vLLM serving the SAME model that generated the corpus)
  python ptrue_context_rule_probe.py run --selection sel.json --out ptrue_ctxrule.jsonl \
      --model qwen --tokenizer Qwen/Qwen3.6-35B-A3B --base-url http://localhost:8000/v1

  # 3. report (GPU-free) -> matrix CSV + markdown
  python ptrue_context_rule_probe.py report --records ptrue_ctxrule.jsonl \
      --csv ptrue_ctxrule_matrix.csv --out ptrue_ctxrule.md
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import math
import random
import re
import statistics
import sys

SCHEMA_VERSION = "ctxrule_1.0.0"

# --------------------------------------------------------------------------- conditions

CONTEXTS = ["C0", "C1", "C2", "C3", "C4", "C5", "C6"]
CONTEXT_DESC = {
    "C0": "task + action",
    "C1": "task + last observation + action",
    "C2": "task + full history + action",
    "C3": "task + full history + reasoning + action (production)",
    "C4": "task + full history + reasoning, no action",
    "C5": "production + the OUTCOME of the action (pre-hindsight)",
    "C6": "production + outcome + the agent's next step (pre-hindsight, full)",
}
# Which contexts contain the history a repeat/loop could be detected in. R2's effect OUTSIDE
# this set is, by construction, not evidence-driven.
CONTEXT_HAS_HISTORY = {"C0": False, "C1": False, "C2": True, "C3": True, "C4": True,
                       "C5": True, "C6": True}
# Contexts that need the NEXT step of the trajectory (skipped for a step with no successor).
CONTEXT_NEEDS_FUTURE = {"C5", "C6"}

RULES = ["R0", "R1", "R2", "R3"]
RULE_TEXT = {
    "R0": "",
    "R1": ("EVALUATION GUIDANCE:\n"
           "A step is wrong if it repeats an action that was already tried without progress, "
           "if it targets an object that is not present in this location, or if it is not one "
           "of the available commands in the current state.\n"),
    "R2": ("EVALUATION GUIDANCE:\n"
           "If the action repeats something the agent has already tried in the history, it is "
           "probably wrong.\n"),
    # DECOY: same shape, same confidence, plausible-sounding, falsifiable — and irrelevant to
    # whether the step is right. Deliberately NOT absurd: an absurd rule gets ignored and would
    # under-control the "a rule was stated" effect.
    "R3": ("EVALUATION GUIDANCE:\n"
           "If the action targets an object that is mentioned late in the task description "
           "rather than early, it is probably wrong.\n"),
}
RULE_DESC = {"R0": "none", "R1": "generic rubric", "R2": "targeted (repeat)", "R3": "decoy (irrelevant)"}

PRODUCTION_CONDITION = ("C3", "R0")          # the current probe = reference for paired shifts

# Default grid: the two factors are tested SEPARATELY, each against the production prompt, not
# as a 5x4 cross. Factor A moves context with no rule; factor B adds a rule to the ORIGINAL
# P(True) prompt (C3), so a rule effect is read against the probe actually in use.
#   + one control cell, C0/R2: the same repeat-rule in a context with NO history in it. If R2
#     moves U there, the model is complying with the rule rather than detecting a repeat — that
#     cell is what makes the C3/R2 result interpretable, so it is in the default grid.
DEFAULT_CONDITIONS = ([(c, "R0") for c in CONTEXTS]
                      + [("C3", r) for r in RULES if r != "R0"]
                      + [("C0", "R2")])                          # 11 cells
CONDITIONS = DEFAULT_CONDITIONS                                  # 9 cells, not a 5x4 cross

_PREAMBLE = "You are evaluating an AI agent that is solving a task in an interactive environment.\n"
_Q_ACTION = ("Is the proposed action above the correct and appropriate next action for this "
             "task?\nAnswer with a single word: Yes or No.")
_Q_THOUGHT = ("Is the proposed reasoning above correct and appropriate for deciding the next "
              "action in this task?\nAnswer with a single word: Yes or No.")

# --------------------------------------------------------------------------- history slicing

# chat_react*.py build history as: <initial observation>  then repeated  "\n> {action}\n{obs}".
# In REACT_HISTORY_MODE=full the action lines are "> THOUGHT: ..." / "> ACTION: ..." /
# "> CONFIDENCE: ..." instead; we treat any "> " line as a turn boundary and pull the ACTION:
# payload when it is labeled.
_TURN_RE = re.compile(r"^>\s?(.*)$", re.MULTILINE)


def last_observation(history: str) -> str:
    """The text after the final '> ...' turn line = the most recent observation. If the history
    has no turn line at all (step 1), the whole history IS the initial observation."""
    hits = list(_TURN_RE.finditer(history or ""))
    if not hits:
        return (history or "").strip()
    tail = (history or "")[hits[-1].end():].strip()
    return tail


def prior_actions(history: str) -> list[str]:
    """Every action the agent already issued, in order. Used only for stratification (spotting
    repeats/revisits) — never fed to the model."""
    out = []
    for m in _TURN_RE.finditer(history or ""):
        line = m.group(1).strip()
        if re.match(r"(?i)^(thought|confidence):", line):
            continue
        line = re.sub(r"(?i)^action:\s*", "", line).strip()
        if line:
            out.append(line)
    return out


# --------------------------------------------------------------------------- prompt assembly

def build_prompt(ctx: dict, context_id: str, rule_id: str, *, with_commands: bool = True) -> str:
    """Assemble the probe prompt for one (context, rule) cell. Blocks are emitted in the same
    order and with the same literal labels as the production probe, so C3/R0 is byte-identical
    to probes.prompt_ptrue_action() (asserted by --selftest)."""
    parts = [_PREAMBLE, "TASK DESCRIPTION:\n%s\n" % ctx["task"]]

    if context_id == "C1":
        parts.append("LAST OBSERVATION:\n%s\n" % last_observation(ctx["history"]))
    elif context_id in ("C2", "C3", "C4"):
        parts.append("ENVIRONMENT HISTORY:\n%s\n" % ctx["history"])
    # C0: no environment block at all.

    if with_commands:
        parts.append("AVAILABLE COMMANDS:\n%s\n" % ctx["commands"])

    if context_id in ("C3", "C4", "C5", "C6"):
        label = "PROPOSED REASONING" if context_id == "C4" else "AGENT REASONING"
        parts.append("%s:\n%s\n" % (label, ctx["thought"]))
    if context_id != "C4":
        parts.append("PROPOSED ACTION:\n%s\n" % ctx["action"])

    # Pre-hindsight: the step was actually taken, so the environment's response to it is already
    # in the frozen trajectory. The blocks are labeled distinctly from PROPOSED ACTION so the
    # question below still refers unambiguously to the step under evaluation — which lets the
    # question wording stay BYTE-IDENTICAL across C0-C6 (no wording confound on top of context).
    if context_id in ("C5", "C6"):
        parts.append("RESULT OF THE PROPOSED ACTION:\n%s\n" % ctx.get("future_obs", ""))
    if context_id == "C6":
        parts.append("WHAT THE AGENT DID AFTER THAT:\nREASONING:\n%s\nACTION:\n%s\n"
                     % (ctx.get("future_thought", ""), ctx.get("future_action", "")))

    parts.append("\n")
    if RULE_TEXT[rule_id]:
        parts.append(RULE_TEXT[rule_id])
    parts.append(_Q_THOUGHT if context_id == "C4" else _Q_ACTION)
    return "".join(parts)


def _selftest():
    """C3/R0 must reproduce the production action-stage prompt exactly — otherwise this sweep is
    measuring a fourth, accidental prompt change on top of the two intended factors."""
    import probes
    ctx = {"task": "put a mug in the microwave.", "history": "You are in a room.\n> go to desk 1\nOn desk 1 you see a mug 1.",
           "commands": "go to desk 1\ntake mug 1 from desk 1", "thought": "I should take the mug.",
           "action": "take mug 1 from desk 1"}
    mine = build_prompt(ctx, "C3", "R0")
    theirs = probes.prompt_ptrue_action(ctx["task"], ctx["history"], ctx["commands"],
                                        ctx["thought"], ctx["action"])
    if mine != theirs:
        sys.stderr.write("C3/R0 DIVERGES from probes.prompt_ptrue_action:\n--- mine ---\n%r\n--- prod ---\n%r\n"
                         % (mine, theirs))
        return 1
    print("selftest OK: C3/R0 == probes.prompt_ptrue_action")
    print("last_observation:", repr(last_observation(ctx["history"])))
    print("prior_actions:", prior_actions(ctx["history"]))
    return 0


# --------------------------------------------------------------------------- selection

# Keyword tagging of the 3-judge free-text reasons. Coarse ON PURPOSE: it only proposes strata,
# and the selection JSON is meant to be reviewed (and edited) by hand before the sweep.
_LOOP_KW = re.compile(r"(?i)\b(repeat|repeated|repetit|loop|again|already (tried|visited|did|been)|redundan)")
_ADMIS_KW = re.compile(r"(?i)\b(not present|no such|invalid|inadmissib|not available|cannot|isn't there|not in the list)")


def _judge_label(rec):
    """(label, n_incorrect, n_valid) with label 1=incorrect, 0=correct, None=non-unanimous."""
    votes = rec.get("votes") or {}
    vals = [v.get("incorrect") for v in votes.values() if isinstance(v.get("incorrect"), int)]
    if not vals:
        return None, 0, 0
    n_inc, n = sum(vals), len(vals)
    if n_inc == n:
        return 1, n_inc, n
    if n_inc == 0:
        return 0, n_inc, n
    return None, n_inc, n


def _error_type(rec):
    reasons = " ".join((v.get("reason") or "") for v in (rec.get("votes") or {}).values())
    if _LOOP_KW.search(reasons):
        return "loop"
    if _ADMIS_KW.search(reasons):
        return "inadmissible"
    return "other"


def cmd_select(a):
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
    import run_probes                                            # pulls probes + openai

    judge = {}
    with open(a.judge) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") == "judge":
                judge[(r.get("run_id"), r.get("task_id"), r.get("step_idx"))] = r

    with open(a.uq) as f:
        records = [json.loads(l) for l in f if l.strip()]

    # The pre-hindsight rungs (C5/C6) need step t+1. Nothing has to be re-run for that: step
    # t+1's logged history is step t's history plus action_t and the observation it produced,
    # so the "one step ahead" is a slice of the frozen trajectory. Index every step first, then
    # attach each step's successor below.
    by_key = {}
    grouped = list(run_probes.group_steps(records))
    for step in grouped:
        by_key[(step["run_id"], step["task_id"], step["step_idx"])] = step

    pool = []
    n_no_future = 0
    for step in grouped:
        key = (step["run_id"], step["task_id"], step["step_idx"])
        jr = judge.get(key)
        if jr is None:
            continue
        label, n_inc, n_valid = _judge_label(jr)
        if label is None:                                        # dissent -> not a clean pole
            continue
        ctx = step["ctx"]
        if not ctx.get("action") or not ctx.get("thought"):
            continue

        nxt = by_key.get((key[0], key[1], (key[2] or 0) + 1))
        if nxt is None:                                          # terminal step: no hindsight
            n_no_future += 1
            if a.require_future:
                continue
        else:
            # everything after the last '> ...' turn line of the NEXT step's history is exactly
            # the observation this step's action produced
            ctx = dict(ctx)
            ctx["future_obs"] = last_observation(nxt["ctx"]["history"])
            ctx["future_thought"] = nxt["ctx"]["thought"]
            ctx["future_action"] = nxt["ctx"]["action"]
        if a.require_history and not ctx.get("history"):         # C1/C2/C3/C4 would be empty
            continue
        prev = prior_actions(ctx["history"])
        repeats = ctx["action"] in prev
        pool.append({
            "run_id": step["run_id"], "task_id": step["task_id"], "step_idx": step["step_idx"],
            "source_call_kind": step["source_call_kind"],
            "label": label, "n_incorrect_votes": n_inc, "n_valid_votes": n_valid,
            "stratum": (_error_type(jr) if label == 1 else ("revisit" if repeats else "plain")),
            "action_repeats_prior": repeats,
            "n_prior_actions": len(prev),
            "has_future": nxt is not None,
            "judge_votes": {k: v.get("incorrect") for k, v in (jr.get("votes") or {}).items()},
            "judge_reasons": {k: (v.get("reason") or "")[:200] for k, v in (jr.get("votes") or {}).items()},
            "ctx": ctx,
        })

    rng = random.Random(a.seed)
    per_task = {}

    def _take(cands, k):
        """Sample k, at most --max-per-task steps from any one trajectory (so a couple of long
        episodes cannot dominate a 20-step sample)."""
        rng.shuffle(cands)
        out = []
        for c in cands:
            if len(out) >= k:
                break
            if per_task.get(c["task_id"], 0) >= a.max_per_task:
                continue
            per_task[c["task_id"]] = per_task.get(c["task_id"], 0) + 1
            out.append(c)
        return out

    # incorrect: quota per error type (loop first — it is what R2 is aimed at), backfilled
    inc = [p for p in pool if p["label"] == 1]
    quota = {"loop": a.n_loop, "inadmissible": a.n_inadmissible}
    quota["other"] = max(0, a.n_incorrect - quota["loop"] - quota["inadmissible"])
    picked_inc = []
    for st in ("loop", "inadmissible", "other"):
        picked_inc += _take([p for p in inc if p["stratum"] == st], quota[st])
    if len(picked_inc) < a.n_incorrect:                          # backfill from whatever is left
        chosen = {(p["task_id"], p["step_idx"]) for p in picked_inc}
        picked_inc += _take([p for p in inc if (p["task_id"], p["step_idx"]) not in chosen],
                            a.n_incorrect - len(picked_inc))

    # correct: reserve slots for legitimate revisits (the false-positive test for R1/R2)
    cor = [p for p in pool if p["label"] == 0]
    picked_cor = _take([p for p in cor if p["stratum"] == "revisit"], a.n_revisit)
    n_plain = a.n_correct - len(picked_cor)

    if a.match_step_idx:
        # Judge-incorrect steps cluster LATE (long history, agent already floundering) and correct
        # steps early, so an unmatched sample lets the context ladder measure history LENGTH
        # instead of history CONTENT. Choose the `plain` correct steps to match the incorrect
        # step_idx distribution: for each incorrect step, take the nearest-in-step_idx unused
        # candidate. Greedy nearest-neighbour, no replacement, still respecting --max-per-task.
        cands = [p for p in cor if p["stratum"] == "plain"]
        rng.shuffle(cands)
        used = set()
        targets = sorted([p["step_idx"] or 0 for p in picked_inc])
        matched = []
        for t in targets:
            if len(matched) >= n_plain:
                break
            best, best_d = None, None
            for i, c in enumerate(cands):
                if i in used or per_task.get(c["task_id"], 0) >= a.max_per_task:
                    continue
                d = abs((c["step_idx"] or 0) - t)
                if best_d is None or d < best_d:
                    best, best_d, best_i = c, d, i
            if best is None:
                break
            used.add(best_i)
            per_task[best["task_id"]] = per_task.get(best["task_id"], 0) + 1
            matched.append(best)
        picked_cor += matched
        if len(picked_cor) < a.n_correct:       # backfill if matching ran out of candidates
            picked_cor += _take([c for i, c in enumerate(cands) if i not in used],
                                a.n_correct - len(picked_cor))
    else:
        picked_cor += _take([p for p in cor if p["stratum"] == "plain"], n_plain)

    sel = {"schema": SCHEMA_VERSION, "uq": a.uq, "judge": a.judge, "seed": a.seed,
           "pool_sizes": {"labeled_unanimous": len(pool), "incorrect": len(inc), "correct": len(cor)},
           "steps": picked_inc + picked_cor}
    with open(a.out, "w") as f:
        json.dump(sel, f, indent=1)

    counts = {}
    for s in sel["steps"]:
        counts[(s["label"], s["stratum"])] = counts.get((s["label"], s["stratum"]), 0) + 1
    print("pool: %d unanimous-labeled steps (%d incorrect / %d correct)"
          % (len(pool), len(inc), len(cor)))
    print("selected %d steps -> %s" % (len(sel["steps"]), a.out))
    for (lab, st), n in sorted(counts.items()):
        print("   label=%d %-13s %d" % (lab, st, n))
    # Step-position imbalance is the confound this sample is most exposed to: judge-incorrect
    # steps cluster LATE (long history, agent already floundering), correct steps early. A
    # context ladder then partly measures history length rather than history content. Surface it
    # so the caller can re-draw with a tighter --max-per-task or hand-swap steps.
    mi = statistics.median([p["step_idx"] for p in picked_inc]) if picked_inc else 0
    mc = statistics.median([p["step_idx"] for p in picked_cor]) if picked_cor else 0
    print("median step_idx: incorrect %.1f | correct %.1f%s"
          % (mi, mc, "   <- IMBALANCED: the ladder partly measures history LENGTH, not content"
             if abs(mi - mc) > 8 else ""))
    if len(picked_inc) < a.n_incorrect or len(picked_cor) < a.n_correct:
        print("WARNING: quota not filled (incorrect %d/%d, correct %d/%d) — relax --max-per-task"
              % (len(picked_inc), a.n_incorrect, len(picked_cor), a.n_correct))
    print("\nREVIEW sel.json by hand before running: check the loop steps really are loops and "
          "the 'revisit' correct steps really are legitimate revisits.")
    return 0


# --------------------------------------------------------------------------- sweep

def cmd_run(a):
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
    import probes
    from openai import OpenAI

    sel = json.load(open(a.selection))
    steps = sel["steps"]
    if a.max_steps:
        steps = steps[:a.max_steps]

    cfg = probes.ProbeConfig(
        model=a.model, tokenizer_path=a.tokenizer, base_url=a.base_url,
        temperature=a.temperature, top_p=a.top_p, top_k=a.top_k, min_p=0.0,
        presence_penalty=0.0, repetition_penalty=1.0, seed_base=a.seed_base)
    client = OpenAI(api_key="EMPTY", base_url=a.base_url)

    n_ok = n_tot = 0

    def _one_cell(s, ci, cx, rl):
        """One probe call. Returns the record dict, or None if the cell is skipped/errored.
        Pure w.r.t. shared state so it can run in a thread pool (the calls are IO-bound)."""
        if cx in CONTEXT_NEEDS_FUTURE and not s["ctx"].get("future_obs"):
            return None                          # terminal step: no one-step-ahead to show
        prompt = build_prompt(s["ctx"], cx, rl, with_commands=not a.no_commands)
        # Deterministic and disjoint per (task, step, condition). The task hash matters only for
        # bookkeeping — step_idx alone collides across episodes — and at temperature 0 the seed
        # has no effect on the output at all.
        seed = (a.seed_base + (hash(s["task_id"]) % 100000) * 100000
                + int(s["step_idx"]) * 1000 + ci)
        try:
            _c, rec = probes._call(client, cfg, prompt, max_tokens=4, seed=seed)
        except Exception as e:                   # never let one cell kill the sweep
            sys.stderr.write("ERROR %s/%s %s%s: %r\n" % (s["task_id"], s["step_idx"], cx, rl, e))
            return None
        top = probes._first_nonws_top(rec["gen_logprobs"])
        p_yes, p_no, conf, U, ok = probes.yesno_mass(top)
        return (ok, prompt, seed, conf, U, p_yes, p_no, top, rec, cx, rl)

    with open(a.out, "a") as fo:
        for si, s in enumerate(steps):
            cells = [(ci, cx, rl) for ci, (cx, rl) in enumerate(CONDITIONS)]
            if a.concurrency > 1:
                with cf.ThreadPoolExecutor(max_workers=a.concurrency) as ex:
                    results = list(ex.map(lambda c: _one_cell(s, *c), cells))
            else:
                results = [_one_cell(s, *c) for c in cells]
            for r in results:
                if r is None:
                    continue
                ok, prompt, seed, conf, U, p_yes, p_no, top, rec, cx, rl = r
                n_tot += 1
                n_ok += 1 if ok else 0
                fo.write(json.dumps({
                    "kind": "probe", "probe_schema_version": probes.PROBE_SCHEMA_VERSION,
                    "ctxrule_schema_version": SCHEMA_VERSION,
                    "probe_kind": "ptrue", "stage": "action" if cx != "C4" else "thought",
                    "context_id": cx, "rule_id": rl, "with_commands": not a.no_commands,
                    "prompt_version_id": "ptrue_ctxrule_%s_%s" % (cx, rl),
                    "run_id": s["run_id"], "task_id": s["task_id"], "step_idx": s["step_idx"],
                    "source_call_kind": s.get("source_call_kind"),
                    "label": s["label"], "stratum": s["stratum"],
                    "action_repeats_prior": s.get("action_repeats_prior"),
                    # carried so `report` can show WHICH step, WHY the judges called it, and its
                    # scores together, without needing the selection file or the corpus
                    "step_meta": {
                        "task": s["ctx"]["task"], "thought": s["ctx"]["thought"],
                        "action": s["ctx"]["action"],
                        "n_incorrect_votes": s.get("n_incorrect_votes"),
                        "n_valid_votes": s.get("n_valid_votes"),
                        "judge_votes": s.get("judge_votes"),
                        "judge_reasons": s.get("judge_reasons"),
                        "n_prior_actions": s.get("n_prior_actions"),
                    },
                    "probe_seed": seed, "probe_prompt": prompt,
                    "parsed_value": conf, "value_units": "P(Yes) over {Yes,No} mass",
                    "U": U, "parse_ok": ok, "p_yes": p_yes, "p_no": p_no,
                    "first_token_top": [{"token": t["token"], "logprob": t["logprob"]} for t in top],
                    "record": rec,
                }) + "\n")
            fo.flush()
            print("[%d/%d] %s step %s: %d conditions (parse_ok %d/%d)"
                  % (si + 1, len(steps), s["task_id"][:40], s["step_idx"], len(CONDITIONS), n_ok, n_tot))
            sys.stdout.flush()
    print("\nDONE: %d steps x %d conditions -> %s | parse_ok %d/%d" %
          (len(steps), len(CONDITIONS), a.out, n_ok, n_tot))
    return 0


# --------------------------------------------------------------------------- report

def _mean(xs):
    return statistics.fmean(xs) if xs else None


def _fmt(x, nd=3):
    return "n/a" if x is None else ("%.*f" % (nd, x))


def _auroc(pairs):
    """AUROC with positive class = incorrect, ties at half credit. `pairs` = [(U, label)].
    Equivalent to P(U_incorrect > U_correct) — a pure ranking read, unaffected by the scale
    shifts that move mean U around between contexts.

    Rank-based (Mann-Whitney U with average ranks for ties), O(n log n). The naive
    all-pairs form is O(n_inc * n_cor) and, inside a 2000-sample bootstrap over 11 conditions
    at n=300, that is ~5e8 Python operations — minutes per condition instead of milliseconds."""
    if not pairs:
        return None
    srt = sorted(pairs, key=lambda p: p[0])
    n_pos = sum(1 for _u, y in srt if y == 1)
    n_neg = len(srt) - n_pos
    if not n_pos or not n_neg:
        return None
    rank_sum = 0.0
    i = 0
    while i < len(srt):                     # average rank within each tie group
        j = i
        while j + 1 < len(srt) and srt[j + 1][0] == srt[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        rank_sum += avg_rank * sum(1 for k in range(i, j + 1) if srt[k][1] == 1)
        i = j + 1
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def _auroc_ci(pairs_by_task, n_boot=2000, seed=12345):
    """Trajectory-clustered bootstrap CI: resample EPISODES (with their steps), not steps.
    Steps within a trajectory are correlated — a step-level bootstrap would understate the CI."""
    tasks = sorted(pairs_by_task)
    if len(tasks) < 2:
        return None, None
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        pool = []
        for _ in range(len(tasks)):
            pool.extend(pairs_by_task[tasks[rng.randrange(len(tasks))]])
        a = _auroc(pool)
        if a is not None:
            boots.append(a)
    if len(boots) < 50:
        return None, None
    boots.sort()
    return boots[int(0.025 * len(boots))], boots[min(len(boots) - 1, int(0.975 * len(boots)))]


def _paired(cells, keys, cond_a, cond_b, predicate=None):
    """Per-step U(cond_a) - U(cond_b) over the steps present (and parsed) in BOTH.
    Returns (median shift, n_down, n_up, n)."""
    d = []
    for k in keys:
        if predicate and not predicate(k):
            continue
        ua, ub = cells.get((k, cond_a)), cells.get((k, cond_b))
        if ua is None or ub is None:
            continue
        d.append(ua - ub)
    if not d:
        return None, 0, 0, 0
    return statistics.median(d), sum(1 for x in d if x < 0), sum(1 for x in d if x > 0), len(d)


def _cond_label(c):
    return "%s/%s" % c


def _steps_section(L, keys, meta, cells, conds):
    """Per-step detail: which step, what the 3 judges said, and the P(True) it got in every
    condition. At n~20 this IS the result — the aggregate tables below are a summary of it."""
    L.append("## Steps")
    L.append("")
    L.append("Per step: the 3-judge ensemble vote (the label), then P(Yes) — the model's P(True) "
             "— in each condition. `x` = the first token carried no Yes/No mass (unparsed, "
             "excluded from every aggregate, never imputed).")
    L.append("")
    for i, k in enumerate(keys, 1):
        m = meta[k]
        sm = m.get("step_meta") or {}
        lab = "INCORRECT" if m["label"] == 1 else "correct"
        L.append("### %d. %s — step %s — judge: **%s** (%s/%s votes incorrect), stratum `%s`"
                 % (i, k[1], k[2], lab, sm.get("n_incorrect_votes"), sm.get("n_valid_votes"),
                    m["stratum"]))
        L.append("")
        if sm.get("task"):
            L.append("- task: %s" % sm["task"].replace("\n", " ").strip())
        L.append("- action: `%s`%s" % (sm.get("action", "?"),
                                       "  (repeats a prior action)" if m.get("repeats") else ""))
        if sm.get("thought"):
            th = " ".join(sm["thought"].split())
            L.append("- reasoning: %s" % (th if len(th) <= 300 else th[:300] + " …"))
        L.append("")
        votes, reasons = sm.get("judge_votes") or {}, sm.get("judge_reasons") or {}
        if reasons:
            L.append("| judge | vote | reason |")
            L.append("|---|---|---|")
            for j in sorted(reasons):
                v = votes.get(j)
                L.append("| %s | %s | %s |" % (
                    j, "incorrect" if v == 1 else ("correct" if v == 0 else "?"),
                    (reasons[j] or "").replace("|", "\\|").replace("\n", " ")))
            L.append("")
        L.append("| " + " | ".join(_cond_label(c) for c in conds) + " |")
        L.append("|" + "---|" * len(conds))
        L.append("| " + " | ".join(
            ("x" if (k, c) not in cells else "%.3f" % (1.0 - cells[(k, c)])) for c in conds) + " |")
        L.append("")


def cmd_dump(a):
    """Print the real prompts for one selected step — the cheapest way to catch a malformed
    context block or a rule that reads wrong before spending any GPU time."""
    sel = json.load(open(a.selection))
    s = sel["steps"][a.step]
    print("### step %s / %s  label=%d stratum=%s  action=%r\n"
          % (s["task_id"], s["step_idx"], s["label"], s["stratum"], s["ctx"]["action"]))
    for cx, rl in CONDITIONS:
        p = build_prompt(s["ctx"], cx, rl, with_commands=not a.no_commands)
        print("=" * 78)
        print("### %s/%s  (%s | rule: %s)  [%d chars]" % (cx, rl, CONTEXT_DESC[cx], RULE_DESC[rl], len(p)))
        print("=" * 78)
        print(p if not a.head else "\n".join(p.splitlines()[:a.head] + ["   … <%d more lines>" % max(0, len(p.splitlines()) - a.head)]))
        print()
    return 0


def cmd_report(a):
    recs = [json.loads(l) for l in open(a.records) if l.strip()]
    if not recs:
        sys.exit("no records in %s" % a.records)

    meta = {}                                        # step key -> label / stratum / step_meta
    cells = {}                                       # (step key, (cx,rl)) -> U   (parsed only)
    parse_fail = {}
    seen = []                                        # conditions actually present, first-seen order
    for r in recs:
        k = (r["run_id"], r["task_id"], r["step_idx"])
        meta[k] = {"label": r["label"], "stratum": r["stratum"],
                   "repeats": r.get("action_repeats_prior"),
                   "step_meta": r.get("step_meta") or {}}
        cond = (r["context_id"], r["rule_id"])
        if cond not in seen:
            seen.append(cond)
        if r.get("parse_ok") and r.get("U") is not None:
            cells[(k, cond)] = float(r["U"])
        else:
            parse_fail[cond] = parse_fail.get(cond, 0) + 1

    # Report whatever grid was actually run (in the canonical order where they overlap), so a
    # partial or extended sweep reports correctly instead of showing phantom empty cells.
    conds = [c for c in CONDITIONS if c in seen] + [c for c in seen if c not in CONDITIONS]

    keys = sorted(meta, key=lambda k: (-meta[k]["label"], meta[k]["stratum"], str(k)))
    inc = [k for k in keys if meta[k]["label"] == 1]
    cor = [k for k in keys if meta[k]["label"] == 0]
    ref = PRODUCTION_CONDITION

    # ---- matrix CSV: rows = steps, cols = conditions, values = U (higher = more uncertain)
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["run_id", "task_id", "step_idx", "label", "stratum"] +
                       ["U_%s_%s" % c for c in conds])
            for k in keys:
                w.writerow(list(k) + [meta[k]["label"], meta[k]["stratum"]] +
                           [_fmt(cells.get((k, c)), 4) for c in conds])

    L = []
    L.append("# P(True) context x rule probe — %d steps (%d incorrect / %d correct), %d conditions"
             % (len(keys), len(inc), len(cor), len(conds)))
    L.append("")
    L.append("Conditions run: " + ", ".join("`%s`" % _cond_label(c) for c in conds) +
             ".  Baseline = `%s` (the production P(True) prompt)." % _cond_label(ref))
    L.append("")
    L.append("- context: " + "; ".join("**%s** %s" % (k, CONTEXT_DESC[k]) for k in CONTEXTS
                                       if any(c[0] == k for c in conds)))
    L.append("- rule: " + "; ".join("**%s** %s" % (k, RULE_DESC[k]) for k in RULES
                                    if any(c[1] == k for c in conds)))
    L.append("")
    L.append("U = P(No) renormalized over {Yes,No} = 1 - P(True); higher = more uncertain the step "
             "is right. **Delta = mean U(incorrect) - mean U(correct)** is the separation. "
             "Unparsed cells are excluded, never imputed.")
    L.append("")

    # At n in the hundreds a full per-step dump is unreadable; show the steps where the probe
    # MOVED most between the production prompt and pre-hindsight (the informative ones), and
    # point at the CSV for the rest.
    if a.steps_detail and len(keys) > a.steps_detail:
        movers = sorted(keys, key=lambda k: -abs(cells.get((k, ("C5", "R0")), 0.0)
                                                 - cells.get((k, ref), 0.0)))[:a.steps_detail]
        shown = [k for k in keys if k in set(movers)]
        L.append("_Showing the %d steps with the largest |U(C5) − U(production)| shift, of %d "
                 "total — the full matrix is in the CSV._" % (len(shown), len(keys)))
        L.append("")
    else:
        shown = keys
    if a.steps_detail:
        _steps_section(L, shown, meta, cells, conds)

    # ---- per-condition separation
    L.append("## Separation per condition")
    L.append("")
    L.append("AUROC (positive class = incorrect) is the ranking read — unlike Delta it is immune "
             "to the scale shifts that move mean U between contexts. CI = 95%, "
             "trajectory-clustered bootstrap (episodes resampled with their steps).")
    L.append("")
    L.append("| condition | what changed | mean U inc | mean U cor | **Delta** | AUROC [95% CI] | sat | n | unparsed |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for c in conds:
        ui = [cells[(k, c)] for k in inc if (k, c) in cells]
        uc = [cells[(k, c)] for k in cor if (k, c) in cells]
        mi, mc = _mean(ui), _mean(uc)
        allu = ui + uc
        pairs, by_task = [], {}
        for k in keys:
            if (k, c) in cells:
                pairs.append((cells[(k, c)], meta[k]["label"]))
                by_task.setdefault(k[1], []).append((cells[(k, c)], meta[k]["label"]))
        au = _auroc(pairs)
        lo, hi = _auroc_ci(by_task) if au is not None else (None, None)
        au_s = "n/a" if au is None else (
            "%.3f" % au if lo is None else "%.3f [%.3f, %.3f]" % (au, lo, hi))
        what = ("production prompt" if c == ref else
                (CONTEXT_DESC[c[0]] if c[1] == "R0" else "%s rule%s"
                 % (RULE_DESC[c[1]], "" if c[0] == "C3" else " on %s" % CONTEXT_DESC[c[0]])))
        L.append("| **%s** | %s | %s | %s | **%s** | %s | %d | %d | %d |"
                 % (_cond_label(c), what, _fmt(mi), _fmt(mc),
                    _fmt(None if (mi is None or mc is None) else mi - mc), au_s,
                    sum(1 for x in allu if (1.0 - x) > 0.99), len(allu), parse_fail.get(c, 0)))
    L.append("")

    # ---- paired shifts vs the production cell
    L.append("## Paired per-step shift vs `%s`" % _cond_label(ref))
    L.append("")
    L.append("Median per-step U difference and how many paired steps moved which way. At this n "
             "the sign count is the evidence: a small median with 18/20 in one direction is a real "
             "shift; a large median with 11/20 is one or two outliers.")
    L.append("")
    L.append("| condition | median dU | down | up | n | median dU (inc) | median dU (cor) |")
    L.append("|---|---|---|---|---|---|---|")
    for c in conds:
        if c == ref:
            continue
        med, dn, up, n = _paired(cells, keys, c, ref)
        mi, _, _, _ = _paired(cells, keys, c, ref, predicate=lambda k: meta[k]["label"] == 1)
        mc, _, _, _ = _paired(cells, keys, c, ref, predicate=lambda k: meta[k]["label"] == 0)
        L.append("| %s | %s | %d | %d | %d | %s | %s |"
                 % (_cond_label(c), _fmt(med), dn, up, n, _fmt(mi), _fmt(mc)))
    L.append("")

    # ---- the diagnostics the design exists for
    L.append("## Diagnostics")
    L.append("")

    L.append("### 1. Rule effect: detection or compliance?")
    L.append("")
    L.append("`C3/R2` adds the repeat-rule to the production prompt, which contains the history a "
             "repeat could be detected in. `C0/R2` adds the SAME rule to a prompt with NO history "
             "in it — nothing there to detect. If the two move U by similar amounts, the rule is "
             "being complied with, not applied. Read the loop-step columns first: R2 is a rule "
             "about repeats, so a median over all steps dilutes a real 4-step effect into noise.")
    L.append("")
    L.append("| comparison | history in prompt | dU loop steps | up/n | dU all steps | up/n |")
    L.append("|---|---|---|---|---|---|")
    for cx in CONTEXTS:
        if (cx, "R2") not in conds or (cx, "R0") not in conds:
            continue
        ml, _d, ul, nl = _paired(cells, keys, (cx, "R2"), (cx, "R0"),
                                 predicate=lambda k: meta[k]["stratum"] == "loop")
        ma, _d2, ua, na = _paired(cells, keys, (cx, "R2"), (cx, "R0"))
        L.append("| %s/R2 - %s/R0 | %s | %s | %d/%d | %s | %d/%d |"
                 % (cx, cx, "yes" if CONTEXT_HAS_HISTORY[cx] else "**NO**",
                    _fmt(ml), ul, nl, _fmt(ma), ua, na))
    L.append("")
    if ("C3", "R3") in conds:
        med, dn, up, n = _paired(cells, keys, ("C3", "R3"), ref)
        L.append("Decoy floor — `C3/R3` (an irrelevant rule, same shape and tone) vs baseline: "
                 "median dU %s, %d up / %d down of %d. This is the pure *a rule was stated* "
                 "effect; R1 and R2 have to beat it to mean anything." % (_fmt(med), up, dn, n))
        L.append("")

    L.append("### 2. Does the rule hit loop errors specifically?")
    L.append("")
    L.append("A rule that raises U on every incorrect step equally is global pessimism, not rule "
             "application. Per stratum, on the production prompt.")
    L.append("")
    L.append("| stratum | label | dU (C3/R2 - C3/R0) | up | down | n | dU (C3/R1 - C3/R0) |")
    L.append("|---|---|---|---|---|---|---|")
    for st in sorted({meta[k]["stratum"] for k in keys}):
        pred = lambda k, st=st: meta[k]["stratum"] == st
        m2, d2, u2, n2 = _paired(cells, keys, ("C3", "R2"), ref, predicate=pred)
        m1, _, _, _ = _paired(cells, keys, ("C3", "R1"), ref, predicate=pred)
        lab = "incorrect" if any(meta[k]["label"] == 1 for k in keys if meta[k]["stratum"] == st) else "correct"
        L.append("| %s | %s | %s | %d | %d | %d | %s |" % (st, lab, _fmt(m2), u2, d2, n2, _fmt(m1)))
    L.append("")
    L.append("The `revisit` row is the false-positive test: those are CORRECT steps that legitimately "
             "repeat a location. If R2 raises U there too, the rule buys its separation by "
             "manufacturing false positives — weigh that against the Delta column before calling "
             "it an improvement.")
    L.append("")

    L.append("### 3. Context ladder (factor A, no rule)")
    L.append("")
    L.append("| context | contents | mean U inc | mean U cor | Delta |")
    L.append("|---|---|---|---|---|")
    for cx in CONTEXTS:
        c = (cx, "R0")
        if c not in conds:
            continue
        ui = [cells[(k, c)] for k in inc if (k, c) in cells]
        uc = [cells[(k, c)] for k in cor if (k, c) in cells]
        L.append("| %s | %s | %s | %s | %s |"
                 % (cx, CONTEXT_DESC[cx], _fmt(_mean(ui)), _fmt(_mean(uc)),
                    _fmt(None if not ui or not uc else _mean(ui) - _mean(uc))))
    L.append("")
    mi_idx = statistics.median([k[2] for k in inc]) if inc else 0
    mc_idx = statistics.median([k[2] for k in cor]) if cor else 0
    if any(c[0] in CONTEXT_NEEDS_FUTURE for c in conds):
        L.append("**C5/C6 are pre-hindsight**: they show the probe what the action actually "
                 "produced. Expect them to separate best — that is the point, and it is not a "
                 "fair comparison with C0-C4. They are a deployable probe only where actions are "
                 "reversible (act, observe, assess, undo); otherwise read them as the ceiling on "
                 "what P(True) could know. C6 minus C5 isolates how much of that comes from the "
                 "agent's own continuation rather than the environment's response.")
        L.append("")
    L.append("Caveat on this ladder: median step_idx is %.1f (incorrect) vs %.1f (correct). Where "
             "those differ, the incorrect steps carry longer histories, so C2/C3 vs C0/C1 partly "
             "measures history LENGTH, not history content." % (mi_idx, mc_idx))
    L.append("")
    L.append("At n~20, read the Steps section and the matrix CSV — the informative cases are "
             "individual steps where a condition flips the model hard, not the means.")

    out = "\n".join(L) + "\n"
    if a.out:
        open(a.out, "w").write(out)
        print("wrote %s%s" % (a.out, " and %s" % a.csv if a.csv else ""))
    else:
        print(out)
    return 0


# --------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("select", help="pick a stratified step sample from a frozen corpus (GPU-free)")
    s.add_argument("--uq", required=True)
    s.add_argument("--judge", required=True)
    s.add_argument("--out", default="sel.json")
    s.add_argument("--n-incorrect", type=int, default=10)
    s.add_argument("--n-correct", type=int, default=10)
    s.add_argument("--n-loop", type=int, default=4, help="loop/repeat errors within --n-incorrect")
    s.add_argument("--n-inadmissible", type=int, default=3)
    s.add_argument("--n-revisit", type=int, default=3, help="legitimate-revisit CORRECT steps")
    s.add_argument("--max-per-task", type=int, default=2)
    s.add_argument("--match-step-idx", action="store_true",
                   help="choose the `plain` correct steps to match the incorrect step_idx "
                        "distribution, so the context ladder is not confounded by history length")
    s.add_argument("--require-history", action="store_true", default=True)
    s.add_argument("--no-require-future", dest="require_future", action="store_false", default=True,
                   help="allow terminal steps (no successor). They cannot get C5/C6, which breaks "
                        "the fully-paired design for the pre-hindsight rungs — off by default.")
    s.add_argument("--seed", type=int, default=20260730)
    s.set_defaults(fn=cmd_select)

    r = sub.add_parser("run", help="sweep the 5x4 conditions (needs a live vLLM)")
    r.add_argument("--selection", required=True)
    r.add_argument("--out", required=True)
    # Model-agnostic: served name / tokenizer / endpoint are all flags, defaulting to the same
    # PROBE_* env vars the rest of Phase-2 uses. --tokenizer takes a HF id OR a local snapshot
    # path (the models4 runs pass a snapshot dir), so any served model works unchanged.
    env = __import__("os").environ
    r.add_argument("--model", default=env.get("PROBE_MODEL", "qwen"))
    r.add_argument("--tokenizer", default=env.get("PROBE_TOKENIZER", "Qwen/Qwen3.6-35B-A3B"))
    r.add_argument("--base-url", default=env.get("PROBE_BASE_URL", "http://localhost:8000/v1"))
    r.add_argument("--temperature", type=float, default=0.0)
    r.add_argument("--top-p", type=float, default=1.0)
    r.add_argument("--top-k", type=int, default=20)
    r.add_argument("--seed-base", type=int, default=9000)
    r.add_argument("--max-steps", type=int, default=None)
    r.add_argument("--concurrency", type=int, default=8,
                   help="probe calls in flight per step (IO-bound; 1 = strictly serial)")
    r.add_argument("--no-commands", action="store_true",
                   help="drop AVAILABLE COMMANDS from every context (stricter ablation)")
    r.set_defaults(fn=cmd_run)

    p = sub.add_parser("report", help="matrix CSV + markdown from the sweep records (GPU-free)")
    p.add_argument("--records", required=True)
    p.add_argument("--csv", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--steps-detail", type=int, default=24,
                   help="max steps in the per-step section (0 = omit it); the biggest "
                        "hindsight movers are shown when the sample is larger")
    p.set_defaults(fn=cmd_report)

    d = sub.add_parser("dump", help="print the 9 prompts for one selected step (GPU-free)")
    d.add_argument("--selection", required=True)
    d.add_argument("--step", type=int, default=0, help="index into the selection")
    d.add_argument("--head", type=int, default=0, help="truncate each prompt to N lines (0 = full)")
    d.add_argument("--no-commands", action="store_true")
    d.set_defaults(fn=cmd_dump)

    t = sub.add_parser("selftest", help="assert C3/R0 == the production P(True) prompt")
    t.set_defaults(fn=lambda a: _selftest())

    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
