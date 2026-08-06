# Gate-1 Phase 0 — inventory and field audit

Corpus: `result/pivot`. Log-scan only — no inference, no environment, no GPU.


## 0. Findings

**Scope.** 16 arms carry `uq.jsonl`; 11 of them are the targets behind the 56-cell (assessor × target) matrix (44573 steps). The 5 `Qwen3.5-*` arms are outside the matrix and are inventoried for completeness only.

**The corpus is live, so every read is pinned.** While gate 1 ran, a `judge_hotpot.py` process and eight `run_probes.py` workers were still appending to the `Qwen3.5-*` arms (none of which is in the 56-cell matrix). Every gate-1 input is therefore recorded in `reports/gate1/input_manifest.json` as (size, sha256, mtime) and every reader takes only the first `size` bytes, so a concurrent append cannot change a result. Verified: one judge file grew by 139 KB mid-run and the Phase-1 output was byte-identical across the two runs that straddled it. `gate1_manifest.py --verify` re-checks the pinned prefixes.

**0.1 — field presence.** Every field gate 1 depends on (`action_parsed`, `obs`, `obs_changed`, `admissible`, `in_admissible`, `loop_flag`, `state_hash`, `task_id`, `step_idx`, `skip_reasons`) is present on **100% of step records in every arm**, non-null. Only `U_verbalized` and `tau` carry nulls, and both are elicitation/tagging outputs rather than environment evidence, so neither blocks labelling.

**0.1 — HotpotQA. STOP condition partially triggered.** Of the four fields named in the brief, three are fully recoverable and one is not:

- *tool-call validity* — recoverable. `in_admissible` is logged on every step and agrees with an independent re-derivation from the `Search|Lookup|Finish[...]` grammar on **every step of every arm** (0 disagreements).
- *result count* — recoverable. `wikienv` emits a fixed `Could not find {entity}. Similar: [...]` / `No more results.` string, so a retrieval that loaded no page is detectable from `obs` verbatim.
- *query text* — recoverable, verbatim in `action_parsed`.
- *gold supporting-fact ids* — **NOT recoverable.** The vendored corpus `src/data/hotpot_dev_v1_simplified.json` holds only `question` / `answer` / `type`; there are no `supporting_facts` and no context paragraphs. No copy carrying them exists on the machine (the only other HotpotQA files, under `experiments/single_agent_uncertainty_exp/data/`, are likewise question/answer only).

  Consequence, per the hard constraint against improvising labels: **Phase 3's HotpotQA search-step rule ("retrieved a gold supporting document") is halted.** Everything else proceeds. The HotpotQA *answer*-step rule is unaffected — `em`, `f1`, `gold_answer` and `predicted_answer` are present on 100% of episode records — and HotpotQA Tier A is unaffected, since A1/A3/A4 need none of the blocked field.

**0.2 — skip-reason taxonomy.** Four reasons occur corpus-wide. Two are action evidence and are **included** in the gate-1 label set as the brief directs:

- `tau_unrecognized_action` — the action matched no entry in the environment grammar.
- `invalid_action_syntax` (HotpotQA only) — same event, logged by the Hotpot drivers alongside the τ reason; the two co-occur one-for-one in every arm.

Two are **flagged as ambiguous and NOT decided here** (see §7).

**0.3 — Tier-A coverage** on matrix arms runs from **23.5% (alfworld/deepseek-v4-flash)** to **81.6% (alfworld/gemma-3-4b-it)** of steps. Tier A produces incorrect labels only, so this is an upper bound on what Tier A alone can decide; Tier B has to carry the rest.

**A3 is an observation-repeat rule, not a state-repeat rule.** `state_hash` is `sha1(obs)[:16]` of the *post*-action observation, so the pair `(state_hash, action_parsed)` is the pair `(obs, action)` the drivers already track as `loop_flag`. Recomputed independently, A3 and `loop_flag` agree on **every ALFWorld step in every arm** (0 disagreements). A3 is therefore reproducing the logged loop detector exactly — it adds no independent evidence, and it cannot detect a revisit to the same world state that produced a different observation.


## 1. Arms and record counts

| dataset | model | in 56-cell matrix | steps | episodes (records) | episodes (distinct task_id) | dup step keys |
|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | yes | 4765 | 140 | 140 | 0 |
| alfworld | Mistral-7B-Instruct-v0.3 | yes | 6482 | 140 | 140 | 0 |
| alfworld | Phi-4-mini-instruct | yes | 6611 | 140 | 140 | 0 |
| alfworld | Qwen3.5-27B | **no** | 3445 | 140 | 140 | 0 |
| alfworld | Qwen3.5-4B | **no** | 4602 | 140 | 140 | 0 |
| alfworld | Qwen3.5-9B | **no** | 4590 | 140 | 140 | 0 |
| alfworld | Qwen3.6-35B-A3B | yes | 3342 | 140 | 140 | 0 |
| alfworld | deepseek-v4-flash | yes | 3313 | 117 | 120 | 0 |
| alfworld | gemma-3-4b-it | yes | 6790 | 140 | 140 | 0 |
| hotpotqa | Llama-3.3-70B-Instruct | yes | 2530 | 500 | 500 | 0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | yes | 3224 | 500 | 500 | 0 |
| hotpotqa | Phi-4-mini-instruct | yes | 2716 | 500 | 500 | 0 |
| hotpotqa | Qwen3.5-4B | **no** | 2479 | 500 | 500 | 0 |
| hotpotqa | Qwen3.5-9B | **no** | 2376 | 500 | 500 | 0 |
| hotpotqa | Qwen3.6-35B-A3B | yes | 2235 | 500 | 500 | 0 |
| hotpotqa | gemma-3-4b-it | yes | 2565 | 500 | 500 | 0 |

## 2. Step-field presence (0.1)

Each cell is present/steps; `null` in parentheses when a present key is null.

| dataset | model | task_id | step_idx | action_parsed | obs | obs_changed | admissible | in_admissible | loop_flag | state_hash | U_verbalized | skip_reasons | tau |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| alfworld | Mistral-7B-Instruct-v0.3 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 0.0%) | 100.0% | 100.0% (null 2.6%) |
| alfworld | Phi-4-mini-instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 1.1%) |
| alfworld | Qwen3.5-27B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 6.9%) | 100.0% | 100.0% (null 6.3%) |
| alfworld | Qwen3.5-4B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 25.6%) | 100.0% | 100.0% (null 11.4%) |
| alfworld | Qwen3.5-9B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 8.1%) | 100.0% | 100.0% (null 7.4%) |
| alfworld | Qwen3.6-35B-A3B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 16.0%) | 100.0% | 100.0% (null 5.2%) |
| alfworld | deepseek-v4-flash | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 0.3%) | 100.0% | 100.0% (null 0.3%) |
| alfworld | gemma-3-4b-it | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 58.6%) | 100.0% | 100.0% (null 0.5%) |
| hotpotqa | Llama-3.3-70B-Instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 0.0%) | 100.0% | 100.0% (null 0.3%) |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 0.7%) |
| hotpotqa | Phi-4-mini-instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 0.1%) | 100.0% | 100.0% (null 0.6%) |
| hotpotqa | Qwen3.5-4B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 20.2%) | 100.0% | 100.0% (null 4.8%) |
| hotpotqa | Qwen3.5-9B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 3.5%) | 100.0% | 100.0% (null 3.5%) |
| hotpotqa | Qwen3.6-35B-A3B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 3.4%) | 100.0% | 100.0% (null 1.9%) |
| hotpotqa | gemma-3-4b-it | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% (null 57.0%) | 100.0% | 100.0% |

## 3. skip_reasons taxonomy (0.2)

| dataset | model | `<none>` | `confidence_parse_failed` | `invalid_action_syntax` | `tau_unrecognized_action` | `thought_parse_failed` |
|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 4765 | 0 | 0 | 0 | 0 |
| alfworld | Mistral-7B-Instruct-v0.3 | 6310 | 2 | 0 | 171 | 0 |
| alfworld | Phi-4-mini-instruct | 6548 | 0 | 0 | 63 | 0 |
| alfworld | Qwen3.5-27B | 3209 | 236 | 0 | 14 | 0 |
| alfworld | Qwen3.5-4B | 3399 | 1179 | 0 | 37 | 0 |
| alfworld | Qwen3.5-9B | 4213 | 372 | 0 | 16 | 0 |
| alfworld | Qwen3.6-35B-A3B | 2776 | 535 | 0 | 33 | 0 |
| alfworld | deepseek-v4-flash | 3303 | 10 | 0 | 1 | 0 |
| alfworld | gemma-3-4b-it | 2797 | 3977 | 0 | 34 | 0 |
| hotpotqa | Llama-3.3-70B-Instruct | 2522 | 1 | 7 | 7 | 0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 3200 | 0 | 24 | 24 | 0 |
| hotpotqa | Phi-4-mini-instruct | 2698 | 3 | 15 | 15 | 0 |
| hotpotqa | Qwen3.5-4B | 1978 | 501 | 10 | 10 | 0 |
| hotpotqa | Qwen3.5-9B | 2292 | 83 | 3 | 3 | 0 |
| hotpotqa | Qwen3.6-35B-A3B | 2159 | 75 | 1 | 1 | 1 |
| hotpotqa | gemma-3-4b-it | 1102 | 1463 | 0 | 0 | 0 |

## 4. Tier-A coverage (0.3)

Tier A emits **incorrect** labels only; coverage = share of steps it can label at all.

| dataset | model | steps | A1 | A2 | A3 | A4 | any (coverage) |
|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 4765 | 397 | 183 | 1556 | 0 | 1714 (36.0%) |
| alfworld | Mistral-7B-Instruct-v0.3 | 6482 | 3502 | 2415 | 3303 | 0 | 4616 (71.2%) |
| alfworld | Phi-4-mini-instruct | 6611 | 2302 | 1112 | 3185 | 0 | 4109 (62.2%) |
| alfworld | Qwen3.5-27B | 3445 | 351 | 143 | 797 | 0 | 967 (28.1%) |
| alfworld | Qwen3.5-4B | 4602 | 1563 | 890 | 1902 | 0 | 2464 (53.5%) |
| alfworld | Qwen3.5-9B | 4590 | 901 | 378 | 1421 | 0 | 1840 (40.1%) |
| alfworld | Qwen3.6-35B-A3B | 3342 | 493 | 206 | 911 | 0 | 1157 (34.6%) |
| alfworld | deepseek-v4-flash | 3313 | 165 | 46 | 688 | 0 | 779 (23.5%) |
| alfworld | gemma-3-4b-it | 6790 | 2909 | 2100 | 5145 | 0 | 5538 (81.6%) |
| hotpotqa | Llama-3.3-70B-Instruct | 2530 | 7 | 0 | 132 | 732 | 841 (33.2%) |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 3224 | 24 | 0 | 878 | 2042 | 2277 (70.6%) |
| hotpotqa | Phi-4-mini-instruct | 2716 | 15 | 0 | 830 | 1290 | 1620 (59.6%) |
| hotpotqa | Qwen3.5-4B | 2479 | 118 | 0 | 193 | 970 | 1174 (47.4%) |
| hotpotqa | Qwen3.5-9B | 2376 | 83 | 0 | 159 | 899 | 1057 (44.5%) |
| hotpotqa | Qwen3.6-35B-A3B | 2235 | 43 | 0 | 59 | 712 | 794 (35.5%) |
| hotpotqa | gemma-3-4b-it | 2565 | 0 | 0 | 835 | 1009 | 1386 (54.0%) |

## 5. HotpotQA field recoverability (0.1 STOP check)

| model | tool-call validity | result count | query text | gold supporting-fact ids |
|---|---|---|---|---|
| Llama-3.3-70B-Instruct | yes (`in_admissible` + grammar; 0 disagreements) | yes (zero-result detectable from `obs`: 732) | yes (100.0% of steps) | **NO** |
| Mistral-7B-Instruct-v0.3 | yes (`in_admissible` + grammar; 0 disagreements) | yes (zero-result detectable from `obs`: 2042) | yes (100.0% of steps) | **NO** |
| Phi-4-mini-instruct | yes (`in_admissible` + grammar; 0 disagreements) | yes (zero-result detectable from `obs`: 1290) | yes (100.0% of steps) | **NO** |
| Qwen3.5-4B | yes (`in_admissible` + grammar; 0 disagreements) | yes (zero-result detectable from `obs`: 970) | yes (95.6% of steps) | **NO** |
| Qwen3.5-9B | yes (`in_admissible` + grammar; 0 disagreements) | yes (zero-result detectable from `obs`: 899) | yes (96.6% of steps) | **NO** |
| Qwen3.6-35B-A3B | yes (`in_admissible` + grammar; 0 disagreements) | yes (zero-result detectable from `obs`: 712) | yes (98.1% of steps) | **NO** |
| gemma-3-4b-it | yes (`in_admissible` + grammar; 0 disagreements) | yes (zero-result detectable from `obs`: 1009) | yes (100.0% of steps) | **NO** |

## 6. Episode-field presence

| dataset | model | task_id | success | terminal_reason | n_steps | loop_collapse_fraction | em | f1 | gold_answer | predicted_answer | question |
|---|---|---|---|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | Mistral-7B-Instruct-v0.3 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | Phi-4-mini-instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | Qwen3.5-27B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | Qwen3.5-4B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | Qwen3.5-9B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | Qwen3.6-35B-A3B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | deepseek-v4-flash | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| alfworld | gemma-3-4b-it | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| hotpotqa | Llama-3.3-70B-Instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 99.8% | 100.0% |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| hotpotqa | Phi-4-mini-instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 99.8% | 100.0% |
| hotpotqa | Qwen3.5-4B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| hotpotqa | Qwen3.5-9B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 99.8% | 100.0% |
| hotpotqa | Qwen3.6-35B-A3B | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 99.8% | 100.0% |
| hotpotqa | gemma-3-4b-it | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

## 7. Flagged for decision — NOT resolved here (0.2)

Two skip reasons are reported rather than decided, because including or excluding them changes what the label set means and the brief reserves that call. Numbered F1/F2 below.

**F1 · `confidence_parse_failed`** — the model's confidence number could not be parsed. This is a failure of the *elicitation*, not of the *action*: the step's action can be perfectly valid and admissible. It is not evidence of an incorrect step, so Tier A does not fire on it and gate-1 labelling is unaffected. What it does affect is **U-side coverage**: these steps have `U_verbalized == null` and therefore drop out of any verbalized-U analysis regardless of label.

| dataset | model | steps | confidence_parse_failed | share |
|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 4765 | 0 | 0.0% |
| alfworld | Mistral-7B-Instruct-v0.3 | 6482 | 2 | 0.0% |
| alfworld | Phi-4-mini-instruct | 6611 | 0 | 0.0% |
| alfworld | Qwen3.6-35B-A3B | 3342 | 535 | 16.0% |
| alfworld | deepseek-v4-flash | 3313 | 10 | 0.3% |
| alfworld | gemma-3-4b-it | 6790 | 3977 | 58.6% |
| hotpotqa | Llama-3.3-70B-Instruct | 2530 | 1 | 0.0% |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 3224 | 0 | 0.0% |
| hotpotqa | Phi-4-mini-instruct | 2716 | 3 | 0.1% |
| hotpotqa | Qwen3.6-35B-A3B | 2235 | 75 | 3.4% |
| hotpotqa | gemma-3-4b-it | 2565 | 1463 | 57.0% |

The rate is not uniform — it is a near-majority for `gemma-3-4b-it` in both environments — so whichever way this is decided it is a per-arm effect, not a wash.

**F2 · `thought_parse_failed`** — same class of event on the thought channel. It occurs 1 time corpus-wide and is listed only for completeness.


## 8. Data-integrity notes

| dataset | model | empty `action_parsed` | of those, no skip_reason | task_ids with steps but no episode record |
|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 0 | 0 | 0 |
| alfworld | Mistral-7B-Instruct-v0.3 | 0 | 0 | 0 |
| alfworld | Phi-4-mini-instruct | 7 | 7 | 0 |
| alfworld | Qwen3.5-27B | 204 | 0 | 0 |
| alfworld | Qwen3.5-4B | 489 | 0 | 0 |
| alfworld | Qwen3.5-9B | 325 | 0 | 0 |
| alfworld | Qwen3.6-35B-A3B | 142 | 1 | 0 |
| alfworld | deepseek-v4-flash | 9 | 0 | 3 |
| alfworld | gemma-3-4b-it | 0 | 0 | 0 |
| hotpotqa | Llama-3.3-70B-Instruct | 0 | 0 | 0 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 0 | 0 | 0 |
| hotpotqa | Phi-4-mini-instruct | 0 | 0 | 0 |
| hotpotqa | Qwen3.5-4B | 108 | 0 | 0 |
| hotpotqa | Qwen3.5-9B | 80 | 0 | 0 |
| hotpotqa | Qwen3.6-35B-A3B | 42 | 0 | 0 |
| hotpotqa | gemma-3-4b-it | 0 | 0 | 0 |

- An **empty `action_parsed` carries no skip reason at all**: the drivers guard both `invalid_action_syntax` and `tau_unrecognized_action` behind `and action`, so a step where the model emitted nothing is invisible to a skip-reason filter. Tier A still catches it via A1 (`in_admissible == false` / grammar mismatch), which is why A1 counts exceed the corresponding skip-reason counts in several arms.
- Any non-zero entry in the last column is an episode whose steps were logged but whose terminal record was not, so `success` / `terminal_reason` are unavailable for it. These episodes are excluded from `y_suffix` (which needs the episode outcome) and flagged in the Phase-4 coverage columns; Tier A and Tier B are unaffected.


## 9. Scan integrity

`call` records are skipped by a head test rather than parsed. 1-in-5000 skipped
lines are parsed to confirm they are `call` records; any other kind here is a bug.

| dataset | model | skipped lines | sampled kinds |
|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 4765 | {'call': 1} |
| alfworld | Mistral-7B-Instruct-v0.3 | 6482 | {'call': 2} |
| alfworld | Phi-4-mini-instruct | 6611 | {'call': 2} |
| alfworld | Qwen3.5-27B | 3445 | {'call': 1} |
| alfworld | Qwen3.5-4B | 4602 | {'call': 1} |
| alfworld | Qwen3.5-9B | 4590 | {'call': 1} |
| alfworld | Qwen3.6-35B-A3B | 3342 | {'call': 1} |
| alfworld | deepseek-v4-flash | 3313 | {'call': 1} |
| alfworld | gemma-3-4b-it | 6790 | {'call': 2} |
| hotpotqa | Llama-3.3-70B-Instruct | 2530 | {'call': 1} |
| hotpotqa | Mistral-7B-Instruct-v0.3 | 3224 | {'call': 1} |
| hotpotqa | Phi-4-mini-instruct | 2716 | {'call': 1} |
| hotpotqa | Qwen3.5-4B | 2479 | {'call': 1} |
| hotpotqa | Qwen3.5-9B | 2376 | {'call': 1} |
| hotpotqa | Qwen3.6-35B-A3B | 2235 | {'call': 1} |
| hotpotqa | gemma-3-4b-it | 2565 | {'call': 1} |
