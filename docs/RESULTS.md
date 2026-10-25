# Supporting results and provenance

The final paper is [`paper.pdf`](../paper.pdf), dated August 26, 2026. Its matching manuscript bundle is in [`manuscript/`](../manuscript/). The bundled PDF was checked against the supplied paper byte for byte.

The code and saved results in this repository span multiple stages of the research. In particular, the August 10 writing registry and earlier gate results predate the final manuscript. Their counts, thresholds, and conclusions can differ from the paper. Use the final PDF for the paper's claims; use the artifacts below to inspect the recorded experiments. They are not a complete final-paper reproduction package.

## Artifact map

| Location | What it records |
| --- | --- |
| [`reports/gate1/`](../reports/gate1/) | Environment-anchored step labels, coverage, label-source audits, and input hashes |
| [`reports/tables/selfassess/`](../reports/tables/selfassess/) | Extracted per-step self-assessment metrics; the directory README describes columns and coverage |
| [`reports/tables/`](../reports/tables/) | Cross-probe matrices, uncertainty summaries, and score-versus-verdict comparisons |
| [`tables_S1/`](../tables_S1/) | Evaluation by label construct, including independence comparisons |
| [`tables_S2/`](../tables_S2/) and [`tables_bundle/`](../tables_bundle/) | Confidence intervals, label-source summaries, and the dated preliminary numbers registry |
| [`tables_S5/`](../tables_S5/) | Frontier-versus-open-estimator comparisons |
| [`tables_S7/`](../tables_S7/) and [`tables_P3/`](../tables_P3/) | Prequential calibration and label-source experiments |
| [`tables_gate3/`](../tables_gate3/) and [`tables_gate4/`](../tables_gate4/) | Registered threshold-transfer attempts and forecast diagnostics |
| [`figures/`](../figures/) | Saved figures and their supporting tabular data |
| [`experiment-records/`](experiment-records/) | Historical stage summaries, decisions, claim/evidence map, and gate ledger |
| [`../runs/manifest.json`](../runs/manifest.json) | Historical execution ledger, hashes, and recorded deviations |

The manuscript's final figure PDFs and typeset tables are in [`manuscript/assets/`](../manuscript/assets/). The August 10 registry in `tables_bundle/numbers_registry_2026-08-10.csv` is preserved for provenance; it is not an updated registry of every final-paper number.

## Labels and interpretation

`reports/gate1/labels_gate1.csv` and `.parquet` record step labels with provenance and coverage flags. Error labels use **1 = incorrect, 0 = correct**; missing labels must not be treated as correct. Read the [Gate 1 documentation](../reports/gate1/README.md) before using these files. Subsequent construct-specific analyses are implemented in `analysis/s1_labels.py`.

Reports distinguish ensemble-derived labels from environment-anchored labels. Construct choice and label pass affect comparisons; do not combine tables without checking these definitions. Historical failed or voided experiments remain documented in the experiment records.

## Availability boundaries

The checkout includes code, prompts, saved labels, extracted metrics, aggregate results, and manuscript assets. It does not include the large `result/` raw-log tree, model weights, ALFWorld's downloaded environments, or a locked runtime environment. Scripts requiring these inputs need them supplied separately. Some recorded paths refer to the original experiment server and are provenance, not portable defaults.

The supplied manuscript cites an anonymous artifact endpoint. That citation is preserved in the paper; its availability and completeness have not been verified as part of this cleanup.
