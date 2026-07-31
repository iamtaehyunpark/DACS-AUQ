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
import fcntl
import os
import threading
import time
from transformers import AutoTokenizer

_TOK = {}

# --- hosted-API mode (UQ_API_MODE=1) -------------------------------------------------
# For endpoints where the weights/tokenizer are not local (e.g. NVIDIA NIM DeepSeek):
#   * skip the local chat-template render (store the raw prompt as prompt_templated, which
#     is all run_probes.parse_task_history needs to recover TASK/HISTORY)
#   * drop vLLM-only sampling extras (top_k / min_p / repetition_penalty) the API rejects
#   * honour a per-process minimum call interval so N workers stay under an RPM quota
#     (set UQ_MIN_INTERVAL = N_workers * 60 / total_rpm).
_API_MODE = os.environ.get("UQ_API_MODE", "0") == "1"
_MIN_INTERVAL = float(os.environ.get("UQ_MIN_INTERVAL", "0"))
_MAX_RETRY = int(os.environ.get("UQ_MAX_RETRY", "10"))       # transient 429/503/504 retries
_BACKOFF_BASE = float(os.environ.get("UQ_BACKOFF_BASE", "3"))
_BACKOFF_CAP = float(os.environ.get("UQ_BACKOFF_CAP", "60"))
# Shared cross-process rate limit (calls/min across ALL workers). Preferred over the
# per-process UQ_MIN_INTERVAL, which cannot prevent fleet-wide bursts.
_RPM = float(os.environ.get("UQ_RPM", "0"))
_RATE_FILE = os.environ.get("UQ_RATE_FILE", "/tmp/uq_rate_slot.lock")
_rate_lock = threading.Lock()
_last_call = [0.0]


def _rate_limit_shared():
    """Cross-process token bucket: reserve the next evenly-spaced slot under a file lock.

    A per-process limiter cannot hold an RPM quota — N independent workers each spacing their
    own calls still burst when they happen to align, which is what produced 429s at only ~11
    calls/min average. Here every worker reserves a slot from ONE shared timeline, so the
    fleet emits a single stream spaced 60/RPM apart and can safely approach the quota.
    """
    if _RPM <= 0:
        return
    spacing = 60.0 / _RPM
    with open(_RATE_FILE, "a+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.seek(0)
            try:
                next_at = float((f.read() or "0").strip() or 0)
            except ValueError:
                next_at = 0.0
            now = time.time()
            slot = max(now, next_at)
            f.seek(0); f.truncate(); f.write("%.6f" % (slot + spacing)); f.flush()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    wait = slot - time.time()
    if wait > 0:
        time.sleep(wait)


def _rate_limit():
    if _RPM > 0:
        return _rate_limit_shared()
    if _MIN_INTERVAL <= 0:
        return
    with _rate_lock:
        wait = _MIN_INTERVAL - (time.monotonic() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()


def _tokenizer(path):
    if path not in _TOK:
        _TOK[path] = AutoTokenizer.from_pretrained(path)
    return _TOK[path]


def instrumented_chat(client, messages, *, model, tokenizer_path, temperature, top_p,
                      max_tokens, seed, top_k=20, min_p=0.0, presence_penalty=1.5,
                      repetition_penalty=1.0, enable_thinking=False):
    """Return (content, record). record holds the full ground truth for this call.

    enable_thinking=None omits the kwarg entirely (non-Qwen chat templates have no such switch).
    UQ_API_MODE=1 skips the local tokenizer and vLLM-only sampling extras (hosted endpoints)."""
    # chat-template kwarg: None -> omit entirely
    _tmpl_kw = {} if enable_thinking is None else {"enable_thinking": enable_thinking}

    if _API_MODE:
        # no local weights: store the raw prompt text (run_probes parses TASK/HISTORY from it)
        templated = "\n".join(m.get("content", "") for m in messages)
        prompt_ids = []
        extra = {"chat_template_kwargs": {"thinking": False}}
    else:
        tok = _tokenizer(tokenizer_path)
        templated = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                            **_tmpl_kw)
        prompt_ids = tok(templated, add_special_tokens=False)["input_ids"]
        extra = {"chat_template_kwargs": _tmpl_kw,
                 "top_k": top_k, "min_p": min_p, "repetition_penalty": repetition_penalty}

    t0 = time.monotonic()
    _kw = dict(model=model, messages=messages, temperature=temperature, top_p=top_p,
               max_tokens=max_tokens, seed=seed, logprobs=True, top_logprobs=20,
               extra_body=extra)
    if not _API_MODE:                      # hosted APIs commonly reject presence_penalty
        _kw["presence_penalty"] = presence_penalty

    # Hosted endpoints return transient 429 (our quota) and 503 ResourceExhausted (their
    # capacity). Neither should kill a multi-hour run — retry with exponential backoff.
    r = None
    for attempt in range(_MAX_RETRY):
        try:
            # Pace EVERY attempt, not just the first: a retry is another billable request that
            # counts against the quota. Pacing only first attempts let a 14-retry call fire 14
            # unpaced requests, which turned one 429 into a burst and then a death spiral.
            _rate_limit()
            r = client.chat.completions.create(**_kw)
            break
        except Exception as e:
            s = str(e)
            # gateway/capacity/transport failures — all retryable. Match on the numeric codes
            # too: an OpenAI SDK 504 stringifies as "Error code: 504" with no "timeout" text.
            # Match on the exception CLASS as well as the message: openai.APITimeoutError
            # stringifies as "Request timed out." — no "timeout" substring — which previously
            # slipped through and killed workers mid-run.
            cls = type(e).__name__
            transient = (
                cls in ("APITimeoutError", "APIConnectionError", "RateLimitError",
                        "InternalServerError", "APIStatusError", "APIError")
                or any(k in s for k in (
                    "429", "500", "502", "503", "504",
                    "ResourceExhausted", "Too Many Requests", "Service Unavailable",
                    "Gateway", "timeout", "Timeout", "timed out", "Connection"))
            )
            if not transient or attempt == _MAX_RETRY - 1:
                raise
            back = min(_BACKOFF_CAP, (2 ** attempt) * _BACKOFF_BASE) * (1.0 + 0.3 * ((attempt * 7919) % 100) / 100.0)
            time.sleep(back)
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
