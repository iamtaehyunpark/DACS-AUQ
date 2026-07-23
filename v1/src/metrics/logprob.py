"""Entropy-family probes, per ReDAct Appendix A (arXiv:2604.07036). Zero extra generations.

Definitions, VERBATIM from ReDAct App. A (higher = more uncertain), for a generated span
y=[y_1..y_L] with token logprobs log p(y_i | x, y_<i):

  SP  (Sequence Probability) = − Σ_i log p(y_i)          # total negative log-likelihood
  PPL (Perplexity)           = − (1/L) Σ_i log p(y_i)     # MEAN NLL — note: ReDAct's "PPL" is the
                                                          #   mean NLL, NOT exp(mean NLL). Named to match.
  MTE (Mean Token Entropy)   = (1/L) Σ_i H(y_i)           # H = entropy of the token distribution

H(y_i) is computed from the top-k alternatives vLLM returns (k=20). This is a lower-bound
approximation of full-vocab entropy, but it is consistent across every step, so ranking-based
analysis (AUROC, PRR, quantiles) is unaffected — which is all E1 uses these for.

Metrics are computed PER STAGE and only compared WITHIN a cell (spec E1★.3): thought-span for the
reasoning probe, action-span for the action probe.
"""
from __future__ import annotations

import math


def token_entropy(top: dict[str, float]) -> float:
    """Entropy (nats) of one position's top-k distribution. Empty -> 0."""
    if not top:
        return 0.0
    ps = [math.exp(lp) for lp in top.values()]
    return -sum(p * math.log(max(p, 1e-12)) for p in ps)


def mte(top_logprobs: list[dict]) -> float:
    """Mean Token Entropy over a span."""
    if not top_logprobs:
        return 0.0
    return sum(token_entropy(t) for t in top_logprobs) / len(top_logprobs)


def sp(logprobs: list[float]) -> float:
    """Sequence Probability score = − Σ log p (total NLL)."""
    return -sum(logprobs) if logprobs else 0.0


def ppl(logprobs: list[float]) -> float:
    """ReDAct 'Perplexity' = − (1/L) Σ log p (mean NLL). Not exp()."""
    if not logprobs:
        return 0.0
    return -sum(logprobs) / len(logprobs)


def char_span_to_token_range(tokens: list[str], char_start: int, char_end: int) -> tuple[int, int]:
    """Map a [char_start, char_end) substring range to a [tok_start, tok_end) token-index range,
    by accumulating token lengths. Returns the full range if the span can't be located."""
    if not tokens:
        return (0, 0)
    spans, pos = [], 0
    for tok in tokens:
        spans.append((pos, pos + len(tok)))
        pos += len(tok)
    idx = [i for i, (a, b) in enumerate(spans) if b > char_start and a < char_end]
    return (idx[0], idx[-1] + 1) if idx else (0, len(tokens))


def stage_metrics(tokens: list[str], logprobs: list[float], top_logprobs: list[dict],
                  tok_start: int = 0, tok_end: int | None = None) -> dict[str, float]:
    """Compute {mte, ppl, sp} over the token span [tok_start, tok_end). Defaults to the whole span."""
    end = len(tokens) if tok_end is None else tok_end
    lp = logprobs[tok_start:end]
    tp = top_logprobs[tok_start:end]
    return {"mte": mte(tp), "ppl": ppl(lp), "sp": sp(lp)}
