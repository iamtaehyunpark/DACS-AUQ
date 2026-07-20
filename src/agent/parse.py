"""Parsing of agent generations — tag extraction, action selection, verb/arg split.

The entangled loop (AUQ App. A.6.1/A.6.2 prompts) emits <think>/<action> (+ <confidence>/
<explanation> with the suffix) in one generation; we need the CONTENT of think/action plus
their CHARACTER SPANS in the generated text, because the per-stage entropy metrics
(thought_mte/ppl/sp vs action_mte/ppl/sp) are computed over the corresponding token spans
via src/metrics/logprob.char_span_to_token_range.

Action-execution policy (logged, never silent): prefer the <action> tag content; if it is not
verbatim-admissible, fall back to the longest admissible command contained in the generation;
else pass the raw string to the env (ALFWorld answers "Nothing happens." to invalid commands).
The match kind is recorded per step so parse quality is reportable per cell (E1★.6).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.env.tau_map import normalize_action

# Amendment 2026-07-20 (pre E0 rerun): the E0 run showed Qwen3.6 frequently closes the
# reasoning block with </thinking> (70/507 steps) or leaves it unclosed before <action>
# (13/507); the strict </think>-only regex dropped those thoughts, which also blanked the
# <think> slot in the entangled history. Both spellings are accepted on BOTH sides of the
# tag, and an unclosed block falls back to content-up-to-the-next-known-tag, flagged not-ok.
_THINK_RE = re.compile(r"<think(?:ing)?>(.*?)</think(?:ing)?>", re.IGNORECASE | re.DOTALL)
_THINK_OPEN_RE = re.compile(r"<think(?:ing)?>(.*?)(?=<(?:action|confidence|explanation)\b|$)",
                            re.IGNORECASE | re.DOTALL)
_ACTION_RE = re.compile(r"<action>(.*?)</action>", re.IGNORECASE | re.DOTALL)
_ACTION_OPEN_RE = re.compile(r"<action>(.*?)(?=$|\n|<)", re.IGNORECASE | re.DOTALL)


@dataclass
class TaggedGen:
    think: str | None = None
    think_span: tuple[int, int] | None = None    # char span of think CONTENT in the generation
    think_tag_ok: bool = False                   # closed think block (either spelling) present
    action: str | None = None
    action_span: tuple[int, int] | None = None
    action_tag_ok: bool = False                  # well-formed <action>...</action> present


def patch_unclosed(text: str, tag: str) -> str:
    """If `<tag>` was opened but the generation stopped before `</tag>` (stop-string ate it,
    or max_tokens truncation), append the closing tag so downstream regexes see well-formed text."""
    lo = text.lower()
    if f"<{tag}>" in lo and f"</{tag}>" not in lo:
        return text + f"</{tag}>"
    return text


def parse_entangled(text: str) -> TaggedGen:
    """Extract <think> and <action> content + char spans from one entangled generation.
    Tolerates: </thinking>-style closes (either spelling, either side); an unclosed think
    block (content up to the next known tag, flagged not-ok); an unclosed <action>
    (content to end-of-line / next tag, flagged not-ok). Among closed think blocks the
    first NON-EMPTY one wins (models occasionally emit degenerate empty <think></think>
    pairs before the real block); if all are empty the first is kept."""
    out = TaggedGen()
    closed = list(_THINK_RE.finditer(text))
    m = next((c for c in closed if c.group(1).strip()), closed[0] if closed else None)
    if m:
        out.think = m.group(1).strip()
        out.think_span = (m.start(1), m.end(1))
        out.think_tag_ok = True
    else:
        m = _THINK_OPEN_RE.search(text)
        if m and m.group(1).strip():
            out.think = m.group(1).strip()
            out.think_span = (m.start(1), m.end(1))
    m = _ACTION_RE.search(text)
    if m:
        out.action = m.group(1).strip()
        out.action_span = (m.start(1), m.end(1))
        out.action_tag_ok = True
    else:
        m = _ACTION_OPEN_RE.search(text)
        if m and m.group(1).strip():
            out.action = m.group(1).strip()
            out.action_span = (m.start(1), m.end(1))
    return out


def choose_executable(action_text: str | None, generation_text: str,
                      admissible: list[str]) -> tuple[str, str]:
    """Pick the command string to execute. Returns (command, match_kind) where match_kind is
    one of: 'exact' (tag content is admissible after normalization), 'contained' (longest
    admissible command found inside the generation), 'raw' (no match — executed as-is).
    """
    norm_adm = {normalize_action(c): c for c in admissible}
    if action_text:
        key = normalize_action(action_text)
        if key in norm_adm:
            return norm_adm[key], "exact"
    hay = normalize_action(generation_text if action_text is None else action_text)
    hits = [c for k, c in norm_adm.items() if k and k in hay]
    if not hits and action_text is not None:
        hay = normalize_action(generation_text)
        hits = [c for k, c in norm_adm.items() if k and k in hay]
    if hits:
        return max(hits, key=len), "contained"
    return (action_text or generation_text).strip(), "raw"


# Leading verb phrases for the schema's action_parsed {"verb", "arg"} split. Longest-first so
# "turn on" wins over a hypothetical "turn". Mirrors the families in src/env/tau_map.py.
_VERBS = sorted(
    ["go to", "pick up", "turn on", "turn off", "take", "put", "move", "place", "open",
     "close", "use", "toggle", "heat", "cool", "clean", "slice", "examine", "look",
     "inventory", "help"],
    key=len, reverse=True,
)


def parse_verb_arg(action: str) -> dict:
    """Split an action string into {"verb", "arg"} on the known family verbs; unknown verb ->
    verb = first word, arg = rest (never fails; tau_of() is the authority on families)."""
    a = normalize_action(action)
    for v in _VERBS:
        if a == v or a.startswith(v + " "):
            return {"verb": v, "arg": a[len(v):].strip()}
    parts = a.split(" ", 1)
    return {"verb": parts[0] if parts else "", "arg": parts[1] if len(parts) > 1 else ""}
