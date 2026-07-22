"""Phase-1 UQ instrumentation — PURE OBSERVATION.

Wraps a chat call so that, in addition to the normal completion, it captures the ground
truth needed to recompute every uncertainty metric offline: per-token logprobs + top-20
alternatives over the whole response, the verbatim post-template prompt + token ids, the
generation config (incl. seed), timing, and token-offset spans.

It does NOT change what the model generates: same messages, same sampling params, a fixed
per-call seed; requesting logprobs is metadata-only (vLLM scores the tokens it already
sampled). Raw completion + logprobs are the ground truth; parsed fields are conveniences
computed downstream.
"""
import time
from transformers import AutoTokenizer

_TOK = {}


def _tokenizer(path):
    if path not in _TOK:
        _TOK[path] = AutoTokenizer.from_pretrained(path)
    return _TOK[path]


def instrumented_chat(client, messages, *, model, tokenizer_path, temperature, top_p,
                      max_tokens, seed, top_k=20, min_p=0.0, presence_penalty=1.5,
                      repetition_penalty=1.0, enable_thinking=False):
    """Return (content, record). record holds the full ground truth for this call."""
    tok = _tokenizer(tokenizer_path)
    templated = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                        enable_thinking=enable_thinking)
    prompt_ids = tok(templated, add_special_tokens=False)["input_ids"]

    t0 = time.monotonic()
    r = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, top_p=top_p,
        max_tokens=max_tokens, seed=seed, presence_penalty=presence_penalty,
        logprobs=True, top_logprobs=20,
        extra_body={"chat_template_kwargs": {"enable_thinking": enable_thinking},
                    "top_k": top_k, "min_p": min_p, "repetition_penalty": repetition_penalty},
    )
    latency_ms = (time.monotonic() - t0) * 1000.0

    ch = r.choices[0]
    content = ch.message.content or ""
    gen = []
    if ch.logprobs and ch.logprobs.content:
        for t in ch.logprobs.content:
            gen.append({
                "token": t.token,
                "bytes": t.bytes,
                "logprob": t.logprob,
                "top": [{"token": a.token, "logprob": a.logprob} for a in t.top_logprobs],
            })
    rec = {
        "prompt_templated": templated,
        "prompt_token_ids": prompt_ids,
        "prompt_tokens": r.usage.prompt_tokens,
        "completion_raw": content,
        "completion_tokens": r.usage.completion_tokens,
        "finish_reason": ch.finish_reason,
        "gen_logprobs": gen,
        "config": {"model": model, "temperature": temperature, "top_p": top_p,
                   "top_k": top_k, "min_p": min_p, "presence_penalty": presence_penalty,
                   "repetition_penalty": repetition_penalty, "max_tokens": max_tokens,
                   "seed": seed, "enable_thinking": enable_thinking},
        "latency_ms": round(latency_ms, 1),
    }
    return content, rec


def char_to_token_span(gen, start_char, end_char):
    """Map a [start,end) char range in the completion to a [i,j) token-index range in gen.

    The tokens in `gen` concatenate to the completion text, so cumulative token char-lengths
    give each token's char extent. Returns the smallest token range covering [start,end).
    """
    if not gen:
        return [0, 0]
    pos = 0
    tok_start = None
    tok_end = 0
    for idx, g in enumerate(gen):
        lo, hi = pos, pos + len(g["token"])
        if tok_start is None and hi > start_char:
            tok_start = idx
        if lo < end_char:
            tok_end = idx + 1
        pos = hi
    return [tok_start if tok_start is not None else len(gen), tok_end]


def content_span(gen, raw, start_label, end_labels):
    """Token span of the CONTENT between `start_label` and the earliest `end_labels` marker
    (case-insensitive), EXCLUDING the labels themselves. Used so Phase-1 stage entropy covers
    only the reasoning/action tokens, never the trailing confidence label+number now emitted in
    the same generation. `start_label=""` means from char 0. Returns None if the range is empty.
    Note: 'action:' never matches inside 'action_confidence:' (no ':' right after ACTION there)."""
    low = raw.lower()
    start = 0
    if start_label:
        i = low.find(start_label.lower())
        if i >= 0:
            start = i + len(start_label)
    ends = [low.find(l.lower()) for l in end_labels]
    ends = [e for e in ends if e >= start]
    end = min(ends) if ends else len(raw)
    if end <= start:
        return None
    span = char_to_token_span(gen, start, end)
    return span if span[1] > span[0] else None


def action_span_char(completion_raw):
    """Char index where the action-regarding context begins (first 'ACTION:' label,
    case-insensitive). Returns len(completion) if no ACTION: label is present (whole thing
    is thought)."""
    low = completion_raw.lower()
    i = low.find("action:")
    return i if i >= 0 else len(completion_raw)
