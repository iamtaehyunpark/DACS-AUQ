"""tau tagging for ALFWorld — the transition-type label (I, W, R, C) for a step (spec V2 §0.4).

tau is a PURE FUNCTION of the environment action string, derived from the tool/environment
grammar, NEVER from LLM self-classification. An unrecognized action -> tau_of(...) == None
(the caller MUST log it and count it toward an unrecognized-action rate; never guess).

tau fields:
  I : information-gathering / epistemic (1) vs not (0)
  W : world-modifying (1) vs not (0)
  R : reversible within an episode (1) vs irreversible (0)
  C : cost class in {"free","cheap","costly"}

Static map (spec V2 §0.4, authoritative):
  look / examine / inventory     1 0 1 free
  go to X                        1 0 1 cheap
  open X / close X               0 1 1 cheap
  take X from Y / move X to Y    0 1 1 cheap   (ALFWorld 0.4.2 placement verb is "move ... to")
  heat X / cool X / clean X      0 1 0 costly  (irreversible within an episode)
  slice X                        0 1 0 costly
  use X                          0 1 1 cheap

Run `python tau_map.py` to execute the per-family unit tests (A12; mandatory before a run).
"""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Tau:
    I: int
    W: int
    R: int
    C: str

    def as_dict(self) -> dict:
        return {"I": self.I, "W": self.W, "R": self.R, "C": self.C}


_RULES: list[tuple[re.Pattern[str], Tau]] = [
    (re.compile(r"^(look|inventory|help)$"), Tau(1, 0, 1, "free")),
    (re.compile(r"^examine\b"), Tau(1, 0, 1, "free")),
    (re.compile(r"^go to\b"), Tau(1, 0, 1, "cheap")),
    (re.compile(r"^(open|close)\b"), Tau(0, 1, 1, "cheap")),
    (re.compile(r"^(take|pick up)\b"), Tau(0, 1, 1, "cheap")),
    (re.compile(r"^(put|move|place)\b"), Tau(0, 1, 1, "cheap")),
    (re.compile(r"^(use|toggle|turn on|turn off)\b"), Tau(0, 1, 1, "cheap")),
    (re.compile(r"^(heat|cool|clean)\b"), Tau(0, 1, 0, "costly")),
    (re.compile(r"^slice\b"), Tau(0, 1, 0, "costly")),
]


def normalize_action(action: str) -> str:
    return re.sub(r"\s+", " ", (action or "").strip().lower()).strip(" .")


def tau_of(action: str) -> Tau | None:
    a = normalize_action(action)
    if not a:
        return None
    for pat, tau in _RULES:
        if pat.search(a):
            return tau
    return None


def tau_dict(action: str):
    t = tau_of(action)
    return t.as_dict() if t else None


if __name__ == "__main__":
    # A12 unit tests — one assertion per action family; a silent mis-tag corrupts E2/E3.
    cases = {
        "look": Tau(1, 0, 1, "free"),
        "inventory": Tau(1, 0, 1, "free"),
        "examine potato 1": Tau(1, 0, 1, "free"),
        "go to fridge 1": Tau(1, 0, 1, "cheap"),
        "open microwave 1": Tau(0, 1, 1, "cheap"),
        "close cabinet 2": Tau(0, 1, 1, "cheap"),
        "take potato 1 from countertop 1": Tau(0, 1, 1, "cheap"),
        "move potato 1 to microwave 1": Tau(0, 1, 1, "cheap"),
        "put mug 3 in/on shelf 1": Tau(0, 1, 1, "cheap"),
        "use desklamp 1": Tau(0, 1, 1, "cheap"),
        "heat potato 1 with microwave 1": Tau(0, 1, 0, "costly"),
        "cool potato 1 with fridge 1": Tau(0, 1, 0, "costly"),
        "clean lettuce 1 with sinkbasin 1": Tau(0, 1, 0, "costly"),
        "slice bread 1 with knife 1": Tau(0, 1, 0, "costly"),
    }
    for act, exp in cases.items():
        got = tau_of(act)
        assert got == exp, "tau mismatch for %r: got %r expected %r" % (act, got, exp)
    # object names must never affect tau
    assert tau_of("go to drawer 12") == tau_of("go to cabinet 1")
    # unrecognized -> None (signal, not default). Note: tau operates on the clean single-line
    # action_parsed, so it matches the leading verb; a non-command string yields None.
    for bad in ("", "flibber the wotsit", "THOUGHT: I should go", "nothing happens."):
        assert tau_of(bad) is None, "expected None for %r, got %r" % (bad, tau_of(bad))
    print("tau_map: all %d family cases + invariants pass" % len(cases))
