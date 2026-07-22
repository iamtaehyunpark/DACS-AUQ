# Pilot report — pure ReAct, 10 episodes (first test)

**Setup.** Pristine ysymyth/ReAct loop (HEAD 6bdb3a1), pure-Python migration, two API
migrations only (llm→vLLM, alfworld get_environment factory). Agent = **Qwen3.6-35B-A3B**
served single-GPU via vLLM 0.23.0 (`--served-model-name qwen`, max_model_len 8192, greedy,
max_tokens 100, stop=["\n"]). Split = eval_out_of_distribution (unseen), the upstream default.
Driver = Jagent env, ALFWORLD_DATA=/home/user/.cache/alfworld. Commit 4f1da5a.

## Headline

- **Ran end-to-end, no crashes.** Structure validated: env init, few-shot prompting, the
  `think:`/action interleave, env stepping, the 134-episode driver (capped to 10) all work.
- **Success: 1/10 (0.1).** Sampled task mix (random 10, unseen): clean×3, cool×2,
  examine×2, puttwo×3 (no put/heat drawn). The one success was an **examine** task
  (easiest type). Far below ReAct's published ~0.71 (davinci-002).
- **463 steps total. 203 (44%) returned "Nothing happens." 84 (18%) were empty actions.**

## The important finding: empty actions are a SPIRAL symptom, not a pervasive bug

**80 of 84 empty actions (95%) occur immediately after a "Nothing happens." observation.**
The failure is a spiral, not a constant leading-newline problem:

1. The model issues a command that doesn't take effect → `Nothing happens.`
2. Under greedy decoding, the repetitive failed context collapses the next-line
   distribution toward an immediate end-of-line → **empty action** → `Nothing happens.`
3. This compounds; the episode burns ~49 steps in the spiral and fails.

Episode 1 is the archetype — 9 textbook steps (find potato → take → cool with fridge → go
to microwave), then `put potato 1 in/on microwave 1` returns `Nothing happens.` **twice**
(even after opening the microwave), the model can't recover, and degenerates.

Breakdown of the 203 "Nothing happens.":
- **84** from empty actions (the spiral),
- **119** from non-empty commands that didn't take effect (invalid/ineffective — the
  canonical ReAct prompt does NOT show admissible commands, so the model must produce
  exact ALFWorld command strings from the few-shot alone).

## What this means for the rebuild premise

The rebuild assumed the empty-action degeneration was **our** plumbing bug (the decoupled
two-call setup feeding a chat model through raw completions). This pilot shows the
degeneration **reproduces in pristine canonical ReAct** with Qwen3.6. So it is at least
partly intrinsic to *this model × the completions+stop=newline paradigm*, triggered by
failed actions — not unique to our code.

Nuance, both true:
- **Intrinsic component:** even the reference loop spirals into empties once actions fail.
- **Our code amplified it:** the old decoupled setup produced ~45-50% empties from the
  start (prompt structure made newline the greedy first token at every action), vs 18%
  here concentrated in spirals.

## Open question for next step (not resolved here)

Why is the base "Nothing happens." rate 44%? Two candidates, separable with more analysis:
- **Command-string mismatch** — model emits commands that aren't in ALFWorld's admissible
  set (canonical ReAct shows no command list; davinci learned the exact strings, Qwen may
  not). 
- **ALFWorld mechanics** — e.g. the microwave-put failing twice suggests a precondition or
  version quirk the model mishandles.

Both point at the same lever: the reference ReAct prompt withholds admissible commands.
Whether to keep that (pure fidelity) or surface commands (our experiment's choice) is the
first real design fork — but it is a *finding to decide on*, not a bug to patch silently.

## Artifacts
- Full run log (server): `/tmp/react_pilot.log` (593 lines, all 10 transcripts).
- vLLM server log: `/tmp/vllm_pilot.log`.
