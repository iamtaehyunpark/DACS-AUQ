# S5_BUDGET — frontier external judge b3 (STOP gate)

**This branch is HALTED pending author budget acknowledgement (EXECUTION_HANDOVER.md §6).** No API key is used and no call is made until then.

## Sample

Stratified per A27: target x dataset x error-tercile x TierA-flag. Target **2,500 steps** across 11 in-matrix arms (~227 per arm), frozen before sampling, seed logged.

## Calls

| arm | framing | calls |
|---|---|---|
| frontier verdict | decision-framed | 2,500 |
| frontier verdict | trust-framed | 2,500 |
| **total** | | **5,000** |

P(True) comes from the same calls via `top_logprobs` where the provider exposes it (OpenAI: yes; deepseek: **verify before sizing** — if not exposed, text verdict only and the logprob arm is dropped, not faked).

## Cost

Cost per call depends on prompt length, which is the banked AGG-true evidence context. The manifest pins those files; a 500-call pilot on one arm gives the token-per-call figure. **A dollar estimate without that pilot would be a guess, and this document does not make one.**

The comparison column the handover requires is $/1k steps for the frontier arm against measured self-hosted throughput for the best open-tier arm from S1d.

## What the author is being asked

1. Approve a ~500-call pilot to fix the per-call cost (small, bounded).
2. Then approve or decline the full 5,000 calls at the measured rate.
3. Confirm the provider list, and whether deepseek exposes top_logprobs.

G2-R4 resolves here.

