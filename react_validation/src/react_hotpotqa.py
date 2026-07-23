"""Pure ReAct HotpotQA validation — pure-Python migration of ysymyth/ReAct's hotpotqa.ipynb.

Provenance: ysymyth/ReAct (MIT), hotpotqa.ipynb, HEAD 6bdb3a1. The notebook's code cells
(llm, WikiEnv/wrappers setup + retrying step(), webthink() loop, the 500-episode driver) are
reproduced VERBATIM except for three unavoidable current-timeline migrations, each
semantically identical to the original:
  1. the llm() backend: davinci-002 (retired) -> Qwen served the standard vLLM way, queried
     with the standard OpenAI client. Same sampling params (greedy, max_tokens 100). The
     per-call `stop` sequences the webthink loop passes are untouched.
  2. `import requests` is added at module top. The notebook's step() catches
     requests.exceptions.Timeout but the notebook never imports requests in a code cell (it is
     a transitive import of wikienv only), so upstream would NameError on the first timeout.
     The added import is a no-op on the happy path and only makes the existing retry work.
  3. a default User-Agent is installed on wikienv's requests.get (see cell 2). Wikipedia now
     returns HTTP 403 to header-less requests, which the pristine loop sends, so it would 403
     on the first search[]. The fetched page is exactly what upstream intended.
No probes, no retries beyond upstream's own, no project code. The ReAct control loop is untouched.

Generation mode (REACT_NO_STOP): the loop has two paths. Default OFF reproduces upstream's
stop-regulated webthink byte-for-byte (fidelity fallback). REACT_NO_STOP=1 is "our modified
react" — the mode this project actually runs, matching chat_react.py's philosophy: generation is
UNRESTRICTED (no stop; the model may emit <think>...</think> and anything else) and the harness's
only job is to parse the labeled `Action i:` out of the whole turn. This is the same treatment as
react_alfworld.py's REACT_NO_STOP. Upstream's stop=["\n"] is never used in this mode; it also
removes the latent empty-action IndexError (an empty action becomes a graceful no-op).

wikienv.py, wrappers.py, prompts/prompts_naive.json and data/hotpot_dev_v1_simplified.json are
vendored byte-identical from upstream (the code + data the loop reads).

NOTE: unlike ALFWorld (fully local), HotpotQA's env hits LIVE Wikipedia
(https://en.wikipedia.org) on every search[] — this validation needs outbound internet in
addition to the served model.

Run: serve a model first (see serve.sh), then `python react_hotpotqa.py`.
Requires: openai, gym, beautifulsoup4, numpy, requests (and outbound access to Wikipedia).
"""
import os
import requests  # migration fix (see docstring #2): upstream step() needs it on timeout.
# Run from this file's directory so the verbatim relative paths ('./prompts/...', the vendored
# 'data/...' read by wrappers.py) resolve regardless of the caller's cwd. (Non-upstream line.)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===== cell 1 (SUBSTITUTED): llm() -> served Qwen via standard vLLM OpenAI client =====
from openai import OpenAI
_client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

# Sampling is configurable; defaults reproduce ReAct's greedy decoding (temperature=0,
# top_p=1). REACT_TEMPERATURE / REACT_TOP_P override it.
_TEMP = float(os.environ.get("REACT_TEMPERATURE", "0"))
_TOP_P = float(os.environ.get("REACT_TOP_P", "1"))

# Modified-react generation (gated, like react_alfworld.py's REACT_NO_STOP): when set, the loop
# passes NO stop sequence, so the model emits its WHOLE free-form turn with no regulation —
# including any <think>...</think> block and extra text — and the action is parsed OFFLINE by the
# harness (see webthink). This is "our modified react": generation is unrestricted; the harness's
# only rule is to locate the labeled `Action i:` (</think> is peeled first as a wrapper, not a
# restriction). It is the intended run mode — original ReAct's stop=["\n"] is a fidelity-only
# fallback (default OFF) that this project does not use. max_tokens is raised so the whole turn
# (reasoning + the Action line) isn't truncated before the label appears.
_NO_STOP = bool(os.environ.get("REACT_NO_STOP"))
_MAXTOK = int(os.environ.get("REACT_MAX_TOKENS", "512" if _NO_STOP else "100"))

def llm(prompt, stop=["\n"]):
    completion = _client.completions.create(
        model="qwen",
        prompt=prompt,
        temperature=_TEMP,
        max_tokens=_MAXTOK,
        top_p=_TOP_P,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=stop,
    )
    text = completion.choices[0].text
    # Gated wire-capture (default OFF; observability only, return value unchanged): when
    # REACT_CAPTURE is set, append the EXACT prompt sent and the EXACT raw completion
    # (pre-strip) plus finish_reason as one JSONL record.
    _cap = os.environ.get("REACT_CAPTURE")
    if _cap:
        import json as _json
        with open(_cap, "a") as _f:
            _f.write(_json.dumps({
                "prompt": prompt,
                "response_raw": text,
                "finish_reason": completion.choices[0].finish_reason,
                "usage_completion_tokens": getattr(completion.usage, "completion_tokens", None),
            }) + "\n")
    return text

# ===== cell 2 (verbatim): WikiEnv + wrappers, and the retrying step() =====
import wikienv, wrappers

# Migration fix #3 (current-timeline adaptation, semantically identical to upstream): since
# upstream was written (2022) Wikipedia tightened its policy and now returns HTTP 403 to any
# request with no User-Agent. wikienv.search_step() does `requests.get(url).text` with no
# header, so the pristine loop 403s on the FIRST search[]. We install a default descriptive
# User-Agent on wikienv's requests.get — the page fetched is exactly what upstream intended.
# Vendored wikienv.py stays byte-identical; the adaptation lives only here, like the llm swap.
# Override via REACT_WIKI_UA.
_WIKI_UA = os.environ.get(
    "REACT_WIKI_UA",
    "ReAct-validation/1.0 (research reproduction; https://github.com/ysymyth/ReAct)",
)
_orig_requests_get = wikienv.requests.get
def _requests_get_with_ua(url, **kwargs):
    headers = dict(kwargs.pop("headers", None) or {})
    headers.setdefault("User-Agent", _WIKI_UA)
    return _orig_requests_get(url, headers=headers, **kwargs)
wikienv.requests.get = _requests_get_with_ua

# Split is selectable via REACT_SPLIT (default = upstream's "dev"); the pure replication is
# unchanged. (Only non-upstream token in this cell besides the env lookup.)
_SPLIT = os.environ.get("REACT_SPLIT", "dev")
env = wikienv.WikiEnv()
env = wrappers.HotPotQAWrapper(env, split=_SPLIT)
env = wrappers.LoggingWrapper(env)

def step(env, action):
    attempts = 0
    while attempts < 10:
        try:
            return env.step(action)
        except requests.exceptions.Timeout:
            attempts += 1

# ===== cell 4 (verbatim upstream, + gated modified-react parse): prompts + the webthink() loop =====
import json
import re
import sys

def strip_think(t):
    """Peel a leading <think>...</think> wrapper (a wrapper to remove, NOT a content restriction).
    Same helper as chat_react.py / react_alfworld.py's _parse_action."""
    return t.split("</think>", 1)[-1] if "</think>" in t else t

def _parse_thought_action(raw, i):
    """Modified-react parse (REACT_NO_STOP): the model may emit ANYTHING — a <think>...</think>
    block, extra prose, even a hallucinated Observation/next-Thought continuation. The harness's
    ONLY rule is to locate the labeled `Action {i}:` and take its line; the thought is whatever
    precedes it. Returns (thought, action, found_label). action='' if the label is absent."""
    t = strip_think(raw)
    m = re.search(r"(?:^|\n)Action %d:[ \t]*" % i, t)
    if m:
        thought = t[:m.start()].strip()
        action = t[m.end():].lstrip().split("\n", 1)[0].strip()
        return thought, action, True
    return t.strip(), "", False

folder = './prompts/'
prompt_file = 'prompts_naive.json'
with open(folder + prompt_file, 'r') as f:
    prompt_dict = json.load(f)

webthink_examples = prompt_dict['webthink_simple6']
instruction = """Solve a question answering task with interleaving Thought, Action, Observation steps. Thought can reason about the current situation, and Action can be three types: 
(1) Search[entity], which searches the exact entity on Wikipedia and returns the first paragraph if it exists. If not, it will return some similar entities to search.
(2) Lookup[keyword], which returns the next sentence containing keyword in the current passage.
(3) Finish[answer], which returns the answer and finishes the task.
Here are some examples.
"""
webthink_prompt = instruction + webthink_examples

def webthink(idx=None, prompt=webthink_prompt, to_print=True):
    question = env.reset(idx=idx)
    if to_print:
        print(idx, question)
    prompt += question + "\n"
    n_calls, n_badcalls = 0, 0
    for i in range(1, 8):
        n_calls += 1
        if _NO_STOP:
            # modified react: NO stop — the model emits its whole free-form turn (incl <think>...
            # </think> and any continuation); the harness parses the labeled Action offline.
            raw = llm(prompt + f"Thought {i}:", stop=None)
            thought, action, found = _parse_thought_action(raw, i)
            if not found:
                # no `Action i:` label surfaced within the turn — one recovery call, still no stop.
                print('ohh...', raw)
                n_badcalls += 1
                n_calls += 1
                thought = thought.split('\n')[0] if thought else thought
                raw2 = llm(prompt + f"Thought {i}: {thought}\nAction {i}:", stop=None)
                action = strip_think(raw2).lstrip().split('\n', 1)[0].strip()
        else:
            # original ReAct (fidelity-only fallback, uses stop=["\n"]) — byte-for-byte upstream.
            thought_action = llm(prompt + f"Thought {i}:", stop=[f"\nObservation {i}:"])
            try:
                thought, action = thought_action.strip().split(f"\nAction {i}: ")
            except:
                print('ohh...', thought_action)
                n_badcalls += 1
                n_calls += 1
                thought = thought_action.strip().split('\n')[0]
                action = llm(prompt + f"Thought {i}: {thought}\nAction {i}:", stop=[f"\n"]).strip()
        # guard the empty action so the modified harness never crashes on action[0] (upstream's
        # latent IndexError); an empty action becomes a no-op the env reports as "Invalid action:".
        env_action = (action[0].lower() + action[1:]) if action else action
        obs, r, done, info = step(env, env_action)
        obs = obs.replace('\\n', '')
        step_str = f"Thought {i}: {thought}\nAction {i}: {action}\nObservation {i}: {obs}\n"
        prompt += step_str
        if to_print:
            print(step_str)
        if done:
            break
    if not done:
        obs, r, done, info = step(env, "finish[]")
    if to_print:
        print(info, '\n')
    info.update({'n_calls': n_calls, 'n_badcalls': n_badcalls, 'traj': prompt})
    return r, info

# ===== cell 5 (verbatim upstream + gated sampling/sharding knobs): the episode driver =====
import random
import time

# Sampling: upstream shuffles range(7405) with a FIXED seed (233) and takes the first N. Both are
# gated env knobs that DEFAULT to the exact upstream values, so the bare run is byte-for-byte:
#   REACT_SEED       — shuffle seed. 233 reproduces upstream; a fresh/random seed draws a random
#                      subset of the dataset instead of the same fixed one.
#   REACT_N_EPISODES — sample size (upstream 500; a pilot uses 10).
# Parallelism: REACT_NUM_WORKERS / REACT_WORKER_ID stride-shard the SAME drawn sample across
# processes (disjoint shards whose union is the full sample), so N workers hit the shared vLLM
# server concurrently for an ~Nx speedup. Defaults (1 worker, id 0) => the whole sample, in order.
_SEED = int(os.environ.get("REACT_SEED", "233"))
N_EPISODES = int(os.environ.get("REACT_N_EPISODES", "500"))
_NW = int(os.environ.get("REACT_NUM_WORKERS", "1"))
_WID = int(os.environ.get("REACT_WORKER_ID", "0"))

idxs = list(range(7405))
random.Random(_SEED).shuffle(idxs)
sample = idxs[:N_EPISODES]
run_idxs = sample[_WID::_NW]   # this worker's disjoint shard (strided)
print("WORKER %d/%d | seed=%d | sample=%d | this_shard=%d episodes" % (_WID, _NW, _SEED, len(sample), len(run_idxs)))
sys.stdout.flush()

rs = []
infos = []
n_overflow = 0   # episodes ended early by context-length overflow (counted as fails)
n_errored = 0    # episodes ended by any other transient error (counted as fails)
old_time = time.time()

def _is_overflow(e):
    s = str(e).lower()
    return "context length" in s or "context_length" in s or "maximum context" in s

for i in run_idxs:
    # Driver-level resilience for the long unattended full run (webthink + parser untouched):
    # a per-episode context-overflow or transient network hiccup is logged and counted as a
    # fail, never aborting the remaining episodes. All skips are tallied in the final summary.
    try:
        r, info = webthink(i, to_print=True)
        em = info['em']
        infos.append(info)
    except Exception as e:
        if _is_overflow(e):
            n_overflow += 1
            print('[episode idx %d] CONTEXT OVERFLOW — counting as fail, continuing' % i)
        else:
            n_errored += 1
            print('[episode idx %d] EPISODE ERROR (%s) — counting as fail, continuing' % (i, repr(e)[:200]))
        sys.stdout.flush()
        em = 0
    rs.append(em)
    print(sum(rs), len(rs), sum(rs) / len(rs), (time.time() - old_time) / len(rs))
    print('-----------')
    print()

print('FINAL[w%d/%d seed=%d]: EM %d/%d = %.4f | overflow-skipped %d | error-skipped %d'
      % (_WID, _NW, _SEED, sum(rs), len(rs), (sum(rs) / len(rs)) if rs else 0.0, n_overflow, n_errored))
