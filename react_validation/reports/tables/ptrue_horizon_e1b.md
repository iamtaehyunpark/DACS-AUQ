# P(True) hindsight-horizon sweep — does the SHAPE of U(k) carry extra information?

120 steps x 7 horizons (k=0..6). k=0 is the production prompt (causal, available online); k>=1 appends what actually followed and is available only where actions are reversible.

## Mean U by horizon, split by step label x trajectory outcome

| group | n | k=0 | k=1 | k=2 | k=3 | k=4 | k=5 | k=6 | ΔK = U_K − U_0 |
|---|---|---|---|---|---|---|---|---|---|
| INCORRECT step / episode FAILED | 30 | 0.517 | 0.623 | 0.661 | 0.678 | 0.743 | 0.738 | 0.767 | **0.250** |
| INCORRECT step / episode SUCCEEDED | 30 | 0.485 | 0.727 | 0.782 | 0.744 | 0.780 | 0.780 | 0.760 | **0.275** |
| correct step / episode FAILED | 30 | 0.337 | 0.416 | 0.549 | 0.578 | 0.571 | 0.616 | 0.645 | **0.308** |
| correct step / episode SUCCEEDED | 30 | 0.289 | 0.347 | 0.506 | 0.549 | 0.633 | 0.683 | 0.719 | **0.430** |

## Step-level discrimination at each horizon

AUROC for the judge's step label, using U_k alone. If this rises with k and then flattens, that flattening point is how much lookahead is worth buying.

| k | AUROC (step incorrect) [95% CI] | n |
|---|---|---|
| 0 | 0.688 [0.584, 0.785] | 120 |
| 1 | 0.783 [0.681, 0.876] | 120 |
| 2 | 0.740 [0.628, 0.841] | 120 |
| 3 | 0.691 [0.589, 0.789] | 120 |
| 4 | 0.742 [0.633, 0.834] | 120 |
| 5 | 0.683 [0.567, 0.788] | 120 |
| 6 | 0.650 [0.538, 0.757] | 120 |

## Trajectory outcome: does Δ beat U_0?

AUROC for *episode FAILED*, positive class = failed, computed over steps (clustered by episode). `U_0` is what an online probe sees; `ΔK` and `slope` are what the hindsight curve adds.

| predictor | AUROC (episode failed) [95% CI] |
|---|---|
| U_0 (online, instantaneous) | 0.535 [0.416, 0.651] |
| U_K (full hindsight) | 0.480 [0.374, 0.589] |
| ΔK = U_K − U_0 | 0.419 [0.305, 0.537] |
| slope of U over k | 0.434 [0.314, 0.561] |

## Conditioned on how the step looked at the time

Split the steps at the median U_0 — 'looked fine' vs 'looked doubtful' to an online probe — and ask whether Δ separates trajectory outcome WITHIN each half. That is the case for Δ as a cue: it would have to add something where U_0 alone is ambiguous.

| U_0 half | n | mean ΔK, episode SUCCEEDED | mean ΔK, episode FAILED | AUROC of ΔK for failure |
|---|---|---|---|---|
| looked fine (U_0 <= 0.34) | 60 | 0.516 | 0.397 | 0.337 [0.201, 0.477] |
| looked doubtful (U_0 > 0.34) | 60 | 0.178 | 0.168 | 0.482 [0.329, 0.634] |

_Caveat that applies to every number above: U_k for k>=1 is not causally available at step t. These measure whether the cue is worth paying for (reversible-action lookahead, or offline analysis), not a deployable online detector._
