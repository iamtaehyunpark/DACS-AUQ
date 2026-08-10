# 06_GAPS — everything requested that could not be located, plus conflicts of record

Format per item: requested · searched · nearest artifact · can the writer proceed?

## Gaps (requested by the handoff, not located)

1. **A-log as a standalone A1–A36 document.** Searched repo root, `docs/`, `reports/`
   on both laptop and server (filename patterns `*a_log*`, `*alog*`, `*amendment*`).
   Nearest: `FINAL_BUNDLE/GATES_LEDGER.md` §"A-log entries bearing on verdicts"
   (A30, A31, A32, A34.1, A35, A36 — every verdict-bearing entry) and
   `docs/paper_proposal_v4.md` §12 (A20–A24). A1–A19 and A25–A29 exist only as
   scattered references. **Proceed: yes** — all entries the paper must cite are in
   the ledger; a full numeric A-log would only serve the appendix's completeness.

2. **Proposal v4.1.** Only **v4** (2026-08-05, amendments A20–A24) exists on both
   machines. "v4.1" is referenced by S6_DECISION/EXECUTION_HANDOVER as the
   post-A25/A31 revision, which was never written to a file — its content lives in
   `STOP_GATE_DECISIONS.md` (D3 thesis-sentence retreat) and the bundle.
   **Proceed: yes** — use v4 + STOP_GATE_DECISIONS; the §9 clause list shipped in
   S2_related is v4's.

3. **b3 "$18.92 / 2,500 steps" (handoff §2).** Not found in any artifact. Nearest:
   `S5_SUMMARY.md` receipt (~$60 total, 7,879 calls, $7.60/1k) and
   `result/b3/b3_sample.csv` (server; 2,475-step frozen sample of the b3 arm —
   2,475 × $7.60/1k ≈ $18.8, the likely origin as the b3-only slice). The registry
   carries only receipt-backed numbers (CO-03, CO-07). **Proceed: yes** — quote the
   receipt figures; do not print $18.92 without a source.

4. **Part B conditional-density overlays (F3's "conditional overlays").** Banked
   artifacts are `tables_gate4/B_wasserstein_pairs.csv` and the verdict table only;
   per-class density curves (f₀/f₁ per target) were never written to CSV. Raw scores
   to regenerate them exist on the server (`result/pivot/crossprobe/`), but
   regeneration is recomputation and is out of contract. **Proceed: yes** — F3 ships
   distances; the paper can describe rather than plot the overlays, or the author
   commissions a regeneration outside this package.

5. **Retention-curve data behind "96–99.9% at ~200 labels" (LT-06).** The sentence
   exists in `docs/paper_proposal_v4.md` §6 (banked, L1-era "sample-efficiency
   curves" per §Status); the underlying curve CSV was not located under `tables_*`
   or `reports/tables/`. **Proceed: yes** for the sentence at its stored precision;
   the curve figure cannot be drawn from this package.

## Conflicts of record (both included; not chosen — per contract §0)

6. **S4 void size: 69,940 vs 44,573.** `runs/manifest.json` `voided.A35_S4_hindsight`
   and debt 13 record **69,940 records / 17 files VOID**. A server-side, untracked
   `S4_SUMMARY.md` reports an analysis over **44,573 records** of the same arm
   (single-judge Qwen half) with uniformly negative deltas — written before/despite
   the A35 void; the ledger, OPEN_DECISIONS and the claim map all carry S4 as
   DROPPED. **Writer instruction:** the postmortem cites 69,940 (manifest verbatim);
   `S4_SUMMARY.md`'s result tables are NOT of record and must not be cited
   (see 05_VERBATIM/s4_postmortem.md).

7. **A28.1 capable capture CI: [0.084, 0.844] vs [0.0970, 0.8471].**
   `reports/gate2/GATE2B1_SUMMARY.md` prints the former; `S2_SUMMARY.md` /
   `tables_bundle/ci_registry_final.csv` print the latter (independent bootstrap
   re-run, same seed policy, 2000 draws). Same verdict either way (CI spans 0.5).
   Both are recorded (HA-03 vs HA-04/MS-04). **Writer instruction:** quote ONE
   consistently and say which artifact it comes from; the bundle's
   `ci_registry_final.csv` is the registry-of-record for CIs per
   `tables_bundle/REGISTRY_CHANGELOG.md` — but the choice is the author's, not
   this package's.

8. **Gate-1 R4 headline: 9.1% (matrix arms) vs 10.6% (all arms).** Not strictly a
   conflict — two populations — but both appear as "the R4 number" in different
   artifacts (`GATE1_SUMMARY.md` prints 9.1% as the rule's number; the audit's own
   §R4 prints 10.6%). LB-04 carries both with denominators. **Writer instruction:**
   the pre-registered R4 number is the matrix-arm 9.1% (2233/24631); 10.6% is the
   all-arms figure.

## Both-label-pass defects (rule §7.4 — flagged, not fixable without recomputation)

9. **L1-only analyses with no L2 counterpart:** the evidence grid (T5/F6, EG-*),
   adaptivity (T7, AD-*), the tier-contrast per-cell table (T8, TR-02…04), the
   verdict-vs-value per-judge table (T6; its L2 counterpart exists only as
   per-construct aggregate gains CH-03…07), the OPERATING_POINT quantities (ME-06,
   ME-07, ME-09), and the flatness curves (F2, ME-01). These analyses were never
   rerun under L2; recomputation is out of contract. **Writer instruction:** every
   table states its label pass; L1-only tables must carry the "L2 rerun not
   performed for this analysis" qualifier rather than an implied L2 status.

## Untracked canonical inputs (located, but not in git at assembly time)

10. `reports/A30_label_constructs.md`, `labelfree_transfer_explainer.md`,
    `EXECUTION_HANDOVER.md`, `REMAINING_WORK.md`, `docs/PAPER_DATA_HANDOFF.md`,
    `reports/gate1/HANDOVER.md` (laptop, untracked) and `S4_SUMMARY.md` (server,
    untracked). Registry rows citing them carry their sha256 as read at assembly.
    **Recommend committing** the laptop set so the shas stay resolvable.

*An empty GAPS file is the completion signal; this one is not empty. Items 1–5 are
resolvable by the author in minutes each; items 6–9 are standing instructions to the
writer, not blockers.*
