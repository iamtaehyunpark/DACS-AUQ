# S2_related — brief

**Claims:** none owned (positioning section).

**num_ids:** none owned.

**Debts:** **3** — cite label-shift / BBSE literature where the percentile-indexing
family is introduced (source: REMAINING_WORK v2 §3; the h-rule is target shift with
invariant class-conditionals — `labelfree_transfer_explainer.md` §8 names BBSE as the
neighbor).

**Source material — the positioning clause list, copied verbatim from
`docs/paper_proposal_v4.md` §9 (per the handoff, source text not prose):**

> Training-free prompted (vs Kapoor's fine-tuned QA estimator; CEB's
> experience-bank critic; supervised escalation predictors) · step-granular
> online (vs UALA/SAUP/MATU trajectory verdicts — tensor-decomposition methods
> additionally require the full trajectory embedding and are offline by
> construction; vs guideline-accumulation's aggregated end-of-trajectory check;
> stepwise self-confidence work [2511.07364] independently finds step-level
> scoring improves error detection, supporting the granularity claim while
> remaining self-evaluation) · evidence-grid characterized (vs single-evidence
> guideline grounding — retrieved guidelines occupy one cell of our grid, the
> *prior* row; vs QA judging where answer text suffices — here it is chance) ·
> independence-tested (vs all self-evaluation including [2511.07364]; MT-Bench
> self-enhancement bias as precedent) · **characterized-instrument deployment**
> (vs per-model metric search, which our §2 shows failing, and vs one-threshold
> LLM-judge practice, which our §7.1 shows failing — the amortized/target-
> dependent split is measured, not assumed) · τ-gated (nearest antecedent: the
> agentic-UQ survey's interactive/evidential action classification, used there
> to model information-gain-driven uncertainty reduction, not to gate estimator
> invocation — see §4.3) · consequence-labeled released corpus with
> environment-anchored provenance (the survey's named benchmark gap).

**Also source text (same file, §9):** the problem-statement lineage paragraph (CEB
formulation adopted; Kapoor extension) and the Tian et al. reconciliation paragraph
(scoped by tier). Copy from `docs/paper_proposal_v4.md` lines under "Problem-statement
lineage" and "The Tian et al. reconciliation".

**Note for the writer:** the corpus-provenance clause's "environment-anchored ground
truth" phrasing predates A30; the shipped framing is the three-construct taxonomy
(a30_construct_definitions.md). Reconcile the clause's wording with A30, not the
other way around.
