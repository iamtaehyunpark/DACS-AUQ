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
    """Probe 1 / U_A: parse an integer 0-100 -> U = 1 - n/100. Unparseable -> (None, False)."""
    if not text:
        return None, False
    m = re.search(r"\b(\d{1,3})\b", text)
    if not m:
        return None, False
    n = min(100, int(m.group(1)))
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


# -- AUQ in-generation entangled probe (Cell B canonical, probe 4) ---------
_CONF_RE = re.compile(r"<confidence>\s*([0-9]*\.?[0-9]+)\s*</confidence>", re.IGNORECASE)
_EXPL_RE = re.compile(r"<explanation>\s*(.*?)\s*</explanation>", re.IGNORECASE | re.DOTALL)


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
