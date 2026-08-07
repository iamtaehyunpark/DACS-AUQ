# S5 / b3 — pre-call checks (D2.1). **HALTED: check (b) fails for every candidate.**

**2026-08-08 · EXECUTION_HANDOVER v2 §4 · STOP_GATE_DECISIONS D2**
No API call has been made and no key has been used.

D2.1 requires two verifications *before any call*. One is blocking on a fact the
decision did not anticipate.

## Check (b) — frontier model disjoint from the label-ensemble trio: **FAILS**

The 3-judge ensemble that produced every `judgment` label is, read from
`result/pivot/*/*/judge.jsonl`:

| ensemble member |
|---|
| `grok-4.3` |
| `DeepSeek-V4-Pro` |
| `gpt-5.6-sol` |

D2.1(b) says a frontier judge that is **not** disjoint from this trio has its
judgment-column comparison marked **contaminated in every table it appears in**.

All three obvious frontier candidates are *inside* the trio. `gpt-5.6-sol` is the
model already wired into `src/judge_e0.py` / `src/judge_hotpot.py` as
`OPENAI_JUDGE_MODEL`, and it is an ensemble member. So the default configuration
would produce a contaminated b3 arm — a frontier judge grading labels it helped
create.

This is not a reason to skip b3. It is a reason the model choice is now an author
decision rather than a default:

1. **Pick a frontier model outside the trio** — the arm stays clean on every
   construct, including judgment. Requires a provider we have not used here.
2. **Use a trio member anyway** and mark the judgment column contaminated wherever
   it appears, per D2.1(b). The `violation` and `outcome` columns remain clean,
   since those labels come from the environment and no LLM contributed to them —
   so a contaminated run is still informative for G2-R4 on two of three constructs.
3. **Use a same-family, different-model** option (e.g. a different OpenAI model id).
   Weaker than (1): not literally the same model, but not independent either. If
   taken, it should be disclosed as partial independence rather than claimed clean.

## Check (a) — deepseek `top_logprobs`: **NOT RUN**

Blocked by the above and by credentials: no `DEEPSEEK_*` key is present in the
server environment, and the only key wired in is the OpenAI one. The check itself is
a single call once a provider is chosen; if `top_logprobs` is absent the logprob arm
is **dropped for that provider, never approximated** (D2.1(a)).

## Cost

No `$/1k` figure is given here. Per D2.2 that number comes from the ~500-call pilot,
and the pilot cannot start until the model is chosen. Stating a cost now would be a
guess dressed as a budget.

## What the author is being asked

Choose the frontier model for b3, knowing that the three obvious candidates are all
ensemble members. On that choice the pilot runs immediately and returns
`S5_BUDGET_MEASURED.md` with the measured `$/1k` and a projected full-run cost, then
re-halts for the 5,000-call acknowledgement exactly as D2.2 specifies.

If b3 goes unfunded before the writing milestone, `S5_UNRESOLVED.md` ships instead,
stating that the frontier tier is open and that G2-R4 is unresolved — v2 §4 already
provides for this.
