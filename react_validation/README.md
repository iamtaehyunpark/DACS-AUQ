# react_validation — clean start, step 1: pure ReAct setup validation

Isolated from the old `src/`. No project code, no configs, no serve scripts. Just the
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
