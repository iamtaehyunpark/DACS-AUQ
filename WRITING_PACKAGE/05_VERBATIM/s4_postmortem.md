# S4 postmortem facts
**Sources: `runs/manifest.json` `voided.A35_S4_hindsight` (verbatim), `FINAL_BUNDLE/WORDING_DEBTS.md` debt 13, `S4_COST.md` MEASURED–RE-HALT. Debt 13: ship as-is.**

Manifest void record (verbatim):

> status: VOID · records: 69940 · files: 17 · reason: "Hindsight block appended after a
> CLOSED chat template (prompt_templated ends <|start_header_id|>assistant<|end_header_id|>),
> so the judge continued the agent ReAct completion instead of answering. Top-1 token
> was \"The\" on 100% of records; U values are residual Yes/No mass behind a token the
> model never intended."

Debt 13 (verbatim):

> **S4 postmortem paragraph**: 69,940 records void from appending a prompt after a
> closed chat template; detected by top-1 token distribution; tripwire adopted as A35.

Probe facts of record (`S4_COST.md`, MEASURED — RE-HALT section): measured rate **375
assessments / 5 min / A100** vs the inherited constant 3,300 (8.8× optimistic); mean
hindsight prompt **6,957 tokens**, max **35,448** vs a 32,768 served context; 3/500
probe errors; projected **17.1 A100-hours** vs the 10.0 ceiling → re-halt under D1.2.
An earlier probe reporting 3,802/5min was invalid (it timed ~91-token prompts) and
nothing from it was used.

**Consistency warning for the writer (do not resolve silently):** a server-side,
untracked `S4_SUMMARY.md` reports an analysis of 44,573 records from this arm with
uniformly negative hindsight−online deltas. The arm is VOID under A35; those result
tables are NOT of record and must not be cited. The 69,940 (manifest, debt 13) vs
44,573 (S4_SUMMARY coverage) discrepancy is logged in 06_GAPS.md.
