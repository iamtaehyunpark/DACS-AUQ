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
SCHEMA_VERSION = "1.1.0"

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
    # U_* uncertainties, when present, must be normalized to [0,1] (*_raw holds tag text
    # and *_parsed holds booleans — neither is a value field).
    for k, v in probes.items():
        if (k.startswith("U_") and not k.endswith(("_raw", "_parsed"))
                and v is not None and not (0.0 <= float(v) <= 1.0)):
            raise ValueError(f"probe {k!r}={v!r} outside [0,1] (1 = maximally uncertain)")


def write_jsonl(path: str, records: list[dict]) -> None:
    """Append-safe writer: validates every record before serializing (mode 'a' to never clobber)."""
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            validate_record(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
