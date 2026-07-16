"""Post-hoc self-evaluation probes P1-P3 (spec §0.6). COMPARATORS, not primary: under the
verbalized := in-generation stipulation (theory §2.4) a later-call judgment on the frozen
stage output is a different measurement class — it drifts toward plausibility/provenance
reading (Kim & Kang 2605.27752). Every call: temperature=0, fresh generation, context =
everything the relevant stage saw + the stage's own output, then the question.
The value NEVER feeds back into the agent's context (spec §0.5); all probes here are
offline-able on frozen trajectories (invariant §5.2 of the 2026-07-16 handoff).

Raw completions are always kept (E1★.6: log every parse failure with the raw completion).
`guided=True` optionally constrains the output at the harness level (vLLM guided_regex) —
default OFF: forcing a format converts a refusal into an arbitrary number and erases the
per-cell exclusion-rate signal. Decide from Cell A pilot parse rates before the freeze.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.agent.llm import VLLMClient
from src.metrics import elicited as parsers

_NUMERIC_REGEX = r"(100|[0-9]{1,2})"


@dataclass
class Elicitation:
    value: float | None
    parsed: bool
    raw_text: str


def _ask(client: VLLMClient, context: str, question: str, *, seed: int,
         max_tokens: int, guided_regex: str | None = None):
    # No stop string: raw-completions models often lead with a newline, and stop=["\n"]
    # terminated those replies as EMPTY text (observed 2026-07-16 smoke: 45.6% P1 parse
    # rate). Instead we cap tokens and parse the first non-empty line.
    return client.generate(
        context.rstrip() + "\n\n" + question,
        temperature=0.0, top_p=1.0, max_tokens=max_tokens, seed=seed,
        guided_regex=guided_regex,
    )[0]


def _first_content_line(text: str) -> str:
    """First non-empty line of a completion — the answer; later lines are transcript
    continuation junk whose stray digits must not reach the parser."""
    for line in (text or "").splitlines():
        if line.strip():
            return line
    return ""


def numeric(client: VLLMClient, stage_context: str, question: str, *,
            seed: int, guided: bool = False) -> Elicitation:
    gen = _ask(client, stage_context, question, seed=seed, max_tokens=8,
               guided_regex=_NUMERIC_REGEX if guided else None)
    u, ok = parsers.numeric_uncertainty(_first_content_line(gen.text))
    return Elicitation(u, ok, gen.text)


def verbal(client: VLLMClient, stage_context: str, question: str, *, seed: int) -> Elicitation:
    gen = _ask(client, stage_context, question, seed=seed, max_tokens=16)
    u, ok = parsers.verbal_uncertainty(_first_content_line(gen.text))
    return Elicitation(u, ok, gen.text)


def yesno(client: VLLMClient, stage_context: str, question: str, *, seed: int) -> Elicitation:
    gen = _ask(client, stage_context, question, seed=seed, max_tokens=4)
    # first NON-WHITESPACE token carries the yes/no mass (models often lead with a newline)
    top = next((t for tok, t in zip(gen.tokens, gen.top_logprobs) if tok.strip()), None)
    u, ok = parsers.yesno_uncertainty(top)
    return Elicitation(u, ok, gen.text)
