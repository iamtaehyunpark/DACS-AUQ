# S9_appendix — brief

**Claims (home):** **N-retrostream** (A31: dropped, recorded as untested — not
tested-and-failed; migration note to follow-up MAS work per D3), **N-hindsight**
(A35: S4 void; postmortem only).

**num_ids:** S4-01…S4-04 (postmortem + probe facts), HA-14 (forecast lock), HA-15
(h-noself), MS-01 (A35 pre-seal audit), MS-03 (frontier logprob availability),
MS-07 (S1 L1 reproduction check), CO-02 (hindsight throughput constant), CO-07
(b3 spend), PQ-04 (prequential protocol), FR-10 (b3 pilot measurement).

**Content blocks:**
1. **Gates ledger, verbatim** — include `FINAL_BUNDLE/GATES_LEDGER.md` in full
   (every verdict quoted anywhere in the paper must match it exactly).
2. **S4 postmortem** (debt 13) — verbatim/s4_postmortem.md. The consistency warning
   there is mandatory: server-side `S4_SUMMARY.md` result tables are NOT of record.
3. **Deviations** (debt 12, shared with S6 — flagged) — verbatim/b3_deviations.md.
4. **Seal-defect disclosure** (debt 11, shared with S7 — flagged) —
   verbatim/seal_defect.md incl. the lock block.
5. **Reproducibility:** seed 13 everywhere; 2000 bootstrap draws; prequential seeds
   13–22; spec sha256s recorded under `runs/manifest.json:specs_recorded`; throughput
   constants CO-01/CO-02 with their verified flags; A35 tripwire (S4-03) and A36
   artifact-hash / ack-token discipline (ledger A-log entry: a sealed artifact is
   identified by its content hash; a run is gated on a recorded acknowledgement
   token).
6. **Spot-check package description** — `spotcheck/INSTRUCTIONS.md` (150 blinded
   steps, 20 calibration controls, ex-ante question; deferred under D4).

**Tables:** T12b (full GATE-4 evaluation grid) lives here in print if not inline.

**Verbatim:** s4_postmortem.md, seal_defect.md (shared), b3_deviations.md (shared),
closed_questions.md (the list itself ships in the appendix; nothing in it may be
reopened by the draft).

**Debts:** **13** (S4 postmortem paragraph).

**S9 (single-judge procedure test):** NOT included — conditional on an author ack
that does not exist at assembly time (OPEN_DECISIONS item 4). Per the handoff, no S9
content anywhere.
