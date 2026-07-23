# Hotpot report — pure→modified ReAct, 100 random dev questions (first full validation)

**Setup.** Pure-Python migration of ysymyth/ReAct's `hotpotqa.ipynb` (HEAD 6bdb3a1),
`src/react_hotpotqa.py`. The notebook cells (llm, WikiEnv/wrappers + retrying `step()`,
`webthink()`, driver) are reproduced verbatim; `wikienv.py`, `wrappers.py`,
`prompts/prompts_naive.json`, `data/hotpot_dev_v1_simplified.json` are vendored byte-identical.
Three current-timeline migrations, each documented and semantically upstream: (1) `llm()`
davinci-002 → served Qwen; (2) `import requests` (the notebook's retry `step()` needs it but
never imports it); (3) a default `User-Agent` on `wikienv.requests.get` (Wikipedia now returns
**403** to header-less requests, so the pristine loop would 403 on the first `search[]`).

Agent = **Qwen3.6-35B-A3B** served single-GPU via vLLM (`--served-model-name qwen`,
max_model_len 16384). Env = `reflexion` conda env (gym 0.26.2, openai 1.86, bs4, numpy 2.0.1).
Unlike ALFWorld (fully local), HotpotQA hits **live Wikipedia** on every `search[]`.
Split = dev. Generation mode = **`REACT_NO_STOP=1`** (see below). Commit da8604c.

**Sample = 100 RANDOM dev questions** (not upstream's fixed seed-233 set): `REACT_SEED=395786003`,
drawn fresh, recorded on the server (`src/.last_parallel_seed`) so it is reproducible. Run as
**4 parallel workers** stride-sharding the sample (25 each, disjoint, union = the 100) against the
shared vLLM server — ~22 min wall-clock vs. ~45 min sequential.

## Headline

- **Ran end-to-end, 0 crashes, 0 overflow-skips, 0 error-skips.** The full harness — random
  sampling, worker sharding, live-Wikipedia search, the modified-react parse, the merge — works.
- **EM 21/100 = 0.21.** Per worker: 4/25 (.16), 8/25 (.32), 2/25 (.08), 7/25 (.28) — the
  0.08–0.32 spread is the variance expected at n=25 each.
- Modestly **below ReAct's published davinci HotpotQA (~0.27–0.30, dev)** and well below the
  10-episode smoke test's 0.40 (which drew easy examine-style questions — small-sample optimism).
  For pure 6-shot ReAct with only `search`/`lookup` and a 7-step budget on Qwen3.6, 0.21 is a
  sane number; the question was sane behavior, not matching 0.27.

## The modified-react generation mode (why not original ReAct)

The original notebook regulates generation with `stop=["\nObservation i:"]` and, in its badcall
recovery, `stop=["\n"]`. Against Qwen3.6 that path **crashed**: on the completions endpoint the
`enable_thinking=False` chat-template flag cannot apply, so the model prepends an empty
`<think>\n\n</think>` marker; its leading newline + `stop=["\n"]` truncates the recovery action to
`""`, and upstream's verbatim `action[0]` then raises `IndexError` (killed the first run at ep 8).

The project's modified react (matching `chat_react.py` / `react_alfworld.py`'s `REACT_NO_STOP`)
fixes this by principle, not patch: **generation is unrestricted** — no stop, the model may emit
`<think>…</think>` and anything else — and **the harness's only job is to parse the labeled
`Action i:` out of the whole turn** (`</think>` is peeled as a wrapper, not a restriction). This
is the mode run here; the original stop-regulated loop remains as a default-OFF fidelity fallback.

## Behavioral findings (n=100)

- **Format is no longer the failure mode.** Main-path parsing is clean — the plumbing/degeneration
  pathologies of the earlier decoupled attempt do not appear. Failures are reasoning depth,
  step-budget exhaustion, and the recovery weakness below — not the loop.
- **Badcalls: 130** (the `webthink` "no `Action i:` label surfaced" path), all recovered without
  crashing. That the recovery fires at all is Qwen3.6 sometimes not emitting the exact `Action i:`
  label within the turn.
- **Recovery-parse weakness — the one actionable finding: 34 bare `<think>` actions.** On a badcall
  recovery the model occasionally opens a `<think>` block that it does not close within the
  512-token window; `strip_think` peels only *closed* blocks, so the first line "`<think>`" becomes
  the action. The env rejects each as `Invalid action: <think>` — a **graceful no-op, never a
  crash** — but it wastes one of the 7 steps. 34 such rejections across the run (of 109 total
  invalid-action observations; the other 75 are ordinary wrong/ineffective commands). Hardening the
  recovery parse to skip a lone/unclosed `<think>` line (or retry) would recover those steps and
  likely lift EM a little.

## What this means

The migration and the modified-react harness are validated at scale on a random sample: it runs
clean, produces a trustworthy EM, and the only harness-attributable loss (the 34 `<think>`
recovery no-ops) degrades gracefully and is a known, small, fixable parse gap — not a silent
corruption. 0.21 is the honest baseline for this model × pure ReAct × live Wikipedia.

## Reproducibility & artifacts

- Sample: `REACT_SEED=395786003`, `REACT_N_EPISODES=100`, dev split. Re-draw/re-run with
  `REACT_SEED=395786003 REACT_N_EPISODES=100 bash scripts/run_hotpot_parallel.sh 100 4`
  (or set `REACT_NUM_WORKERS`/`REACT_WORKER_ID` manually).
- Worker logs (server): `src/run_hotpot_w{0..3}.log`. Per-worker `FINAL[...]` lines carry the seed.
- Commits: ea387a0 (migration) → 7bf97db (Wikipedia UA) → 348b85b (modified-react mode) →
  d73f39a (full-run resilience) → da8604c (parallel + random sample).
