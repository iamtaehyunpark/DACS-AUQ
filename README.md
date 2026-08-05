# react_validation — clean start, step 1: pure ReAct setup validation

## HotpotQA UQ data acquisition (decoupled + entangled)

The HotpotQA experiment harness now mirrors the completed ALFWorld acquisition system:

- `src/chat_react_hotpot.py` — decoupled two-call ReAct arm. It logs targeted
  `THOUGHT_TARGET`/`THOUGHT_CONFIDENCE`, action confidence, raw completions,
  post-template prompts, per-token logprobs with top-20 alternatives, thought/action
  spans, deterministic seeds, step bookkeeping, Hotpot τ, and EM/F1 episode outcomes.
- `src/chat_react_hotpot_entangled.py` — entangled one-call
  `THOUGHT`/`ACTION`/`CONFIDENCE` arm with the same environment, sampled questions,
  action/observation-only history, model settings, logging contract, and outcome records.
- `src/run_probes.py` — detects `domain=hotpotqa` and uses Hotpot-specific
  evidence/retrieval prompts. It retains the ALFWorld stage probes and adds exactly one
  whole-response P(True) record per step: `stage="response"`,
  `metric_field="U_R_ptrue"` (AGG-true).
- `src/judge_hotpot.py` — the same whole-trajectory three-judge acquisition protocol,
  using the Hotpot question and action/observation trajectory.

Run all six raw acquisition outputs in a fresh directory:

```bash
bash scripts/run_hotpot_acquisition.sh runs/hotpot_run_01 100
```

On the experiment server the runner sources
`/home/user/.config/azure_judge.env` (kept outside git, chmod 600), which must
export `AZURE_JUDGE_ENDPOINT` and `AZURE_JUDGE_KEY`. Override only the path with
`AZURE_JUDGE_ENV_FILE` when running on a differently configured host; credential
values are never copied into repository artifacts or logs.

The six JSONL artifacts are:

```text
uq_hotpot_decoupled.jsonl       probes_hotpot_decoupled.jsonl       judge_hotpot_decoupled.jsonl
uq_hotpot_entangled.jsonl       probes_hotpot_entangled.jsonl       judge_hotpot_entangled.jsonl
```

Both arms use the same shuffled question sample (`REACT_SEED`, default 233) and
task-derived per-call seeds. The pipeline refuses to append to existing artifacts and
runs `audit_hotpot.py` before any probe calls. HotpotQA still requires outbound access
to live Wikipedia.

The pure/not-instrumented migration described below remains as a historical baseline
validation track; it is not the UQ acquisition harness.

The original baseline track was isolated from the old `src/`: just the
**original** ReAct ALFWorld loop (ysymyth/ReAct, MIT) run against a Qwen model served the
**standard** vLLM way, with exactly one substitution: the `llm()` backend (davinci-002 is
retired). The loop, prompts, exemplars, `think:` convention, split, and 134-episode driver
are byte-for-byte upstream.

Goal: does pure ReAct + our served Qwen + ALFWorld run and behave sanely, before we build
anything on top? The success rate and the raw transcripts are the deliverable — not a fix.

## Run

```bash
# 1. serve Qwen (standard vLLM; substitute your checkpoint)
bash serve.sh                       # -> OpenAI-compatible server at http://localhost:8000

# 2a. FIRST: 10-episode pilot smoke test of the structure
bash run_pilot.sh                   # REACT_N_EPISODES=10, writes run_pilot.log

# 2b. full run (all 134 episodes)
bash run_validation.sh              # runs react_alfworld.py, writes run.log
```

Episode count is `REACT_N_EPISODES` (default 134); the pilot sets it to 10.

Requires: `vllm`, `openai`, and `alfworld` with its data (`ALFWORLD_DATA` set). No jupyter.

## Files (self-contained — no clone, no nbconvert)

- `react_alfworld.py` — pure-Python migration of upstream `alfworld.ipynb` (HEAD 6bdb3a1).
  Cells 1-4 (env, prompt load, `alfworld_run`, 134-episode driver) are VERBATIM; only
  cell 0's `llm()` is swapped to the served Qwen via the standard vLLM OpenAI client.
- `base_config.yaml`, `prompts/alfworld_3prompts.json` — vendored byte-identical from
  upstream (the data the loop reads).
- `serve.sh`, `run_validation.sh` — standard serve + run.
- `ReAct/` — pristine upstream clone (HEAD 6bdb3a1), reference-only, never edited,
  gitignored. The source of truth the migration was checked against.

## Report (write to REPORT.md here)

- upstream HEAD, served model string (`curl -s localhost:8000/v1/models`), sampling params;
- per-task-type success (`rs`/`cnts`) and total `sum(rs)/sum(cnts)`;
- total vs ReAct's published ALFWorld ~0.71 (davinci-002, unseen) — expect a different
  number with Qwen; the question is sane behavior, not matching 0.71;
- first 3 episode transcripts verbatim from `run.log`;
- plain grep tallies over `run.log`: empty-action count, "Nothing happens." count.

Stop after the report. No fixes — if it degenerates, that raw result is the finding.

---

## HotpotQA track (same discipline, second task)

`src/react_hotpotqa.py` is the pure-Python migration of upstream `hotpotqa.ipynb` (HEAD
6bdb3a1), done the **same way** as the ALFWorld one: cells reproduced VERBATIM, with only the
`llm()` backend swapped to the served Qwen (standard vLLM OpenAI client, same sampling) plus
one unavoidable fix (`import requests`, which the notebook's retry `step()` needs but never
imports). The `step()` retry helper, the `webthink()` loop, and the 500-episode driver are
byte-for-byte upstream (verified). Prompt strings match upstream to the byte.

Vendored byte-identical from upstream (the code + data the loop reads):
- `src/wikienv.py`, `src/wrappers.py` — the WikiEnv + HotPotQA/Logging wrappers.
- `src/prompts/prompts_naive.json` — the `webthink_simple6` exemplars.
- `src/data/hotpot_dev_v1_simplified.json` — the dev split (7405 questions; driver default).

```bash
bash scripts/serve.sh                 # same server as ALFWorld
bash scripts/run_hotpot_pilot.sh      # REACT_N_EPISODES=10 smoke test -> run_hotpot_pilot.log
bash scripts/run_hotpot_validation.sh # full run (500 episodes) -> run_hotpot.log
```

Knobs mirror the ALFWorld file (`REACT_TEMPERATURE`, `REACT_TOP_P`, `REACT_MAX_TOKENS`,
`REACT_N_EPISODES`, `REACT_SPLIT` default `dev`, `REACT_CAPTURE` wire-capture) — all default
to the upstream behavior, so the bare run is the pure replication.

**Important operational difference from ALFWorld:** HotpotQA's env hits **live Wikipedia**
(`en.wikipedia.org`) on every `search[]`. This run needs outbound internet in addition to the
served model, and requires `gym`, `beautifulsoup4`, `numpy`, `requests`. The published ReAct
HotpotQA number is EM ≈ 0.27–0.30 (davinci, dev); as with ALFWorld the question is sane
behavior with Qwen, not matching that.
