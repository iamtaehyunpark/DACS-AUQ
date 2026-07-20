"""The frozen per-step JSONL record (spec §0.3). This schema is frozen; ALL experiments read it.

One step in one condition = one JSONL record. `probes` fields not applicable to a condition are
set to None (null), never omitted. All U_* values are normalized to [0,1] where 1 = maximally
uncertain (elicited confidence c in [0,100] -> U = 1 - c/100).

`tau` is assigned by the environment wrapper (src/env/tau_map.py), never by the model.
"""
from __future__ import annotations

import json
from typing import Any

# 1.1.0 (2026-07-16): pre-data amendment — verbalized/posthoc probe split (elicited_* ->
# posthoc_*, U_auq_entangled -> U_T_verbalized, added U_[TA]_verbalized{,_raw}). No data
# had been generated under 1.0.0.
# 1.2.0 (2026-07-16): pre-data amendment — EOS-repair continuation flags
# (U_[TA]_verbalized_continued): True = value obtained via a forced-prefix continuation
# after the model stopped without emitting the tag; False = parsed in-generation;
# None = probe N/A. Smoke evidence: 18/104 steps omitted <confidence> at EOS.
# 1.3.0 (2026-07-20): pre-data amendment for the E0 rerun (first E0 attempt discarded —
# 24.3% empty-thought rate vs the 10% gate). (a) think parser accepts </thinking>-spelled
# and unclosed reasoning blocks (E0: 70 + 13 / 507 steps silently dropped, which also
# blanked the <think> slot in entangled history); (b) one seed-offset re-draw on an
# empty non-cap generation (one episode degenerated to bare EOS on 39/50 steps), logged
# in extra.generation_retry; (c) EOS-repair never fires on an empty generation. No probe
# fields added or renamed; thought_text extraction semantics changed.
# 1.4.0 (2026-07-20): pre-data amendment, decided jointly for E0-full and E1 —
# PER-STEP seeds. sampling.seed now varies within an episode:
# seed = seed_base + task_index*100 + step_idx (episode summary keeps the episode
# base). Old per-episode seed reuse replayed the identical RNG stream every step,
# which with copy-collapsed loop distributions produced byte-exact locked repetition
# (E0 smoke: 41 identical thoughts; P(exact) ~0.3/step under independent draws).
# E0 validates the judge on the step distribution E1 will produce, so the policy
# changes for both at once, pre-data. No fields added or renamed.
# 1.5.0 (2026-07-20): pre-data amendment after the 4bd6a08 smoke TERMINAL failure
# (71/104 steps degenerate instruction-list echo). Per-step seeds exposed the model's
# true per-draw tail risk of degenerate openings ~50x/episode where the old
# per-episode seed sampled it once; the raw-action fallback then fed echo text into
# history as an <action>, cascading 2 onsets into 71 bad steps. Fixes, contract-level
# only: (a) the entangled prompt now ends with the opening <think> tag (prefill) —
# extra.generation therefore begins INSIDE the think block, without an opener;
# (b) the one-re-draw retry extends to degenerate generations (no think-close, no
# <action>), logged in extra.generation_retry {retry_reason, retry_degenerate};
# (c) EOS-repair never fires on degenerate text. Probe semantics untouched: Probe V
# still in-generation, stage entropy still spans only generated tokens.
# 1.6.0 (2026-07-20): pre-data amendment from the decoupled loop-control DIAGNOSTIC
# (not a protocol step; run to test whether looping replicates under ReDAct's exact
# architecture). Found: the v1 (tag-free) DECOUPLED action call had no degenerate-content
# retry guard -- only emptiness. 45% of action calls (diagnostic, n=69) drew an immediate
# blank first token; the retry sometimes returned a stray '</think>' (the reasoning-tuned
# model's habitual close-of-thinking artifact leaking past the one-line contract), which
# was accepted AS THE ACTION, unflagged (retry_degenerate=False), executed raw, and
# rendered into the next step's history as 'Action: </think>' -- same failure class as
# the entangled instruction-echo cascade (0617ee5), never given the equivalent guard.
# Fix: _degenerate_action_line (any '<' + letter/slash -- no legitimate ALFWorld command
# contains one) wired into the v1 action call's retry only (v2's tag-ended contract is
# exempt). No fields added; generation_retry.retry_degenerate now correctly flags this
# case for the decoupled path. Scoped to Cell C/D generation; does not touch E0
# (entangled-only) -- Step 5 (E0 judge labeling) is unaffected and unblocked by this.
# 1.7.0 (2026-07-20): pre-data amendment -- ROOT CAUSE of the v1 empty-action rate found
# by re-verifying the 2181701 diagnostic rerun (byte-identical generations confirmed by
# hash, as forced by per-step seeds). The v1 (tag-free) decoupled action call used
# stop=["\n"] on a prompt that already ends with "\n": whenever the model sampled a
# newline as its FIRST token (~50% of draws at temp 0.7 -- a formatting choice, not a
# refusal; the thought call had 0/69 empties), the stop fired at 1 completion token and
# the record got an empty action, which executed as "Nothing happens." (tau=None) --
# 14/50 wasted turns on Bowl-301 alone, confounding the loop-control comparison. All 31
# retried first draws show finish_reason='stop' at exactly 1 token. Fixes, contract-level
# only: (a) v1 action call drops the "\n" stop and draws to max_action_tokens; the action
# read is the FIRST CONTENT LINE (fixed rule -- a degenerate first line is kept+flagged,
# never searched past); (b) _degenerate_action_line judges that same first line, so
# post-line ramble cannot fail a good action; (c) pre-registered span rule: action-stage
# entropy (action_mte/ppl/sp/nll) covers the command line's tokens ONLY, uniform across
# v1/v2 -- leading newlines and post-line ramble are formatting, not action content
# (matches how think-block spans already exclude non-content). Same failure class as
# 1.3.0/1.5.0: the contract cutting off the read at a formatting token. Scoped to
# decoupled Cells C/D; entangled path (E0, Cells A/B) untouched. ReDAct Fig-6 prompt
# text remains byte-identical -- stop sequences were never part of their published spec.
SCHEMA_VERSION = "1.7.0"

# The probe keys the schema knows about. Present in every record (None when N/A for the condition),
# so downstream analysis can rely on a fixed shape and compute per-cell exclusion rates.
#
# TERMINOLOGY (definitional commitment, 2026-07-16, Taehyun — see uq_theory.md §2.4):
# "verbalized" = confidence emitted IN THE SAME GENERATION as the content it qualifies
# (Probe V, PRIMARY, both architectures; Cell B's instance is AUQ's verbatim suffix).
# "posthoc" = post-hoc self-evaluation, a separate temperature=0 call on the frozen stage
# output (Probes P1-P3, comparators only, never the decision variable).
PROBE_KEYS: tuple[str, ...] = (
    # Probe V — verbalized (in-generation), primary. *_raw keeps the tag text for parse audits.
    "U_T_verbalized",
    "U_T_verbalized_raw",
    "U_A_verbalized",
    "U_A_verbalized_raw",
    "auq_explanation_text",          # Cell B only: AUQ's <explanation> rides the same generation
    # Probes P1-P3 — post-hoc self-evaluation, comparators (offline-able on frozen trajectories)
    "U_T_posthoc_numeric",
    "U_T_posthoc_verbal",
    "U_T_posthoc_yesno",
    "U_A_posthoc_numeric",
    # entropy-family, per stage (ReDAct App. A): MTE, PPL(=mean NLL), SP(=sum NLL)
    "thought_mte", "thought_ppl", "thought_sp",
    "action_mte", "action_ppl", "action_sp",
    "action_nll",
)

# Whether each probe parsed on this step (None = probe not run for this condition,
# True/False = ran and parsed / failed to parse). Drives per-cell exclusion-rate reporting
# (our policy: unparseable -> excluded from that probe's metrics, NOT imputed).
PARSE_FLAG_KEYS: tuple[str, ...] = (
    "U_T_verbalized_parsed",
    "U_A_verbalized_parsed",
    "U_T_verbalized_continued",
    "U_A_verbalized_continued",
    "U_T_posthoc_numeric_parsed",
    "U_T_posthoc_verbal_parsed",
    "U_T_posthoc_yesno_parsed",
    "U_A_posthoc_numeric_parsed",
)

_VALID_C = {"free", "cheap", "costly"}


def new_probes() -> dict[str, Any]:
    """A probes dict with every known key present and None (spec: fields N/A are null, not omitted)."""
    d: dict[str, Any] = {k: None for k in PROBE_KEYS}
    d.update({k: None for k in PARSE_FLAG_KEYS})
    return d


def make_record(
    *,
    run_id: str,
    condition: str,
    task_id: str,
    step_idx: int,
    state_summary_hash: str,
    thought_text: str,
    action_text: str,
    action_parsed: dict,
    tau: dict,
    observation_text: str,
    probes: dict,
    sampling: dict,
    label: dict | None = None,
    timing: dict | None = None,
) -> dict:
    """Build one frozen step record. Validates the invariants that later stages depend on."""
    rec = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "condition": condition,
        "task_id": task_id,
        "step_idx": step_idx,
        "state_summary_hash": state_summary_hash,
        "thought_text": thought_text,
        "action_text": action_text,
        "action_parsed": action_parsed,
        "tau": tau,
        "observation_text": observation_text,
        "probes": probes,
        "sampling": sampling,
        "label": label if label is not None else {"judge": None, "judge_raw": None, "human_1": None, "human_2": None},
        "timing": timing if timing is not None else {},
    }
    validate_record(rec)
    return rec


def validate_record(rec: dict) -> None:
    """Raise ValueError on any violation of the frozen contract. Cheap; call on every write."""
    for key in ("run_id", "condition", "task_id", "step_idx", "thought_text",
                "action_text", "tau", "probes", "sampling"):
        if key not in rec:
            raise ValueError(f"record missing required field: {key!r}")
    if not isinstance(rec["step_idx"], int) or rec["step_idx"] < 0:
        raise ValueError(f"step_idx must be a non-negative int, got {rec['step_idx']!r}")

    tau = rec["tau"]
    # tau may be None ONLY for an unrecognized action (logged + counted upstream); if present it must be well-formed.
    if tau is not None:
        for f in ("I", "W", "R", "C"):
            if f not in tau:
                raise ValueError(f"tau missing field {f!r}: {tau!r}")
        if tau["I"] not in (0, 1) or tau["W"] not in (0, 1) or tau["R"] not in (0, 1):
            raise ValueError(f"tau I/W/R must be 0 or 1: {tau!r}")
        if tau["C"] not in _VALID_C:
            raise ValueError(f"tau C must be one of {_VALID_C}: {tau['C']!r}")

    probes = rec["probes"]
    for k in PROBE_KEYS:
        if k not in probes:
            raise ValueError(f"probes missing key {k!r} (N/A fields must be present as null, not omitted)")
    # U_* uncertainties, when present, must be normalized to [0,1] (*_raw holds tag text;
    # *_parsed and *_continued hold booleans — none is a value field).
    for k, v in probes.items():
        if (k.startswith("U_") and not k.endswith(("_raw", "_parsed", "_continued"))
                and v is not None and not (0.0 <= float(v) <= 1.0)):
            raise ValueError(f"probe {k!r}={v!r} outside [0,1] (1 = maximally uncertain)")


def write_jsonl(path: str, records: list[dict]) -> None:
    """Append-safe writer: validates every record before serializing (mode 'a' to never clobber)."""
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            validate_record(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
