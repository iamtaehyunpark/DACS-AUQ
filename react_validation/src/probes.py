"""Phase-2 UQ instrumentation — SEPARATE confidence-probe calls (post-hoc self-evaluation).

POST-HOC and NON-INTRUSIVE. Given a frozen Phase-1 UQ log (the JSONL that chat_react.py /
chat_react_entangled.py write under REACT_UQLOG), this module re-reads each agent step's
already-generated thought/action and issues SEPARATE model calls that elicit uncertainty
*about* that frozen text. It never re-runs, modifies, or perturbs the agent, and never feeds
a probe value back into any agent context — the probes are offline-able on frozen trajectories
(spec §0.5 / §0.6, the "post-hoc self-evaluation" comparator class).

Every probe call goes through uqlog.instrumented_chat, so each is logged with the same ground
truth as a Phase-1 call: verbatim post-template prompt + token ids, per-token logprobs with the
top-20 alternatives (crucially the FIRST-token top-20 for P(True)), sampling config, timing.
The raw completion is authoritative; the parsed scalar is a convenience carried with a parse_ok
flag (unparseable is NEVER imputed — spec E1★.6).

Probes (each for the thought stage AND the action stage, except `targeted` which is thought-only):
  * ptrue           — P(True) (Kadavath et al.). "... Yes or No." First generated token's top-20
                      logprob mass over Yes/yes/YES vs No/no/NO, renormalized. THE key probe.
  * sep_verbalized  — separate-call FIRST-PERSON confidence, single number 0.00-1.00.
  * posthoc_numeric — separate-call SUPPLIED-TEXT self-evaluation, integer 0-100
                      (verbatim of prompts/posthoc_numeric{,_action}.txt).
  * targeted        — u(q_t): extract the single key claim q_t the thought commits to (a small
                      logged extraction call, `qt_extract`), then ask confidence in THAT claim
                      alone (thought fluency removed). The most novel probe. Thought-only.

TERMINOLOGY / TAXONOMY FLAG (memory `verbalized-in-generation`, schema 1.1.0): the project reserves
`U_*_verbalized` for confidence emitted IN the same generation as the content (Probe V). All four
probes here are SEPARATE later calls, i.e. the "post-hoc self-evaluation" class. The task that
commissioned Phase-2 asked for a probe it called "verbalized (separate call)" with fields
U_T_verbalized / U_A_verbalized; to avoid colliding with the frozen in-generation meaning we log it
under probe_kind `sep_verbalized` and carry the caller's requested name in `metric_field`
(U_T_verbalized_sep / U_A_verbalized_sep). This naming tension is flagged for the PI.

No agent files are imported or modified; only uqlog (Phase-1's own logger) is reused.
"""
from __future__ import annotations

import math
import re

from uqlog import instrumented_chat

# --------------------------------------------------------------------------- config

PROBE_SCHEMA_VERSION = "2.0.0"

# Per-probe deterministic seed offsets (added to base + step_idx*_SEED_STRIDE). Distinct per
# (probe, stage) so no two probe calls on a step share an RNG stream; wide gaps leave room.
_SEED_STRIDE = 1000
_STAGE_OFFSET = {"thought": 0, "action": 100}
_PROBE_OFFSET = {"ptrue": 0, "sep_verbalized": 10, "posthoc_numeric": 20,
                 "targeted": 30, "qt_extract": 40}


# --------------------------------------------------------------------------- parsers
# Logic mirrors src/metrics/elicited.py (the frozen parse conventions) but is re-implemented
# locally so react_validation stays self-contained (it imports only uqlog, like Phase-1).

_YES = {"yes", "y", "yeah", "yep", "correct", "true"}
_NO = {"no", "n", "nope", "false", "incorrect"}


def yesno_mass(first_token_top):
    """P(True): from a first-token top-logprobs list [{'token','logprob'},...] compute
    (p_yes, p_no, confidence_yes, U, parse_ok). confidence_yes = P(Yes)/(P(Yes)+P(No));
    U = P(No)/(P(Yes)+P(No)) (1 = max uncertainty, matching elicited.yesno_uncertainty).
    Probabilities are summed over case/leading-space variants of Yes vs No. No yes/no mass
    present -> parse_ok False (excluded, never imputed)."""
    if not first_token_top:
        return 0.0, 0.0, None, None, False
    p_yes = p_no = 0.0
    for a in first_token_top:
        t = a["token"].strip().lower()
        if t in _YES:
            p_yes += math.exp(a["logprob"])
        elif t in _NO:
            p_no += math.exp(a["logprob"])
    z = p_yes + p_no
    if z <= 0:
        return p_yes, p_no, None, None, False
    return p_yes, p_no, p_yes / z, p_no / z, True


def parse_unit_confidence(text):
    """Parse a first-person confidence in [0,1]. Accepts '0.7', '.7', '0.70'; also a bare
    integer 0-100 or an 'N%' as a fallback (divided by 100 — models sometimes answer '80'
    despite the 0-1 instruction). Returns (confidence, U=1-confidence, parse_ok). LAST match
    wins (models state the answer last). Out-of-range / no number -> parse_ok False."""
    if not text:
        return None, None, False
    # percent form first ("80%") -> 0.80
    pcts = re.findall(r"(\d{1,3}(?:\.\d+)?)\s*%", text)
    if pcts:
        v = float(pcts[-1])
        if 0.0 <= v <= 100.0:
            c = v / 100.0
            return c, 1.0 - c, True
        return None, None, False
    nums = re.findall(r"\d*\.\d+|\d+", text)
    if not nums:
        return None, None, False
    v = float(nums[-1])
    if 0.0 <= v <= 1.0:
        return v, 1.0 - v, True
    if 1.0 < v <= 100.0:            # tolerate a 0-100 answer to a 0-1 question
        c = v / 100.0
        return c, 1.0 - c, True
    return None, None, False


def parse_numeric_0_100(text):
    """posthoc_numeric parser (mirrors elicited.numeric_uncertainty): integer 0-100 ->
    (n, U=1-n/100, parse_ok). Handles 'N/100'/'N out of 100' denominators and strips a
    '0-100' scale echo; LAST standalone integer wins; n>100 -> parse_ok False (never clamp)."""
    if not text:
        return None, None, False
    m = re.search(r"\b(\d{1,3})\s*(?:/|out of)\s*100\b", text)
    if m:
        n = int(m.group(1))
        return (n, 1.0 - n / 100.0, True) if n <= 100 else (None, None, False)
    cleaned = re.sub(r"\b0\s*(?:-|to|–)\s*100\b", " ", text)
    hits = re.findall(r"\b(\d{1,3})\b", cleaned)
    if not hits:
        return None, None, False
    n = int(hits[-1])
    if n > 100:
        return None, None, False
    return n, 1.0 - n / 100.0, True


def _first_content_line(text):
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _first_nonws_top(gen_logprobs):
    """The first NON-WHITESPACE generated token's top-20 list (models often lead with a
    newline/space whose top-20 carries no yes/no mass). Returns [] if none."""
    for g in gen_logprobs or []:
        if g["token"].strip():
            return g["top"]
    return []


# --------------------------------------------------------------------------- context reconstruction

_TASK_RE = re.compile(r"TASK DESCRIPTION:\s*\n(.*?)\n(?:ENVIRONMENT HISTORY:)", re.DOTALL)
_HIST_RE = re.compile(
    r"ENVIRONMENT HISTORY:\s*\n(.*?)\n(?:YOUR CURRENT REASONING:|AVAILABLE COMMANDS:)", re.DOTALL)


def parse_task_history(prompt_templated):
    """Pull the raw TASK / HISTORY blocks out of a Phase-1 call's `prompt_templated`. We match
    the harness's OWN literal section labels (written by chat_react*.py), which survive as plain
    substrings inside the chat-templated string — so this is robust to the chat template itself.
    Commands are taken from the step record's `admissible`, not parsed here."""
    task = m.group(1).strip() if (m := _TASK_RE.search(prompt_templated or "")) else ""
    hist = m2.group(1).strip() if (m2 := _HIST_RE.search(prompt_templated or "")) else ""
    return task, hist


def split_entangled(completion_raw):
    """Entangled joint completion -> (thought, action_line). Mirrors chat_react_entangled's
    parse: ignore any <think> block, thought = before first ACTION:, action = last ACTION: line."""
    t = completion_raw.split("</think>", 1)[-1] if "</think>" in completion_raw else completion_raw
    tm = re.search(r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", t, re.IGNORECASE | re.DOTALL)
    thought = tm.group(1).strip() if tm else t.split("ACTION:", 1)[0].strip()
    acts = re.findall(r"ACTION:\s*(.+)", t, re.IGNORECASE)
    action = acts[-1].splitlines()[0].strip().strip("`").strip() if acts else ""
    return thought, action


# --------------------------------------------------------------------------- prompt builders

def _ctx_block(task, history, commands):
    return ("TASK DESCRIPTION:\n%s\n"
            "ENVIRONMENT HISTORY:\n%s\n"
            "AVAILABLE COMMANDS:\n%s\n") % (task, history, commands)


_PREAMBLE = "You are evaluating an AI agent that is solving a task in an interactive environment.\n"

# ptrue (P(True), Kadavath et al.) -----------------------------------------------------------
def prompt_ptrue_thought(task, history, commands, thought):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "PROPOSED REASONING:\n%s\n\n" % thought +
            "Is the proposed reasoning above correct and appropriate for deciding the next "
            "action in this task?\nAnswer with a single word: Yes or No.")


def prompt_ptrue_action(task, history, commands, thought, action):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "AGENT REASONING:\n%s\nPROPOSED ACTION:\n%s\n\n" % (thought, action) +
            "Is the proposed action above the correct and appropriate next action for this "
            "task?\nAnswer with a single word: Yes or No.")


# sep_verbalized (separate-call FIRST-PERSON numeric confidence) ------------------------------
def prompt_sepverb_thought(task, history, commands, thought):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "PROPOSED REASONING:\n%s\n\n" % thought +
            "How confident are you that this reasoning is correct and sufficient to decide the "
            "next action? State your confidence as a single number from 0.00 (no confidence) to "
            "1.00 (complete confidence). Output only that number.")


def prompt_sepverb_action(task, history, commands, thought, action):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "AGENT REASONING:\n%s\nPROPOSED ACTION:\n%s\n\n" % (thought, action) +
            "How confident are you that this action is the correct next action? State your "
            "confidence as a single number from 0.00 to 1.00. Output only that number.")


# posthoc_numeric (separate-call SUPPLIED-TEXT self-evaluation, verbatim prompts/*.txt) -------
def prompt_posthoc_thought(task, history, commands, thought):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "REASONING:\n%s\n\n" % thought +
            "On a scale of 0-100, how confident are you that the reasoning above is factually "
            "correct and sufficient to decide the next action? Reply with a single integer.")


def prompt_posthoc_action(task, history, commands, thought, action):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "REASONING:\n%s\nACTION:\n%s\n\n" % (thought, action) +
            "On a scale of 0-100, how confident are you that the action above is the correct "
            "next action? Reply with a single integer.")


# targeted u(q_t) ----------------------------------------------------------------------------
def prompt_qt_extract(task, history, commands, thought):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "AGENT REASONING:\n%s\n\n" % thought +
            "The reasoning above commits to ONE key factual claim about the current state of the "
            "environment (for example: 'the potato is in the fridge', or 'the desk lamp is on "
            "desk 1'). In one short declarative sentence, state that single key claim. "
            "Output only the claim, nothing else.")


def prompt_targeted(task, history, commands, qt):
    return (_PREAMBLE + _ctx_block(task, history, commands) +
            "Consider this specific claim about the environment:\n\"%s\"\n\n" % qt +
            "How confident are you that this claim is true, given the task and the environment "
            "history above? State your confidence as a single number from 0.00 (certainly false) "
            "to 1.00 (certainly true). Output only that number.")


_PROMPT_VERSION = {
    "ptrue": "ptrue_v1",                       # Kadavath P(True), single-word Yes/No
    "sep_verbalized": "sep_verbalized_v1",     # first-person 0.00-1.00 (separate call)
    "posthoc_numeric": "posthoc_numeric_v1",   # verbatim prompts/posthoc_numeric{,_action}.txt
    "qt_extract": "qt_extract_v1",
    "targeted": "targeted_v1",
}
_METRIC_FIELD = {
    ("ptrue", "thought"): "U_T_ptrue", ("ptrue", "action"): "U_A_ptrue",
    ("sep_verbalized", "thought"): "U_T_verbalized_sep", ("sep_verbalized", "action"): "U_A_verbalized_sep",
    ("posthoc_numeric", "thought"): "U_T_posthoc_numeric", ("posthoc_numeric", "action"): "U_A_posthoc_numeric",
    ("targeted", "thought"): "U_T_targeted",
}


# --------------------------------------------------------------------------- probe runner


class ProbeConfig:
    """Sampling + call config for the probe calls. Defaults = Qwen official non-thinking
    (temperature 0.7, top_p 0.80, top_k 20, min_p 0.0, presence_penalty 1.5, repetition 1.0)
    per the Phase-2 task. NOTE (flagged for PI): the frozen post-hoc convention in
    src/probes/posthoc.py uses temperature=0; here we follow the task's 0.7 default but expose
    every knob, so a deterministic re-read (and, for P(True), a calibrated temp=1.0 first-token
    reading) is a one-flag change."""

    def __init__(self, *, model, tokenizer_path, base_url, temperature=0.7, top_p=0.80,
                 top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0,
                 seed_base=7000, qt_mode="llm",
                 max_tokens_ptrue=4, max_tokens_conf=8, max_tokens_qt=64):
        self.model = model
        self.tokenizer_path = tokenizer_path
        self.base_url = base_url
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.min_p = min_p
        self.presence_penalty = presence_penalty
        self.repetition_penalty = repetition_penalty
        self.seed_base = seed_base
        self.qt_mode = qt_mode
        self.max_tokens_ptrue = max_tokens_ptrue
        self.max_tokens_conf = max_tokens_conf
        self.max_tokens_qt = max_tokens_qt


def _seed(cfg, step_idx, probe_kind, stage):
    return (cfg.seed_base + int(step_idx) * _SEED_STRIDE
            + _PROBE_OFFSET[probe_kind] + _STAGE_OFFSET.get(stage, 0))


def _call(client, cfg, prompt, *, max_tokens, seed):
    return instrumented_chat(
        client, [{"role": "user", "content": prompt}], model=cfg.model,
        tokenizer_path=cfg.tokenizer_path, temperature=cfg.temperature, top_p=cfg.top_p,
        top_k=cfg.top_k, min_p=cfg.min_p, presence_penalty=cfg.presence_penalty,
        repetition_penalty=cfg.repetition_penalty, max_tokens=max_tokens, seed=seed,
        enable_thinking=False)


def _base_record(step, probe_kind, stage, target_text, prompt, rec, seed):
    """Common probe-log record envelope. `rec` is the full instrumented_chat ground-truth."""
    return {
        "kind": "probe",
        "probe_schema_version": PROBE_SCHEMA_VERSION,
        "probe_kind": probe_kind,
        "stage": stage,
        "prompt_version_id": _PROMPT_VERSION[probe_kind],
        "metric_field": _METRIC_FIELD.get((probe_kind, stage)),
        "run_id": step["run_id"],
        "task_id": step["task_id"],
        "step_idx": step["step_idx"],
        "source_call_kind": step["source_call_kind"],
        "target_text": target_text,
        "probe_seed": seed,
        "probe_prompt": prompt,
        "record": rec,
    }


def probe_ptrue(client, cfg, step, stage):
    ctx = step["ctx"]
    if stage == "thought":
        prompt = prompt_ptrue_thought(ctx["task"], ctx["history"], ctx["commands"], ctx["thought"])
        target = ctx["thought"]
    else:
        prompt = prompt_ptrue_action(ctx["task"], ctx["history"], ctx["commands"], ctx["thought"], ctx["action"])
        target = ctx["action"]
    seed = _seed(cfg, step["step_idx"], "ptrue", stage)
    _content, rec = _call(client, cfg, prompt, max_tokens=cfg.max_tokens_ptrue, seed=seed)
    top = _first_nonws_top(rec["gen_logprobs"])
    p_yes, p_no, conf, U, ok = yesno_mass(top)
    out = _base_record(step, "ptrue", stage, target, prompt, rec, seed)
    out.update({
        "parsed_value": conf,           # P(Yes) renormalized over {Yes,No}
        "value_units": "P(Yes) over {Yes,No} mass",
        "U": U, "parse_ok": ok,
        "p_yes": p_yes, "p_no": p_no,
        "first_token_top": [{"token": a["token"], "logprob": a["logprob"],
                             "prob": math.exp(a["logprob"])} for a in top],
    })
    return out


def probe_sepverb(client, cfg, step, stage):
    ctx = step["ctx"]
    if stage == "thought":
        prompt = prompt_sepverb_thought(ctx["task"], ctx["history"], ctx["commands"], ctx["thought"])
        target = ctx["thought"]
    else:
        prompt = prompt_sepverb_action(ctx["task"], ctx["history"], ctx["commands"], ctx["thought"], ctx["action"])
        target = ctx["action"]
    seed = _seed(cfg, step["step_idx"], "sep_verbalized", stage)
    content, rec = _call(client, cfg, prompt, max_tokens=cfg.max_tokens_conf, seed=seed)
    conf, U, ok = parse_unit_confidence(_first_content_line(content))
    out = _base_record(step, "sep_verbalized", stage, target, prompt, rec, seed)
    out.update({"parsed_value": conf, "value_units": "confidence in [0,1]", "U": U, "parse_ok": ok})
    return out


def probe_posthoc_numeric(client, cfg, step, stage):
    ctx = step["ctx"]
    if stage == "thought":
        prompt = prompt_posthoc_thought(ctx["task"], ctx["history"], ctx["commands"], ctx["thought"])
        target = ctx["thought"]
    else:
        prompt = prompt_posthoc_action(ctx["task"], ctx["history"], ctx["commands"], ctx["thought"], ctx["action"])
        target = ctx["action"]
    seed = _seed(cfg, step["step_idx"], "posthoc_numeric", stage)
    content, rec = _call(client, cfg, prompt, max_tokens=cfg.max_tokens_conf, seed=seed)
    n, U, ok = parse_numeric_0_100(_first_content_line(content))
    out = _base_record(step, "posthoc_numeric", stage, target, prompt, rec, seed)
    out.update({"parsed_value": n, "value_units": "integer 0-100", "U": U, "parse_ok": ok})
    return out


def probe_targeted(client, cfg, step):
    """u(q_t): extract q_t (logged as its own `qt_extract` probe record), then ask confidence
    in that isolated claim. Thought-only. Returns [qt_record, targeted_record]. If q_t extraction
    fails to yield a non-empty claim, the targeted call is skipped and a parse_ok=False targeted
    stub is emitted so the exclusion is visible (never imputed)."""
    ctx = step["ctx"]
    records = []
    # 1) extract q_t (or heuristic)
    qt_seed = _seed(cfg, step["step_idx"], "qt_extract", "thought")
    if cfg.qt_mode == "heuristic":
        qt = _heuristic_qt(ctx["thought"])
        qt_ok = bool(qt)
        qt_rec_env = None
    else:
        prompt_x = prompt_qt_extract(ctx["task"], ctx["history"], ctx["commands"], ctx["thought"])
        content_x, rec_x = _call(client, cfg, prompt_x, max_tokens=cfg.max_tokens_qt, seed=qt_seed)
        qt = _first_content_line(content_x).strip().strip('"').strip()
        qt_ok = bool(qt)
        qtr = _base_record(step, "qt_extract", "thought", ctx["thought"], prompt_x, rec_x, qt_seed)
        qtr.update({"parsed_value": qt or None, "value_units": "extracted claim q_t",
                    "U": None, "parse_ok": qt_ok})
        records.append(qtr)
    # 2) targeted confidence in q_t
    seed = _seed(cfg, step["step_idx"], "targeted", "thought")
    if not qt_ok:
        stub = {
            "kind": "probe", "probe_schema_version": PROBE_SCHEMA_VERSION, "probe_kind": "targeted",
            "stage": "thought", "prompt_version_id": _PROMPT_VERSION["targeted"],
            "metric_field": _METRIC_FIELD[("targeted", "thought")], "run_id": step["run_id"],
            "task_id": step["task_id"], "step_idx": step["step_idx"],
            "source_call_kind": step["source_call_kind"], "target_text": ctx["thought"],
            "qt_text": None, "qt_mode": cfg.qt_mode, "probe_seed": seed, "probe_prompt": None,
            "record": None, "parsed_value": None, "value_units": "confidence in [0,1]",
            "U": None, "parse_ok": False, "skipped_reason": "qt_extraction_empty",
        }
        records.append(stub)
        return records
    prompt = prompt_targeted(ctx["task"], ctx["history"], ctx["commands"], qt)
    content, rec = _call(client, cfg, prompt, max_tokens=cfg.max_tokens_conf, seed=seed)
    conf, U, ok = parse_unit_confidence(_first_content_line(content))
    out = _base_record(step, "targeted", "thought", ctx["thought"], prompt, rec, seed)
    out.update({"qt_text": qt, "qt_mode": cfg.qt_mode, "parsed_value": conf,
                "value_units": "confidence in [0,1]", "U": U, "parse_ok": ok})
    records.append(out)
    return records


def _heuristic_qt(thought):
    """Fallback q_t: last non-empty sentence of the thought (ALFWorld thoughts typically end on
    the state commitment / decision). Crude by design; the LLM extractor is the default."""
    sents = re.split(r"(?<=[.!?])\s+", (thought or "").strip())
    sents = [s.strip() for s in sents if s.strip()]
    return sents[-1] if sents else ""


_PROBE_FN = {
    "ptrue": probe_ptrue,
    "sep_verbalized": probe_sepverb,
    "posthoc_numeric": probe_posthoc_numeric,
}


def run_step_probes(client, cfg, step, *, kinds, stages):
    """Run the requested probes for one reconstructed step bundle. Returns a list of probe-log
    records. `targeted` is thought-only and handled specially (it also emits a qt_extract record)."""
    out = []
    for kind in kinds:
        if kind == "targeted":
            if "thought" in stages:
                out.extend(probe_targeted(client, cfg, step))
            continue
        fn = _PROBE_FN.get(kind)
        if fn is None:
            continue
        for stage in stages:
            if stage == "action" and not step["ctx"]["action"]:
                continue                       # no action text to probe (e.g. empty action)
            out.append(fn(client, cfg, step, stage))
    return out
