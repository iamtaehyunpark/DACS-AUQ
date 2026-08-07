# S5 / b3 — UNRESOLVED: frontier tier open

**2026-08-08 · EXECUTION_HANDOVER v2 §4 fallback · for the limitations section**

The frontier-judge arm did not run. Two independent blockers, one hard.

## 1. Billing (hard blocker)

The OpenAI key at `MULTIAGENT/api.key` is valid but has **no credits**:

```
429 RateLimitError — You have no credits remaining. Add credits to continue
using the API.
```

Provider fixed to OpenAI by author decision (2026-08-08): GPT via the OpenAI API,
not Azure. So the ~500-call pilot D2.2 requires cannot start, and no `$/1k` figure
exists. **No cost estimate is given here** — inventing one would be the same error
as the 1.3–3.9 A100-hour estimate that the S4 probe later corrected 8.8×.

## 2. Contamination (soft, and it survives the billing fix)

D2.1(b) requires the frontier judge to be disjoint from the 3-model ensemble that
produced the `judgment` labels. Read from `judge.jsonl`, that ensemble is:

| ensemble member |
|---|
| `grok-4.3` |
| `DeepSeek-V4-Pro` |
| `gpt-5.6-sol` |

`gpt-5.6-sol` — the model wired into `src/judge_e0.py` and `src/judge_hotpot.py` as
`OPENAI_JUDGE_MODEL`, and the one the GPT-only decision selects — **is an ensemble
member**. Under D2.1(b) its judgment-column comparison is therefore marked
**contaminated** wherever it appears.

This does not void the arm. The `violation` and `outcome` constructs are labelled
from environment evidence with no LLM involvement, so those columns stay clean and
G2-R4 remains answerable on two of three constructs. Only the `judgment` column
would carry a frontier judge partly grading its own labels.

Choosing a different OpenAI model id would weaken rather than remove this: same
family, same training lineage, not independent. If that route is taken it should be
disclosed as partial independence, not as clean.

## What remains open

**G2-R4 is unresolved.** The paper cannot say whether a frontier external judge beats
the mid-tier open judges, because the frontier arm was never run. The limitations
section should state:

> The frontier tier is untested. Cost-to-capability comparisons in this paper are
> between open-weight judges at the 4B–70B scale; whether a frontier API judge
> changes the picture is open, and the comparison was not run.

## To unblock

1. Add credits to the OpenAI account, then the ~500-call pilot runs immediately and
   returns `S5_BUDGET_MEASURED.md` with measured `$/1k` and a projected full-run
   cost, re-halting for the 5,000-call acknowledgement per D2.2.
2. Decide the contamination handling: accept the mark on the judgment column, or
   nominate a model outside the trio.

Neither is on the critical path — v2 §4 already provides for shipping this as open.
