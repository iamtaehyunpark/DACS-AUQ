"""Elicited-uncertainty probes (spec §0.6). Each returns (U, parsed): U in [0,1] with 1 = max
uncertainty, and a parsed flag. POLICY (frozen, spec E1★.6): unparseable -> (None, False); the
caller records the flag and EXCLUDES that step from the probe's metrics, reporting the per-cell
exclusion rate. We never impute a value for an unparseable elicitation.
"""
from __future__ import annotations

import math
import re

# 5-point verbal scale -> uncertainty (spec §0.6 probe 2).
VERBAL_SCALE = {
    "almost certain": 0.05,
    "likely": 0.275,
    "unsure": 0.5,
    "unlikely": 0.725,
    "almost certainly not": 0.95,
}


def numeric_uncertainty(text: str | None) -> tuple[float | None, bool]:
    """Probe 1 / U_A: parse an integer 0-100 -> U = 1 - n/100. Unparseable -> (None, False).

    Parsing rules (each guards a real failure mode of instruction-echoing models):
    - 'N/100' and 'N out of 100' denominators parse as N ("85/100" is 85, not 100).
    - Scale echoes ('0-100', '0 to 100') are stripped before matching, so a reply that
      repeats the question ("On a scale of 0-100, I'd say 85") parses 85, not 0.
    - Among remaining standalone integers the LAST wins (models state the answer at the end).
    - An integer > 100 is a protocol violation -> (None, False). Clamping it would be
      imputation, which the frozen policy forbids (E1*.6: exclude + report, never impute).
    """
    if not text:
        return None, False
    m = re.search(r"\b(\d{1,3})\s*(?:/|out of)\s*100\b", text)
    if m:
        n = int(m.group(1))
        return (1.0 - n / 100.0, True) if n <= 100 else (None, False)
    cleaned = re.sub(r"\b0\s*(?:-|to|–)\s*100\b", " ", text)
    hits = re.findall(r"\b(\d{1,3})\b", cleaned)
    if not hits:
        return None, False
    n = int(hits[-1])
    if n > 100:
        return None, False
    return 1.0 - n / 100.0, True


def verbal_uncertainty(text: str | None) -> tuple[float | None, bool]:
    """Probe 2: map a 5-point phrase -> uncertainty. Longest phrase wins ('almost certainly not'
    before 'almost certain'). Unparseable -> (None, False)."""
    if not text:
        return None, False
    t = text.lower()
    for phrase in sorted(VERBAL_SCALE, key=len, reverse=True):
        if phrase in t:
            return VERBAL_SCALE[phrase], True
    return None, False


def yesno_uncertainty(first_token_top: dict[str, float] | None) -> tuple[float | None, bool]:
    """Probe 3: U_T = P('No') from first-token logprobs, renormalized over {Yes,No} variants
    (case/leading-space handled by stripping). No yes/no mass present -> (None, False)."""
    if not first_token_top:
        return None, False
    p_yes = p_no = 0.0
    for tok, lp in first_token_top.items():
        t = tok.strip().lower()
        if t in ("yes", "y"):
            p_yes += math.exp(lp)
        elif t in ("no", "n"):
            p_no += math.exp(lp)
    if p_yes + p_no <= 0:
        return None, False
    return p_no / (p_yes + p_no), True


# -- Probe V: verbalized (in-generation) confidence tags --------------------
_CONF_RE = re.compile(r"<confidence>\s*([0-9]*\.?[0-9]+)\s*</confidence>", re.IGNORECASE)
_EXPL_RE = re.compile(r"<explanation>\s*(.*?)\s*</explanation>", re.IGNORECASE | re.DOTALL)
_CONF_OPEN_RE = re.compile(r"<confidence>", re.IGNORECASE)


def verbalized_confidence(text: str | None) -> tuple[float | None, str | None, bool, bool]:
    """Parse an in-generation <confidence>c</confidence> tag (Probe V, c in [0,1]).

    Returns (U = 1 - c, raw_tag_text, parsed, multiple_tags_anomaly). Multiple tags: the
    FIRST wins (the one adjacent to the content it qualifies) and the anomaly is flagged
    for logging. Missing/malformed/out-of-range -> (None, raw-or-None, False, anomaly).
    """
    if not text:
        return None, None, False, False
    matches = _CONF_RE.findall(text)
    anomaly = len(matches) > 1
    m = _CONF_RE.search(text)
    if not m:
        return None, None, False, anomaly
    raw = m.group(0)
    try:
        c = float(m.group(1))
    except ValueError:
        return None, raw, False, anomaly
    if not (0.0 <= c <= 1.0):
        return None, raw, False, anomaly
    return 1.0 - c, raw, True, anomaly


def strip_confidence_tag(text: str) -> str:
    """Truncate a stage output at its (terminal) confidence tag BEFORE it is passed
    downstream (no-feedback invariant: the verbalized value must never appear in a later
    call's prompt). Everything from the first <confidence> onward is dropped; the pre-tag
    content is returned rstripped and otherwise byte-identical. Use for the decoupled
    thought/action outputs, whose contract puts the tag at the END."""
    m = _CONF_OPEN_RE.search(text or "")
    return (text[:m.start()] if m else (text or "")).rstrip()


def remove_confidence_tags(text: str) -> str:
    """Excise confidence tag(s) IN PLACE, keeping surrounding text. Use where content
    legitimately follows the tag (AUQ's <explanation> comes after <confidence>) — e.g.
    when building post-hoc probe contexts, which must not see the in-generation value
    (it would anchor the post-hoc reading and inflate E1b's rank agreement trivially)."""
    if not text:
        return ""
    out = _CONF_RE.sub("", text)
    # unclosed trailing tag (stop-string ate the close): drop from the opener to end-of-line
    out = re.sub(r"<confidence>[^\n<]*", "", out, flags=re.IGNORECASE)
    return out


def remove_self_assessment(text: str) -> str:
    """Excise confidence AND explanation tags (decision 2026-07-16, pre-data): AUQ's
    <explanation> is the self-assessment in prose form — leaving it in a post-hoc probe
    context leaks Probe V's judgment and makes E1b's rank agreement partially circular.
    For probe-independence analyses, err toward independence. The excised explanation is
    already logged separately (probes.auq_explanation_text)."""
    if not text:
        return ""
    out = remove_confidence_tags(text)
    out = _EXPL_RE.sub("", out)
    # unclosed trailing explanation (stop-string ate the close): drop opener to end of text
    out = re.sub(r"<explanation>.*", "", out, flags=re.IGNORECASE | re.DOTALL)
    return out


def auq_entangled(text: str | None) -> tuple[float | None, str | None, bool]:
    """Parse AUQ's in-generation tags: returns (U = 1 - conf, explanation_text, parsed).
    conf is a float in [0,1] inside <confidence>...</confidence>. Missing/malformed -> (None, expl, False).
    Explanation is returned when present even if confidence failed (kept for qualitative analysis)."""
    if not text:
        return None, None, False
    expl_m = _EXPL_RE.search(text)
    expl = expl_m.group(1).strip() if expl_m else None
    conf_m = _CONF_RE.search(text)
    if not conf_m:
        return None, expl, False
    try:
        c = float(conf_m.group(1))
    except ValueError:
        return None, expl, False
    if not (0.0 <= c <= 1.0):
        return None, expl, False
    return 1.0 - c, expl, True
