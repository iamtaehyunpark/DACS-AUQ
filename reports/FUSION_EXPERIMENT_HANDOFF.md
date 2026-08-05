# Handoff: Training-Free Fusion of Decoupled Thought and Action Uncertainty

## Status and execution rule

This document is an execution protocol, not authorization to immediately run a
large sweep.

The first assignment is **Phase 0 only: repository, data, and figure research**.
Inspect the current repository and return a discovery report plus the questions
listed below. Do not finalize paths, schemas, metric pairs, split definitions,
or grids until the report has been discussed with the user. Do not generate new
trajectories or overwrite existing results during Phase 0.

Existing work may be dirty or untracked. Preserve it. In particular, inspect
existing fusion scripts and outputs as prior work, but do not assume that they
define the approved experiment. The final experiment must exclude methods that
fit supervised predictive models.

## Objective

On **decoupled data only**, determine which training-free transformation and
fusion rule best combines:

- thought uncertainty, \(U_T\); and
- action uncertainty, \(U_A\)

for predicting step/task failure.

The study must address two related questions:

1. Which normalization–fusion combination gives the strongest held-out failure
   ranking and failure/success decision performance?
2. Is there a thought/action contribution ratio that generalizes across models
   and datasets, rather than merely optimizing one corpus?

The mandatory unsplit baseline is:

- **AGG-true P(True):** generate/evaluate the response without splitting it into
  thought and action, treat it as a single response, and emit one P(True)
  uncertainty score.

Verify whether stored AGG-true values are P(True), P(False), or an already
converted uncertainty \(U=1-P(\mathrm{True})\). All evaluation scores must be
oriented so that a larger value means greater predicted failure risk.

## Scope

### Included

- Decoupled trajectories and their existing thought-stage and action-stage
  uncertainty scores.
- Same-metric pairs, such as P(True) thought + P(True) action.
- Cross-metric pairs, if the Phase 0 audit shows that they are aligned,
  sufficiently complete, and scientifically interpretable.
- Formula-based fusion rules.
- Unlabeled reference-statistic transformations, fitted inside the appropriate
  training fold.
- Grid selection of a small number of formula parameters.

### Excluded

- Entangled data as experimental observations. Entangled files may be inspected
  only to understand repository organization or prevent accidental mixing.
- Logistic regression, isotonic calibration, beta calibration, splines, GAMs,
  density estimation, copulas, trees, boosting, neural networks, learned gates,
  learned Choquet capacities, stacking, and ranking-loss training.
- Any fusion model fitted directly to labels.
- Test-fold polarity selection, normalization, threshold fitting, or parameter
  selection.
- New data generation unless Phase 0 establishes that required artifacts are
  missing and the user separately approves generation.

Grid-searching \(\lambda,\gamma,p,\eta,\delta,\kappa\), or fixed Choquet
capacities on inner validation data is allowed. These are formula parameters,
not fitted predictive models, but they still require nested evaluation to avoid
optimistic reporting.

---

# Phase 0 — Mandatory repository and data research

## 0.1 Map the repository

Locate and report:

1. The authoritative decoupled trajectory files.
2. Thought/action probe files and their schemas.
3. AGG-true P(True) files and the script/prompt that created them.
4. Judge labels, task-completion labels, and any soft vote fields.
5. Model, dataset, run, task, trajectory, step, and action-type identifiers.
6. Existing analysis scripts, fusion scripts, result tables, plots, and figure
   generation scripts.
7. Which artifacts are authoritative, partial, smoke-test, legacy, rerun,
   duplicated, or currently unfinished.
8. The current Git state. Do not modify or delete unrelated dirty files.

Likely starting points currently visible in the repository include:

- `react_validation/result/`
- `react_validation/analysis/`
- `react_validation/fusion_sweep.py`
- `react_validation/table0_trajectory_bridge_v2.py`
- `react_validation/table1_step_auroc_v2.py`
- `v1/data/`
- `v1/src/analysis/`
- `v1/uq_experiments.md`

These are leads, not pre-decided authoritative paths.

## 0.2 Audit the data

Produce a compact inventory table with one row per model × dataset × decoupled
run. At minimum report:

- number of trajectories/tasks;
- number of steps;
- number and prevalence of success/failure labels;
- label source and whether it is hard, soft, or vote-derived;
- available thought metrics;
- available action metrics;
- AGG-true P(True) availability;
- count and rate of missing values for every score;
- intersection count for each feasible thought/action pair;
- duplicate keys;
- unmatched probe/judge/trajectory keys;
- parse failures, degenerate steps, retries, or exclusion flags;
- whether terminal steps are included;
- score direction and theoretical range;
- empirical minimum, maximum, median, IQR, and important quantiles.

Confirm the unique join key. It will probably include model/run, task or
trajectory ID, and step index, but do not assume this.

Check whether AGG-true was evaluated on exactly the same response, step, judge
label, and sample population as the decoupled scores. If it is not directly
paired, document the mismatch before proposing comparisons.

## 0.3 Research existing tables and figures

Inventory every relevant existing table and figure:

- file path;
- generating script;
- source data;
- model/dataset/run represented;
- filtering and exclusion rules;
- metric polarity;
- whether values are in-sample or held out;
- whether the artifact is reproducible from current data.

Open and visually inspect existing plots rather than relying only on filenames.
Report what each plot implies about:

- differences between thought and action score ranges;
- saturation, spikes, clipping, or round-number behavior;
- separation between completed and failed tasks;
- tail behavior;
- correlation and disagreement between \(U_T\) and \(U_A\);
- model/dataset distribution shift;
- missing or suspicious regions.

## 0.4 Produce discovery plots if missing

Phase 0 may create new read-only diagnostic outputs in a new, clearly named
directory, without altering source data. Prefer plots faceted by model and
dataset.

Required diagnostics:

1. Histograms/KDEs of every thought and action score, split by outcome.
2. ECDFs of thought versus action scores.
3. Conditional task-failure/completion rate versus score quantile.
4. Thought–action joint scatter/hexbin plots colored by failure rate.
5. Difference and disagreement distributions:
   \(U_T-U_A\) and \(|U_T-U_A|\).
6. Thought/action rank correlation overall and by outcome.
7. Single-score AUROC with trajectory-level confidence intervals.
8. Missingness and pairwise-availability matrix.
9. AGG-true P(True) distribution and outcome separation.
10. Per-model and per-dataset range/quantile comparison.

Do not interpret a smoothed calibration curve as a deployable trained
calibrator. It is descriptive only.

## 0.5 Phase 0 deliverable and stop point

Return:

1. `DISCOVERY_REPORT.md`
2. An artifact/data map.
3. A schema and join-key summary.
4. A figure inventory with thumbnails or links.
5. The diagnostic plots above, where missing.
6. A list of feasible thought/action metric pairs with sample counts.
7. A proposed final experiment matrix and estimated number of evaluations.
8. Explicit answers—or evidence that an answer is unavailable—to the questions
   below.

Then stop and discuss the findings with the user before implementing Phase 1.

### Questions to resolve after discovery

1. Which files/runs are the authoritative decoupled datasets?
2. What is the primary target: hard judge failure, soft vote-derived failure,
   terminal task completion, or more than one?
3. What is the evaluation unit: step, episode, or both?
4. Which model × dataset combinations define a domain?
5. Is normalization using the unlabeled distribution of a held-out target
   domain permitted, or must all reference statistics come from source domains?
6. Should the metric-pair search include the full thought-metric ×
   action-metric cross-product, only same-metric pairs, or a preselected subset?
7. Is AGG-true P(True) directly aligned with every decoupled example?
8. Is the primary goal a single global formula/ratio, or is a small
   model-conditioned table acceptable?
9. Which failure/success operating cost or coverage level matters, if any?
10. Are any exclusions from existing analysis already pre-registered?

---

# Phase 1 — Candidate experiment after approval

Phase 1 must be adapted to the findings and user decisions from Phase 0.

## 1.1 Mandatory baselines

Evaluate on matched examples:

- **B0:** AGG-true P(True), converted to failure uncertainty if necessary.
- **B1:** thought score alone.
- **B2:** action score alone.
- **B3:** current/reference 50:50 fusion, including the currently used Noisy-OR
  definition exactly as implemented.
- **B4:** raw 50:50 arithmetic mean.

For every paired merger, B1 and B2 must be recomputed on the exact same
complete-case population. Also report their performance on their full available
populations as secondary coverage diagnostics.

## 1.2 Retained score representations

### N0 — Raw

Use the original score after a documented direction correction. Only
\([0,1]\)-valued inputs may be passed to probability/fuzzy operators.

### N1 — Source-specific percentile

\[
q_T=F_T(U_T),\qquad q_A=F_A(U_A)
\]

Fit each empirical CDF on the inner-training/reference portion only. Apply it
unchanged to validation/test data. Use a documented rule for values outside the
training range and for ties.

### N2 — Gaussian quantile

\[
z_i=\Phi^{-1}(\operatorname{clip}(q_i,\epsilon,1-\epsilon))
\]

Use a fixed \(\epsilon\), proposed after inspecting sample sizes.

### N3 — Robust standardized

\[
z_i=\frac{U_i-\operatorname{median}(U_i)}
{\operatorname{IQR}(U_i)}
\]

Estimate median and IQR on the inner-training/reference portion only. Specify a
fallback for zero IQR.

### N4 — Baseline-centered log odds

Use only for genuine probability-valued scores:

\[
e_i=\operatorname{logit}(p_i)-\operatorname{logit}(\pi)
\]

Clip probabilities using a predeclared \(\epsilon\). Estimate \(\pi\) from
training labels only. Do not apply this representation to entropy or arbitrary
unit-interval metrics.

## 1.3 Retained fusion families

### F1 — Weighted arithmetic

\[
s=\lambda x_T+(1-\lambda)x_A
\]

### F2 — Power mean

\[
s=\left[\lambda x_T^p+(1-\lambda)x_A^p\right]^{1/p}
\]

Use only for suitable nonnegative inputs. Handle \(p=0\) as the geometric-mean
limit.

### F3 — Ordered weighted average

\[
s=\eta\max(x_T,x_A)+(1-\eta)\min(x_T,x_A)
\]

This tests whether the higher warning should dominate independently of which
source produced it.

### F4 — Weighted Noisy-OR

\[
s=1-\left[(1-x_T)^{\gamma\lambda}
\cdot(1-x_A)^{\gamma(1-\lambda)}\right].
\]

Use only for \([0,1]\)-valued inputs. \(\lambda\) controls the thought/action
ratio; \(\gamma\) controls total evidence strength.

### F5 — Weighted prior-centered odds

\[
s=\sigma\left(
\operatorname{logit}(\pi)
+\gamma\lambda e_T
+\gamma(1-\lambda)e_A
\right)
\]

Use only when both components are genuine probability-derived evidence.

### F6 — Disagreement-aware additive fusion

\[
s=\lambda x_T+(1-\lambda)x_A+\delta|x_T-x_A|
\]

If Phase 0 shows direction-specific disagreement, include:

\[
s=\lambda x_T+(1-\lambda)x_A
+\delta_T\max(x_T-x_A,0)
+\delta_A\max(x_A-x_T,0).
\]

Only include the directional version if the descriptive evidence and sample
size justify its additional parameters.

### F7 — Interaction/synergy fusion

\[
s=\lambda x_T+(1-\lambda)x_A+\kappa x_Tx_A
\]

Evaluate the unclipped score for ranking. Clip only when a bounded display score
is explicitly required.

### F8 — Asymmetric two-source Choquet

\[
s=
\begin{cases}
x_A+(x_T-x_A)g_T,&x_T\ge x_A,\\
x_T+(x_A-x_T)g_A,&x_A>x_T.
\end{cases}
\]

Use fixed grid-searched capacities only; do not fit a learned fuzzy measure.

## 1.4 Initial parameter grids

These are starting proposals and must be reconsidered after Phase 0:

- \(\lambda\in\{0,0.05,\ldots,1\}\)
- \(\gamma\in\{0.25,0.5,1,2,4\}\)
- \(p\in\{-4,-2,-1,0,1,2,4,8\}\)
- \(\eta\in\{0,0.1,\ldots,1\}\)
- \(\delta,\kappa\in\{-1,-0.5,-0.25,0,0.25,0.5,1\}\)
- \(g_T,g_A\in\{0,0.1,\ldots,1\}\)

Prune grids when formulas duplicate endpoints of other families. Do not expand
the grid after seeing outer-test results.

## 1.5 Valid representation–fusion pairings

| Representation | Permitted fusion families |
|---|---|
| Raw \([0,1]\) | F1, F2, F3, F4, F7, F8 |
| Percentile \([0,1]\) | F1, F2, F3, F4, F7, F8 |
| Gaussian quantile | F1, F3, F6, F7 |
| Robust standardized | F1, F3, F6, F7 |
| Centered log odds | F1, F5, F6, F7 |

Do not blindly take a Cartesian product across invalid pairings.

---

# Phase 2 — Honest selection and generalization test

## 2.1 Split unit

No trajectory/task may span training, validation, and test partitions.

Use one immutable split manifest shared by every method. Include a hash of the
manifest in outputs. If multiple steps belong to one trajectory, group by
trajectory at every resampling level.

## 2.2 Preferred evaluation hierarchy

If there are enough model × dataset domains:

1. Outer loop: leave one complete domain out.
2. Inner loop: grouped cross-validation on the remaining trajectories/domains.
3. Select metric pair, representation, fusion family, parameters, and decision
   threshold using inner data only.
4. Freeze the full pipeline and evaluate once on the outer domain.

Also perform leave-one-model-out and leave-one-dataset-out evaluation when the
number of domains permits.

If there are too few domains, use nested grouped cross-validation by trajectory
and clearly label the result as in-domain generalization rather than
cross-model/dataset generalization.

## 2.3 Finding a generalized ratio

For each outer split, choose one shared \(\lambda\) on inner data by macro
averaging performance across training domains:

\[
\lambda^*=
\arg\max_\lambda
\frac{1}{D_{\mathrm{train}}}
\sum_d \mathrm{AUROC}_d(\lambda).
\]

Report:

- selected \(\lambda\) in every outer split;
- median and IQR of selected \(\lambda\);
- AUROC-versus-\(\lambda\) curves by domain;
- performance of the global \(\lambda\);
- each domain's oracle \(\lambda\), clearly marked descriptive and optimistic;
- transfer regret:

\[
\mathrm{regret}_d=
\mathrm{AUROC}_d(\lambda^{\mathrm{oracle}}_d)
-\mathrm{AUROC}_d(\lambda^{\mathrm{global}}).
\]

A generalized ratio is supported only if it is stable across outer splits and
has low transfer regret. Do not infer universality merely from the average of
per-domain oracle ratios.

## 2.4 Missing-data fairness

- Primary paired comparisons use the identical complete-case population.
- Never impute a missing thought/action score.
- Report retained sample count and coverage for every method.
- Report single-source full-coverage results separately.
- If AGG-true has a different population, provide both its full-population
  result and a matched-subset result; do not compare unmatched values as if
  paired.

## 2.5 Polarity

Set polarity from the metric definition wherever possible. For example:

- convert P(True) success probability into \(1-P(\mathrm{True})\);
- preserve uncertainty scores whose documented direction is already
  failure-positive.

If a metric's direction is genuinely ambiguous, resolve it inside inner
training data only and report that this occurred. Never auto-flip from outer
test performance.

---

# Outcomes and statistical reporting

## Primary outcome

- Held-out AUROC for failure ranking.

Macro-average across domains so that a large dataset does not dominate the
generalized-method decision.

## Secondary outcomes

- AUPRC, with failure as the positive class.
- Balanced accuracy for failure/success division.
- MCC.
- Sensitivity, specificity, precision, and F1.
- Failure rate at fixed coverage, if the user selects a target coverage.
- Risk–coverage/AURC if abstention is an intended use.

Select classification thresholds on inner validation data only. The default
threshold objective, unless replaced after discussion, is maximum balanced
accuracy. Apply the frozen threshold to the outer test fold.

Report Brier score, log loss, and calibration plots only for outputs with a
defensible probability interpretation. Do not report percentile, Gaussian
quantile, robust-z, or arbitrary interaction scores as calibrated
probabilities.

## Uncertainty intervals and comparisons

- Bootstrap at the trajectory level, not the step level.
- Use paired bootstrap deltas because methods are evaluated on matched examples.
- Provide 95% confidence intervals for:
  - each method;
  - improvement over AGG-true P(True);
  - improvement over the best single-stage baseline;
  - improvement over the current 50:50 Noisy-OR.
- Report domain-level values, macro average, and worst-domain performance.
- Do not declare a winner from a tiny numerical difference with an overlapping
  paired interval.

## Winner rule

Choose the final method in this order:

1. Highest outer-held-out macro AUROC.
2. Must not materially reduce worst-domain AUROC relative to the best simple
   baseline.
3. Use AUPRC and balanced accuracy as tie-breakers.
4. If performance is statistically indistinguishable, choose the lower-parameter
   formula.
5. A method is considered a meaningful fusion improvement only if its paired
   interval versus both the best single-stage score and AGG-true excludes zero,
   or if the user approves a predeclared practical-effect threshold instead.

---

# Required outputs

## Tables

1. Data and score availability audit.
2. Single-score baselines.
3. Full matched comparison against AGG-true P(True), thought-only,
   action-only, and current 50:50 Noisy-OR.
4. Normalization × fusion macro performance.
5. Per-model and per-dataset results.
6. Selected hyperparameters and ratios by outer split.
7. Coverage/missingness table.
8. Thresholded failure/success metrics.

## Figures

1. Thought/action distributions before normalization.
2. Conditional failure rate versus source-specific score quantile.
3. Joint thought/action failure-rate map.
4. AUROC heatmap for valid normalization–fusion combinations.
5. AUROC-versus-\(\lambda\) curves by domain.
6. Global-ratio transfer-regret plot.
7. Paired improvement forest plot against baselines.
8. Risk–coverage curves for finalists, if applicable.
9. Decision-boundary or score-surface plots for the top formulas.

Every table and figure must include the data scope, number of trajectories and
steps, split level, score direction, and whether results are inner-validation,
outer-test, or descriptive.

## Reproducibility

- Use deterministic split and bootstrap seeds.
- Save the split manifest and hashes.
- Save exact parameter grids and selected parameters.
- Record source-file paths and hashes.
- Create outputs in a new experiment directory; do not overwrite prior results.
- Add tests for joins, polarity, normalization leakage, formula boundaries, and
  matched-population evaluation.
- Verify that empirical normalization is fitted only on the allowed reference
  portion of each fold.
- Make one command reproduce the final tables and figures from existing scored
  data.

## Final execution report

The final report must answer:

1. Does any decoupled thought/action fusion outperform AGG-true P(True)?
2. Does fusion outperform both thought-only and action-only uncertainty?
3. Which normalization is most transferable?
4. Which fusion family wins, and is the gain robust across domains?
5. What thought/action ratio generalizes best?
6. How much regret does a global ratio incur versus domain-specific oracle
   ratios?
7. Does thought/action disagreement contribute useful information?
8. Are gains due to normalization, fusion geometry, metric-pair choice, or all
   three?
9. Does the winner improve practical failure/success division, not just AUROC?
10. What limitations follow from missingness, label quality, domain count, and
    AGG-true alignment?
