# T2 — Independence deltas per construct, with CIs

**Caption-of-record.** Best-self vs best-external per arm (11 arms × 5 constructs = 55 rows), Δ = AUROC(best external) − AUROC(self), paired episode-clustered bootstrap CI. Positive Δ means the external judge reads the target better than the target reads itself. External beats self in 10/11 arms on violation, outcome, judgment and y_env, and 9/11 on violation+judgment; CIs exclude 0 in 7/8/10/7/10 arms respectively. The two primary-construct exceptions are the upward-probing cells (hotpotqa capable targets: Δ −0.0092 and −0.0183).

- Labels: L2 · constructs: all five · claim: C-indep
- assembled-from: `tables_S1/S1b_independence_L2_{violation,outcome,judgment,y_env,violation-judgment}.csv` (construct column prepended; no values altered)

Data: `T2_independence_deltas.csv` (55 rows; columns construct, dataset, target, best_external, self_auroc, ext_auroc, delta, ci_lo, ci_hi, n_ext, note).
