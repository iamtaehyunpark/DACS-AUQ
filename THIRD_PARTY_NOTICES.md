# Third-party notices

## ReAct

This repository contains code and prompts adapted or migrated from [ysymyth/ReAct](https://github.com/ysymyth/ReAct), recorded in the source as upstream revision `6bdb3a1`.

These include the baseline agent loops in `src/react_alfworld.py` and `src/react_hotpotqa.py`, `src/wikienv.py`, `src/wrappers.py`, `src/base_config.yaml`, and upstream-derived examples in `src/prompts/`. The source files describe changes to model backends, API compatibility, and instrumentation.

ReAct is distributed under the MIT License, copyright (c) 2023 Shunyu Yao. The complete upstream notice is preserved in [docs/licenses/ReAct-MIT.txt](docs/licenses/ReAct-MIT.txt).

## Benchmarks and models

The simplified HotpotQA development file in `src/data/` was distributed through the ReAct repository. HotpotQA's dataset terms and the terms for its underlying Wikipedia content apply independently. See the [HotpotQA project](https://hotpotqa.github.io/) for dataset provenance.

ALFWorld data, model checkpoints, and hosted API services are obtained separately and remain subject to their respective terms. This repository does not distribute model weights.

## Original work

No additional license grant for the original paper or original research code is declared by this cleanup. The third-party license above applies to the corresponding upstream-derived materials.
