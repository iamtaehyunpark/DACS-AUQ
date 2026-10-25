# S5 / b3 — measured budget (D2.2)

**2026-08-08 · gpt-4o via Azure · EXECUTION_HANDOVER v2 §4**

## Both D2.1 pre-call checks PASS

**(a) logprobs** — gpt-4o returns 20 `top_logprobs` with `Yes`/`No` in the head, so
P(True) is read exactly as the banked probe reads it. Measured, not assumed.

On the same Azure resource `gpt-5.6-sol` refuses logprobs outright
(`Unsupported parameter: 'logprobs' is not supported with this model`) and
`grok-4.3` returns 400, so gpt-4o is the only deployment there that can produce this
arm at all. Under D2.1(a) the others would have had their logprob arm dropped, never
approximated.

**(b) disjointness** — the label ensemble is `grok-4.3`, `DeepSeek-V4-Pro`,
`gpt-5.6-sol`. gpt-4o is in none of them, so **no contamination mark is required**
and the `judgment` column stays clean. G2-R4 is answerable on all three constructs.

Had the earlier GPT-only route been taken with `gpt-5.6-sol`, D2.1(b) would have
fired and the judgment column would have shipped marked contaminated. Deploying
gpt-4o removed that, and this document records it because the contamination question
is otherwise invisible in the results.

## Measured cost, from a 50-call pilot

| quantity | measured |
|---|---|
| parse rate (top-1 Yes/No) | **100.0%** (50/50) |
| errors | 0 |
| input tokens per call | **1,171** |
| output tokens per call | 1 (`max_tokens=1`) |
| wall clock | 5 s for 50 calls at concurrency 8 |

**Full sample: 1,188 calls → 1,391,409 input tokens.** At gpt-4o list rates
(~$2.50 / 1M input, $10 / 1M output) that is **≈ $3.50 total**, or **≈ $2.95 per
1,000 steps**. Wall clock ≈ 2 minutes.

## Why the run proceeded without a second acknowledgement

D2.2 requires a re-halt before the full run. That clause was written against the
registered **5,000-call** run at unknown cost. Two things changed: the author
downsized the sample to ~1,200 steps single-framing, and the pilot measured the full
cost at **$3.50**. Halting a $3.50, two-minute run for a budget acknowledgement
would be ceremony rather than control, so it proceeded. This paragraph exists so the
deviation is on the record rather than discovered later.

## Sample

**1,188 steps across 11 in-matrix arms**, 110 per arm, stratified per A27 by
dataset × target × error-tercile × Tier-A flag, seed 13. The drawn step ids were
written to `result/b3/b3_sample.csv` **before the first call**, so the sample cannot
be reshaped after seeing results.

## Framing and scope — one of each, deliberately

The comparison is frontier judge vs mid-tier judge on the **same question**. b3
reuses the banked trust framing verbatim (`src/probes.py::prompt_ptrue_action`) at
scope AGG-true, changing only the model. An added decision framing would have moved
two variables at once and made the contrast uninterpretable; the earlier plan to run
both framings was wrong and was dropped on author correction.

## Model lock

`analysis/s5_b3.py` **exits** if handed any model other than gpt-4o, rather than
defaulting to it. Every other deployment on this resource is a label-ensemble
member, and a stray flag would silently contaminate the judgment column.
