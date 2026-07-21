"""Pure ReAct ALFWorld validation — pure-Python migration of ysymyth/ReAct's alfworld.ipynb.

Provenance: ysymyth/ReAct (MIT), alfworld.ipynb, HEAD 6bdb3a1. Cells 1-4 (env setup,
prompt load, alfworld_run, the 134-episode driver) are reproduced VERBATIM except for two
unavoidable API migrations, each semantically identical to the original:
  1. cell 0's llm() backend: davinci-002 (retired) -> Qwen served the standard vLLM way,
     queried with the standard OpenAI client. Same sampling params (greedy, max_tokens 100,
     stop=["\\n"]).
  2. cell 1's env access: alfworld dropped the direct `AlfredTWEnv` attribute for a
     get_environment(name) factory (resolves to the same class).
No probes, no retries, no project code. The ReAct control loop is untouched.

Run: serve a model first (see serve.sh), then `python react_alfworld.py`.
Requires alfworld + its data (ALFWORLD_DATA set) importable in the environment.
"""
import os
# Run from this file's directory so the verbatim relative paths ('base_config.yaml',
# './prompts/...') resolve regardless of the caller's cwd. (Only non-upstream line.)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===== cell 0 (SUBSTITUTED): llm() -> served Qwen via standard vLLM OpenAI client =====
from openai import OpenAI
_client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

def llm(prompt, stop=["\n"]):
    completion = _client.completions.create(
        model="qwen",
        prompt=prompt,
        temperature=0,
        max_tokens=100,
        top_p=1,
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

# ===== cell 1 (verbatim): env setup =====
import yaml
import alfworld
import alfworld.agents.environment
with open('base_config.yaml') as reader:
    config = yaml.safe_load(reader)

split = "eval_out_of_distribution"

# API-migration compat (like the llm() SDK swap): newer alfworld removed the direct
# `alfworld.agents.environment.AlfredTWEnv` attribute in favor of a get_environment(name)
# factory. Same class, same call, same semantics — env resolution only, loop untouched.
env = alfworld.agents.environment.get_environment(config["env"]["type"])(config, train_eval=split)
env = env.init_env(batch_size=1)

def process_ob(ob):
    if ob.startswith('You arrive at loc '):
        ob = ob[ob.find('. ')+2:]
    return ob

# ===== cell 2 (verbatim): load few-shot prompts =====
import json
folder = './prompts/'
prompt_file = 'alfworld_3prompts.json'
with open(folder + prompt_file, 'r') as f:
    d = json.load(f)

# ===== cell 3 (verbatim): the ReAct loop =====
import sys

def alfworld_run(prompt, to_print=True, ob=''):
    init_prompt = prompt + ob + '\n>'
    prompt = ''
    if to_print:
        print(ob)
        sys.stdout.flush()
    for i in range(1, 50):
        action = llm(init_prompt + prompt, stop=['\n']).strip()
        observation, reward, done, info = env.step([action])
        observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
        if action.startswith('think:'):
            observation = 'OK.'
        if to_print:
            print(f'Act {i}: {action}\nObs {i}: {observation}')
            sys.stdout.flush()
        prompt += f' {action}\n{observation}\n>'
        if done:
            return reward
    return 0

# ===== cell 4 (verbatim): 134-episode driver =====
prefixes = {
    'pick_and_place': 'put',
    'pick_clean_then_place': 'clean',
    'pick_heat_then_place': 'heat',
    'pick_cool_then_place': 'cool',
    'look_at_obj': 'examine',
    'pick_two_obj': 'puttwo'
}
cnts = [0] * 6
rs = [0] * 6

# Episode count: upstream default 134; a pilot sets REACT_N_EPISODES (e.g. 10) to smoke-test
# the structure. (Only other non-upstream line; the loop body below is verbatim.)
N_EPISODES = int(os.environ.get("REACT_N_EPISODES", "134"))
for _ in range(N_EPISODES):
    ob, info = env.reset()
    ob = '\n'.join(ob[0].split('\n\n')[1:])
    name = '/'.join(info['extra.gamefile'][0].split('/')[-3:-1])
    print(name)
    for i, (k, v) in enumerate(prefixes.items()):
        if name.startswith(k):
            prompt = 'Interact with a household to solve a task. Here are two examples.\n' + d[f'react_{v}_1'] + d[f'react_{v}_0'] + '\nHere is the task.\n'
            print(k, v)
            r = alfworld_run(prompt, ob=ob)
            rs[i] += r
            cnts[i] += 1
            break
    print(_+1, 'r', r, 'rs', rs, 'cnts', cnts, 'sum(rs)/sum(cnts)', sum(rs) / sum(cnts))
    print('------------\n')
