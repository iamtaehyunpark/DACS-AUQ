"""Feasibility test for DeepSeek-V4-Flash via NVIDIA NIM, for the ALFWorld UQ harness.

The harness needs more than text: token logprobs + top-k alternatives drive MTE/MaxTE/PPL/SP
and the P(True) probe (first generated token's top-20 mass over Yes/No). If the endpoint
cannot return logprobs, most of the metric roster is unavailable.

Checks, in order of importance:
  1. basic chat completion works
  2. logprobs=True accepted, and logprobs actually returned
  3. top_logprobs=20 accepted (needed for entropy + P(True))
  4. format-native label compliance (THOUGHT_TARGET / ACTION_CONFIDENCE)
  5. seed support (A13 per-step seeding) and latency
"""
import os, sys, time, json
from openai import OpenAI

KEY = os.environ.get("NVIDIA_API_KEY", "")
if not KEY:
    sys.exit("NVIDIA_API_KEY not set")
MODEL = os.environ.get("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-flash")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=KEY)

def hdr(s): print("\n" + "=" * 60 + "\n" + s + "\n" + "=" * 60)

# ---- 1. basic call ----
hdr("1. basic completion")
try:
    t0 = time.time()
    r = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        temperature=0, max_tokens=16)
    print("  OK  content=%r  latency=%.1fs" % (r.choices[0].message.content, time.time() - t0))
    print("  usage:", r.usage)
except Exception as e:
    print("  FAILED:", repr(e)[:400]); sys.exit(1)

# ---- 2/3. logprobs ----
hdr("2/3. logprobs + top_logprobs (CRITICAL)")
for tk in (20, 5, 1):
    try:
        r = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": "Answer Yes or No: is 2+2=4?"}],
            temperature=0, max_tokens=8, logprobs=True, top_logprobs=tk)
        lp = r.choices[0].logprobs
        if lp and getattr(lp, "content", None):
            t = lp.content[0]
            print("  top_logprobs=%d ACCEPTED — first token=%r logprob=%.4f, %d alternatives"
                  % (tk, t.token, t.logprob, len(t.top_logprobs or [])))
            break
        else:
            print("  top_logprobs=%d accepted but logprobs field EMPTY" % tk)
    except Exception as e:
        print("  top_logprobs=%d rejected: %s" % (tk, repr(e)[:200]))
else:
    print("  >>> NO LOGPROBS AVAILABLE — token-entropy metrics and P(True) impossible")

# ---- 4. format-native compliance ----
hdr("4. format-native label compliance")
prompt = """You are an AI agent solving a task in an interactive environment.
TASK DESCRIPTION:
put a clean mug on the desk
ENVIRONMENT HISTORY:
You are in the middle of a room. Looking quickly around you, you see a desk 1, a drawer 1, and a sinkbasin 1.
Think about the current situation, then respond in EXACTLY this format, each label on its own line:
THOUGHT: your step-by-step reasoning about what to do next
THOUGHT_TARGET: the single factual claim your next decision depends on
THOUGHT_CONFIDENCE: a number from 0.00 to 1.00 that the claim is true
"""
try:
    t0 = time.time()
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}],
                                       temperature=0.7, top_p=0.8, max_tokens=512)
    c = r.choices[0].message.content or ""
    rsn = getattr(r.choices[0].message, "reasoning_content", None)
    print("  latency=%.1fs  completion_tokens=%s" % (time.time() - t0, r.usage.completion_tokens))
    print("  has separate reasoning channel:", bool(rsn))
    for lab in ("THOUGHT:", "THOUGHT_TARGET:", "THOUGHT_CONFIDENCE:"):
        print("   %-20s %s" % (lab, "FOUND" if lab in c.upper() else "MISSING"))
    print("  --- first 400 chars ---\n", c[:400])
except Exception as e:
    print("  FAILED:", repr(e)[:300])

# ---- 5. seed support ----
hdr("5. seed support (A13 per-step seeding)")
try:
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": "hi"}],
                                       temperature=0.7, max_tokens=8, seed=1234)
    print("  seed ACCEPTED")
except Exception as e:
    print("  seed rejected:", repr(e)[:200])
