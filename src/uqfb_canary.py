"""Representative health check for a freshly served model.

A one-token curl against a 10-word prompt is NOT sufficient: on 2026-07-31 GPU1 passed exactly
that and then returned 'Out of range float values are not JSON compliant: nan' for every real
request. The failing calls differ in two ways that matter — LONG prompts (chunked prefill) and
CONCURRENCY — so the canary has to exercise both, using the real probe code path.

Exit 0 only if every probe returns usable Yes/No mass.
"""
import concurrent.futures as cf
import os
import sys

from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probes

BASE = os.environ.get("PROBE_BASE_URL", "http://localhost:8044/v1")
MODEL = os.environ.get("PROBE_MODEL", "qwen")
TOK = os.environ.get("PROBE_TOKENIZER", "qwen")
N = int(os.environ.get("CANARY_N", "12"))
MULT = int(os.environ.get("CANARY_MULT", "40"))

filler = ("You are in the middle of a room. Looking quickly around you, you see a cabinet 1, a "
          "countertop 1, a drawer 1, a fridge 1, a microwave 1, and a sinkbasin 1.\n"
          "> go to cabinet 1\nYou arrive at cabinet 1. The cabinet 1 is closed.\n"
          "> open cabinet 1\nYou open the cabinet 1. In it, you see a mug 1.\n") * MULT
PROMPT = ("You are evaluating an AI agent that is solving a task in an interactive environment.\n"
          "TASK DESCRIPTION:\nput a hot mug in the cabinet.\n"
          "ENVIRONMENT HISTORY:\n%s\nAVAILABLE COMMANDS:\ngo to cabinet 1\ntake mug 1 from cabinet 1\n"
          "AGENT REASONING:\nI should take the mug so I can heat it.\n"
          "PROPOSED ACTION:\ntake mug 1 from cabinet 1\n\n"
          "Is the proposed action above the correct and appropriate next action for this "
          "task?\nAnswer with a single word: Yes or No." % filler)

client = OpenAI(api_key="EMPTY", base_url=BASE)
cfg = probes.ProbeConfig(model=MODEL, tokenizer_path=TOK, base_url=BASE, temperature=0.0,
                         top_p=1.0, top_k=20, min_p=0.0, presence_penalty=0.0,
                         repetition_penalty=1.0, seed_base=9000)


def one(i):
    try:
        _c, rec = probes._call(client, cfg, PROMPT, max_tokens=4, seed=9000 + i)
        top = probes._first_nonws_top(rec["gen_logprobs"])
        _py, _pn, _cf2, U, ok = probes.yesno_mass(top)
        return (ok and U is not None), None if ok else "no yes/no mass"
    except Exception as e:
        return False, repr(e)[:120]


with cf.ThreadPoolExecutor(max_workers=N) as ex:
    res = list(ex.map(one, range(N)))
good = sum(1 for ok, _ in res if ok)
print("canary: %d/%d probes OK | concurrency=%d prompt=%d chars" % (good, N, N, len(PROMPT)))
for ok, err in res:
    if not ok:
        print("  failure:", err)
        break
sys.exit(0 if good == N else 1)
