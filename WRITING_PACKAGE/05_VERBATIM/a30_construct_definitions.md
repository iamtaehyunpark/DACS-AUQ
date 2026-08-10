# A30 §2–3 — the construct and the three label families
**Source: `reports/A30_label_constructs.md` §2 and §3 (verbatim).**

## 2. The construct this paper measures

The paper's evaluation target, fixed since §1 of the proposal, is **ex-ante decision
quality**: the correctness of (state + history + reasoning → action) given the
information available at decision time. It is explicitly NOT hindsight outcome quality —
the gap between the two is the paper's own framing device (the online/hindsight
knowledge gap, §8.vi). Any label family must be read against this construct.

## 3. Three label constructs, and where each stands

**(a) Violation labels — A1 inadmissible, A2 no-op, A3 exact repeat, malformed calls.**
Wrong under EVERY construct, including ex-ante: the legal-command list was in the
agent's prompt (A1); a repeated (state, action) pair has zero information gain by
construction — the agent already holds the outcome (A3). "Agents explore" does not
cover these: exploration is trying what you don't know; A3 re-tries what you do know.
Certainty: environmental, absolute. Ensemble agreement: 98.0–99.7% per sub-rule.
**These labels are not in dispute and anchor everything.**

**(b) Outcome labels — A4 zero-result search; Tier-B gold-supporting-fact retrieval
(HotpotQA) and expert-plan distance (ALFWorld).** Hindsight-anchored: they encode
oracle knowledge the agent lacks (which query hits, which cabinet holds the item, what
the expert plan is). A well-formed query over an unknown corpus that returns nothing is
a failed OUTCOME and a defensible DECISION. These labels measure progress against an
oracle, i.e., the hindsight side of the paper's own online/hindsight gap. They are not
wrong; they answer a different question.

**(c) Judgment labels — the 3-judge ensemble.** Ex-ante semantic assessment: the same
construct as the paper's target. Previously suspect for circularity; the gate-1 audit
now bounds that suspicion: on steps where certain ground truth exists, ensemble error is
**1.3% (A1) / 0.8% (A2) / 0.3–1.9% (A3) / 2.0% overall ex-A4**. The 9.1% headline is
dominated by A4 (31.5% "error"), where under construct (b)-vs-(c) divergence the
ensemble is plausibly judging ex-ante soundness correctly. **The circularity audit,
designed to indict the ensemble, substantially validated it on the overlap** — while
proving the constructs measurably diverge off the overlap.
