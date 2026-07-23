"""tau tagging for ALFWorld — the transition-type label (I, W, R, C) for a step.

CONTRACT (theory doc §2.5, spec §0.4): tau is a PURE FUNCTION of the environment action
string. It is derived from the tool/environment specification, NEVER from LLM self-classification.
A silent mis-tag corrupts E2/E3 invisibly while leaving E1 looking fine, so:
  - every ALFWorld action family has an explicit rule (see TAU_TABLE and tests/test_tau_map.py),
  - an unrecognized action returns tau_of(...) -> None (caller must log + count it, never guess).

tau fields (spec §0.4):
  I : information-gathering / epistemic action (1) vs not (0)
  W : world-modifying (1) vs not (0)
  R : reversible within an episode (1) vs irreversible (0)
  C : cost class in {"free", "cheap", "costly"}

Static mapping (spec §0.4), authoritative:
  | family                         | I | W | R | C      |
  |--------------------------------|---|---|---|--------|
  | look / examine / inventory     | 1 | 0 | 1 | free   |
  | go to X                        | 1 | 0 | 1 | cheap  |
  | open X / close X               | 0 | 1 | 1 | cheap  |
  | take X from Y / put X in/on Y  | 0 | 1 | 1 | cheap  |
  | heat X / cool X / clean X      | 0 | 1 | 0 | costly |
  | slice X                        | 0 | 1 | 0 | costly |
  | use X                          | 0 | 1 | 1 | cheap  |

heat/cool/clean/slice are treated as irreversible (R=0): ALFWorld does not undo these
state transformations within an episode. Changing this table is an EXPERIMENT change.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Tau:
    I: int
    W: int
    R: int
    C: str  # "free" | "cheap" | "costly"

    def as_dict(self) -> dict:
        return {"I": self.I, "W": self.W, "R": self.R, "C": self.C}


# Each rule: (compiled verb pattern matched against the normalized action, Tau).
# Order matters only for disambiguation; patterns are written to be mutually exclusive.
# We match on the leading verb/phrase so object names ("drawer 2", "apple 1") never affect tau.
_RULES: list[tuple[re.Pattern[str], Tau]] = [
    # information-gathering, non-world-modifying
    # `help` is TextWorld's universal meta-command (lists affordances) — present in every ALFWorld
    # admissible set; epistemic/free/reversible like look/inventory. (Deviation from spec §0.4 table,
    # documented: the table omits it because it is an engine meta-command, not an ALFRED task action.)
    (re.compile(r"^(look|inventory|help)$"),   Tau(1, 0, 1, "free")),
    (re.compile(r"^examine\b"),                Tau(1, 0, 1, "free")),
    (re.compile(r"^go to\b"),                  Tau(1, 0, 1, "cheap")),
    # world-modifying, reversible, cheap
    (re.compile(r"^(open|close)\b"),           Tau(0, 1, 1, "cheap")),
    (re.compile(r"^(take|pick up)\b"),         Tau(0, 1, 1, "cheap")),
    (re.compile(r"^(put|move|place)\b"),       Tau(0, 1, 1, "cheap")),
    (re.compile(r"^(use|toggle|turn on|turn off)\b"), Tau(0, 1, 1, "cheap")),
    # world-modifying, IRREVERSIBLE, costly
    (re.compile(r"^(heat|cool|clean)\b"),      Tau(0, 1, 0, "costly")),
    (re.compile(r"^slice\b"),                  Tau(0, 1, 0, "costly")),
]


def normalize_action(action: str) -> str:
    """Lowercase, collapse whitespace, strip surrounding punctuation. Pure/deterministic."""
    return re.sub(r"\s+", " ", (action or "").strip().lower()).strip(" .")


def tau_of(action: str) -> Tau | None:
    """Return the Tau for an ALFWorld action string, or None if no family matches.

    None is a signal, not a default: the caller MUST log the raw action and count it toward a
    reported unrecognized-action rate. Never substitute a guessed tag.
    """
    a = normalize_action(action)
    if not a:
        return None
    for pat, tau in _RULES:
        if pat.search(a):
            return tau
    return None
