#!/usr/bin/env python3
"""Empirical anatomy of the empty-action collapse. Read-only."""
import json, statistics
from collections import Counter

recs = [json.loads(l) for l in open("data/trajectories/e1_primary_decoupled.jsonl")]
coll = Counter(); lps = []; multi = 0; thought_empty = 0; empties = 0
first_tok_reason = Counter()
for d in recs:
    ex = d.get("extra") or {}
    ag = ex.get("action_generation")
    au = ex.get("action_stage_audit") or {}
    toks = au.get("tokens") or []; lp = au.get("logprobs") or []
    gr = (ex.get("generation_retry") or {}).get("action") or {}
    if not (ex.get("thought_generation") or "").strip():
        thought_empty += 1
    if (ag or "") == "":
        empties += 1
        if toks:
            coll[toks[0]] += 1
            if len(toks) > 1: multi += 1
            if lp: lps.append(lp[0])
        first_tok_reason[gr.get("first_finish_reason")] += 1

print("total steps:", len(recs))
print("EMPTY action steps:", empties)
print("collapse first-token counts:", coll.most_common(8))
print("empties whose audit has >1 token:", multi)
print("empties by first_finish_reason:", dict(first_tok_reason))
if lps:
    print("collapse-token logprob: n=%d mean=%.2f median=%.2f min=%.2f max=%.2f"
          % (len(lps), statistics.mean(lps), statistics.median(lps), min(lps), max(lps)))
    buck = Counter(round(x) for x in lps)
    print("logprob histogram (rounded):", sorted(buck.items()))
    # convert mean logprob to probability
    import math
    print("implied P(collapse token) at median logprob: %.3f" % math.exp(statistics.median(lps)))
print("THOUGHT-stage empty generations:", thought_empty, "/", len(recs))
