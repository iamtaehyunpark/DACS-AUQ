# Cost-Effective Online Uncertainty Quantification for LLM Agents

### via a Single Characterized External Estimator

**[Read the paper (PDF)](paper.pdf)** · [Manuscript source](manuscript/) · [Research code and setup](docs/REPRODUCIBILITY.md) · [Supporting results](docs/RESULTS.md)

An external, frozen language model estimates whether an agent's next step should be trusted, using the task, interaction history, reasoning, and proposed action. This work studies step-level uncertainty in ALFWorld and HotpotQA, the limits of agents' self-assessment, and the transfer of decision thresholds across agents.

The paper evaluates 62,065 labelled steps from six model families and distinguishes three error constructs: violation, outcome, and judgment. It examines estimator capability, self-leniency, evidence requirements, and the cost of external estimation.

## Paper

The linked PDF is the supplied final manuscript, dated August 26, 2026 (24 pages). It retains its original anonymous review formatting. The LaTeX source and figure assets are included in [`manuscript/`](manuscript/).

For an application or reading list, use this direct paper link after pushing these changes:

**https://github.com/iamtaehyunpark/DACS-AUQ/blob/main/paper.pdf**

## Repository

| Path | Contents |
| --- | --- |
| [`src/`](src/) | Agent harnesses, uncertainty probes, judge protocols, prompts, and environment wrappers |
| [`analysis/`](analysis/) | Label construction, cross-agent evaluation, calibration, transfer, and diagnostic analyses |
| [`scripts/`](scripts/) | Model serving, baseline validation, and HotpotQA acquisition entry points |
| [`reports/`](reports/) | Supporting reports, step labels, extracted metrics, and evaluation tables |
| [`figures/`](figures/) and `tables_*/` | Saved research figures and tabular outputs |
| [`tests/`](tests/) | Offline acquisition contract tests |
| [`docs/`](docs/) | Setup, artifact guide, experiment records, and third-party notices |

The supporting artifacts include earlier experiment snapshots. The [artifact guide](docs/RESULTS.md) distinguishes these from the final manuscript. Large raw model outputs and checkpoints are not included, so this checkout alone does not reproduce every final-paper result.

## Quick check

Run the offline tests with Python, without model downloads, credentials, or GPU access:

```bash
python3 -m unittest discover -s tests -v
```

See the [reproducibility guide](docs/REPRODUCIBILITY.md) for dependencies and experiment entry points, and [third-party notices](THIRD_PARTY_NOTICES.md) for source and dataset attribution.
