# Research code and setup

Start with the [artifact guide](RESULTS.md) for the scope of the saved results. The final PDF and source are available without installing anything.

## Offline checks

From the repository root:

```bash
python3 -m unittest discover -s tests -v
```

These tests use synthetic completions and environment responses. They exercise both HotpotQA acquisition arms, sampling, action grammar, real token-span helpers, logging, and output audits. They do not measure model quality or validate all final-paper results.

## Dependencies

Use a separate Python environment for research work. Python 3.10 or 3.11 is a reasonable starting point; this repository does not contain a fully pinned environment from the original runs.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The requirements file lists direct dependencies used by the retained Python code; installation and full experiment execution have not been validated on every platform. ALFWorld/TextWorld and GPU model serving are separate, heavier dependencies:

```bash
python -m pip install alfworld
alfworld-download
```

Set `ALFWORLD_DATA` to your environment-data directory. ALFWorld replay additionally uses TextWorld and its planner. Install vLLM in a compatible GPU serving environment if using the supplied serving script; the client environment can remain separate. Model weights must be obtained separately.

## Agent acquisition

The core entry points are:

| Task | Decoupled agent | Entangled agent |
| --- | --- | --- |
| ALFWorld | `src/chat_react.py` | `src/chat_react_entangled.py` |
| HotpotQA | `src/chat_react_hotpot.py` | `src/chat_react_hotpot_entangled.py` |

`src/run_probes.py` reads saved trajectories to extract post-hoc uncertainty signals. `src/judge_e0.py` and `src/judge_hotpot.py` acquire trajectory-based judge labels. Prompt files are in `src/prompts/`.

A generic model server can be started with:

```bash
bash scripts/serve.sh /path/to/model-checkpoint
```

The script serves the model as `qwen` on port 8000. Choose a checkpoint that supports the harness's chat-template settings, generation parameters, and token logprobs. Configure the matching client tokenizer explicitly:

```bash
export REACT_BASE_URL=http://localhost:8000/v1
export REACT_MODEL=qwen
export REACT_TOKENIZER=/path/to/model-checkpoint
```

For the complete HotpotQA pipeline, supply your own judge endpoint and credentials through the environment, or set `AZURE_JUDGE_ENV_FILE` to a local file that exports them. `JUDGE_MODELS` must name deployments available at that endpoint. Credentials are not included in the repository.

```bash
export AZURE_JUDGE_ENDPOINT=https://YOUR-RESOURCE.services.ai.azure.com/openai/v1
export AZURE_JUDGE_KEY=YOUR_LOCAL_KEY
# Set JUDGE_MODELS to the deployments available on your endpoint.
bash scripts/run_hotpot_acquisition.sh runs/hotpot_example 10
```

HotpotQA acquisition accesses live Wikipedia, so retrieval results can change. The pipeline uses the same sampled questions for both arms, audits the acquisition logs, then runs probes and judges. It refuses to append to existing output files. Inference and judge calls consume your compute or API quota.

For ALFWorld, run the chosen harness from `src/` with `REACT_UQLOG` set to an output JSONL path. Model endpoint, tokenizer, episode count, seed, and other options are documented at the top of each entry point. The `run_pilot.sh` / `run_validation.sh` scripts and their HotpotQA counterparts run the baseline ReAct track, not the instrumented acquisition track.

## Analysis

Most analysis entry points document their inputs in the module docstring and expose `--help`. Examples:

```bash
python analysis/s1_labels.py --help
python analysis/crossprobe_matrix_auroc.py --help
python analysis/gate2b_cut_transfer.py --help
python analysis/gate2b1_indexed_cut.py --help
```

The usual input layout is `result/pivot/<dataset>/<model>/`, containing agent trajectories, probes, and judge outputs. That raw tree is not included. Supply your own inputs with the relevant command's `--pivot`, label, and output arguments. Run output-producing analyses in a separate copy if you want to preserve the checked-in result snapshots.

The registered protocols are retained in `docs/specs/`, `docs/GATE2B_SPEC_A28.md`, `docs/GATE2B1_SPEC_A28_1.md`, and the root `GATE3_SPEC_A33.md`. The historical execution ledger remains in `runs/manifest.json`.

## Manuscript source

`manuscript/main.tex` and `manuscript/assets/` come from the final manuscript bundle. All local input and figure references are included; references are embedded in the TeX source. With a TeX distribution installed:

```bash
cd manuscript
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The source falls back to an article layout if the optional conference style is absent. It uses LaTeX's build date, so a new build can differ in date or layout from the supplied PDF. The original PDF is preserved unchanged at the repository root. A TeX compiler was unavailable during this cleanup; compilation has not been verified.
