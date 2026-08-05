#!/usr/bin/env python3
"""Recompute thought/action token spans in an existing uq log, in place, without regenerating.

Why this exists
---------------
char_to_token_span assumed decoded token strings concatenate back into the completion
text. SentencePiece tokenizers return them with the space marker stripped, so len(token)
undercounts by one per word, the running position lags, and every boundary lands too far
right — worse the deeper into the text it sits. Mistral-7B: thought span ran past ACTION:
on 100% of calls in both environments, and ~46% of action spans pointed at the trailing
confidence number. phi4mini and gemma4b are clean at the same code path.

Spans are DERIVED data. gen_logprobs (ordered token strings) and completion_raw are both
logged, so the correct spans can be recomputed offline. Nothing needs regenerating — which
matters, because logprobs and in-generation confidence are the only unrecoverable fields
and both are intact.

What is NOT touched: completion_raw, gen_logprobs, thought_text, action_parsed, and every
other field. Only `spans` is rewritten, and only on `kind == "call"` records. Executed
actions came from a text parse of completion_raw and were never affected.

Usage:
  backfill_spans.py <uq.jsonl> [more.jsonl ...]      rewrite in place (.bak kept)
  backfill_spans.py --check <uq.jsonl> [...]         report only, change nothing
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

SPECIALS = ("</s>", "<s>", "<|endoftext|>", "<|eot_id|>", "<end_of_turn>", "<|im_end|>")


def visible(token):
    for marker in SPECIALS:
        token = token.replace(marker, "")
    return "".join(token.split())


def char_to_token_span(gen, start_char, end_char, raw):
    """Whitespace-insensitive char->token mapping. Mirrors the fixed uqlog.char_to_token_span;
    duplicated here so the backfill does not depend on importing the agent stack."""
    if not gen:
        return [0, 0]
    widths = [len(visible(g["token"])) for g in gen]
    nws = lambda s: len("".join(s.split()))
    lo_bound, hi_bound = nws(raw[:start_char]), nws(raw[:end_char])
    pos, tok_start, tok_end = 0, None, 0
    for idx, width in enumerate(widths):
        lo, hi = pos, pos + width
        if tok_start is None and hi > lo_bound:
            tok_start = idx
        if lo < hi_bound:
            tok_end = idx + 1
        pos = hi
    return [tok_start if tok_start is not None else len(gen), tok_end]


def content_span(gen, raw, start_label, end_labels):
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
    span = char_to_token_span(gen, start, end, raw)
    return span if span[1] > span[0] else None


def misaligned(gen, span, stage):
    """The two structural failures the audit names, checked on the joined token text.

    Indices are clamped: a span recorded before the fix can run past the end of gen, and
    this must diagnose such a record rather than crash on it."""
    if not span:
        return None
    lo = max(0, min(span[0], len(gen)))
    hi = max(lo, min(span[1], len(gen)))
    flat = "".join(visible(gen[i]["token"]) for i in range(lo, hi)).upper()
    if stage == "thought" and "ACTION" in flat:
        return "thought_swallows_action"
    if stage == "action" and ("CONFIDENCE" in flat or flat.startswith(":0.")):
        return "action_is_confidence"
    return None


def process(path, check_only):
    stats = {"calls": 0, "rewritten": 0, "no_markers": 0,
             "bad_before": 0, "bad_after": 0, "spans_gained": 0, "spans_lost": 0}
    out_lines = []
    for line in open(path):
        rec = json.loads(line)
        if rec.get("kind") != "call":
            out_lines.append(line)
            continue
        stats["calls"] += 1
        gen = rec.get("gen_logprobs") or []
        raw = rec.get("completion_raw") or ""
        old = rec.get("spans") or {}

        for stage in ("thought", "action"):
            if misaligned(gen, old.get(stage), stage):
                stats["bad_before"] += 1

        # Only rewrite entangled-style calls, where both markers are present. A thought-only
        # or action-only call from the decoupled harness has a different span contract and
        # must be left alone.
        low = raw.lower()
        if "thought:" not in low or "action:" not in low:
            stats["no_markers"] += 1
            out_lines.append(line)
            continue

        new = {
            "thought": content_span(gen, raw, "thought:", ["action:"]),
            "action": content_span(gen, raw, "action:", ["confidence:", "action_confidence:"]),
        }
        for stage in ("thought", "action"):
            if misaligned(gen, new.get(stage), stage):
                stats["bad_after"] += 1
            if old.get(stage) is None and new.get(stage) is not None:
                stats["spans_gained"] += 1
            if old.get(stage) is not None and new.get(stage) is None:
                stats["spans_lost"] += 1

        if new != old:
            stats["rewritten"] += 1
            rec["spans"] = new
        out_lines.append(json.dumps(rec) + "\n")

    print("%s" % path)
    print("  calls=%(calls)d  rewritten=%(rewritten)d  no-markers(skipped)=%(no_markers)d" % stats)
    print("  misaligned spans: before=%(bad_before)d  after=%(bad_after)d" % stats)
    print("  spans gained=%(spans_gained)d  lost=%(spans_lost)d" % stats)

    if check_only:
        print("  (check only, file unchanged)")
        return stats
    if stats["bad_after"] > stats["bad_before"]:
        print("  REFUSING to write: the rewrite made things worse", file=sys.stderr)
        return stats
    backup = path + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
        print("  backup -> %s" % backup)
    tmp = path + ".tmp"
    with open(tmp, "w") as fo:
        fo.writelines(out_lines)
    os.replace(tmp, path)
    print("  written")
    return stats


def main():
    args = sys.argv[1:]
    check_only = "--check" in args
    paths = [a for a in args if a != "--check"]
    if not paths:
        sys.exit(__doc__)
    for p in paths:
        if not os.path.exists(p):
            print("missing: %s" % p, file=sys.stderr)
            continue
        process(p, check_only)


if __name__ == "__main__":
    main()
