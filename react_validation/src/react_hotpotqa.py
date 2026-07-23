"""Pure ReAct HotpotQA validation — pure-Python migration of ysymyth/ReAct's hotpotqa.ipynb.

Provenance: ysymyth/ReAct (MIT), hotpotqa.ipynb, HEAD 6bdb3a1. The notebook's code cells
(llm, WikiEnv/wrappers setup + retrying step(), webthink() loop, the 500-episode driver) are
reproduced VERBATIM except for two unavoidable migrations, each semantically identical to the
original:
  1. the llm() backend: davinci-002 (retired) -> Qwen served the standard vLLM way, queried
     with the standard OpenAI client. Same sampling params (greedy, max_tokens 100). The
     per-call `stop` sequences the webthink loop passes are untouched.
  2. `import requests` is added at module top. The notebook's step() catches
     requests.exceptions.Timeout but the notebook never imports requests in a code cell (it is
     a transitive import of wikienv only), so upstream would NameError on the first timeout.
     The added import is a no-op on the happy path and only makes the existing retry work.
No probes, no retries beyond upstream's own, no project code. The ReAct control loop is untouched.

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
_MAXTOK = int(os.environ.get("REACT_MAX_TOKENS", "100"))

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

# ===== cell 4 (verbatim): load prompts + the webthink() loop =====
import json
import sys

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
        thought_action = llm(prompt + f"Thought {i}:", stop=[f"\nObservation {i}:"])
        try:
            thought, action = thought_action.strip().split(f"\nAction {i}: ")
        except:
            print('ohh...', thought_action)
            n_badcalls += 1
            n_calls += 1
            thought = thought_action.strip().split('\n')[0]
            action = llm(prompt + f"Thought {i}: {thought}\nAction {i}:", stop=[f"\n"]).strip()
        obs, r, done, info = step(env, action[0].lower() + action[1:])
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

# ===== cell 5 (verbatim): 500-episode driver =====
import random
import time
idxs = list(range(7405))
random.Random(233).shuffle(idxs)

# Episode count: upstream default 500; a pilot sets REACT_N_EPISODES (e.g. 10) to smoke-test
# the structure. (Only non-upstream line; the loop body below is verbatim.)
N_EPISODES = int(os.environ.get("REACT_N_EPISODES", "500"))

rs = []
infos = []
old_time = time.time()
for i in idxs[:N_EPISODES]:
    r, info = webthink(i, to_print=True)
    rs.append(info['em'])
    infos.append(info)
    print(sum(rs), len(rs), sum(rs) / len(rs), (time.time() - old_time) / len(rs))
    print('-----------')
    print()
