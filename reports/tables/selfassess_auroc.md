# Self-assessment AUROC per (dataset x model)

Step-level soft AUROC vs the 3-judge ensemble, positive class = incorrect.
**Judge-anchored, therefore provisional** until gate-1 recomputation.

Confidence-valued signals (c-hat, separate verbalized, post-hoc numeric) are
negated so that every row shares the 'higher = more uncertain' convention.
AUROC below 0.5 means the signal is anti-correlated with error; reported as-is
rather than flipped, because a consistently inverted metric is a finding.

## Best metric per cell

| dataset | model | metric | scope | n | AUROC |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | ptrue | SPLIT-action | 4765 | 0.883 |
| alfworld | Mistral-7B-Instruct-v0.3 | chat_ingen | AGG-true | 6480 | 0.657 |
| alfworld | Phi-4-mini-instruct | chat_ingen | AGG-true | 6604 | 0.622 |
| alfworld | Qwen3.6-35B-A3B | ptrue | AGG-mean | 3197 | 0.708 |
| alfworld | deepseek-v4-flash | SP | SPLIT-thought | 3304 | 0.799 |
| alfworld | gemma-3-4b-it | ptrue | SPLIT-action | 6790 | 0.642 |
| hotpotqa | Llama-3.3-70B-Instruct | ptrue | AGG-true | 2530 | 0.820 |
| hotpotqa | Mistral-7B-Instruct-v0.3 | ptrue | SPLIT-action | 3224 | 0.723 |
| hotpotqa | Phi-4-mini-instruct | SP | SPLIT-thought | 2716 | 0.622 |
| hotpotqa | Qwen3.6-35B-A3B | ptrue | AGG-true | 2192 | 0.842 |
| hotpotqa | gemma-3-4b-it | ptrue | AGG-true | 2565 | 0.725 |

## alfworld / Llama-3.3-70B-Instruct

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | ptrue | SPLIT-action | 4765 | 0.883 | — |
| 2 | ptrue | AGG-mean | 4765 | 0.872 | — |
| 3 | ptrue | AGG-true | 4765 | 0.839 | — |
| 4 | ptrue | SPLIT-thought | 4765 | 0.796 | — |
| 5 | SP | SPLIT-thought | 4765 | 0.743 | — |
| 6 | MaxTE | SPLIT-thought | 4765 | 0.695 | — |
| 7 | MTE | SPLIT-thought | 4765 | 0.694 | — |
| 8 | PPL | SPLIT-thought | 4765 | 0.685 | — |
| 9 | MTE | AGG-mean | 4765 | 0.681 | — |
| 10 | PPL | AGG-mean | 4765 | 0.676 | — |
| 11 | MaxTE | AGG-mean | 4765 | 0.663 | — |
| 12 | SP | AGG-mean | 4765 | 0.531 | — |
| 13 | MTE | SPLIT-action | 4765 | 0.516 | — |
| 14 | PPL | SPLIT-action | 4765 | 0.510 | — |
| 15 | SP | SPLIT-action | 4765 | 0.507 | — |
| 16 | MaxTE | SPLIT-action | 4765 | 0.506 | — |
| 17 | targeted_posthoc | SPLIT-thought | 4765 | 0.480 | — |
| 18 | chat_ingen | AGG-true | 4765 | 0.401 | — |
| 19 | posthoc_num | SPLIT-thought | 4765 | 0.358 | — |
| 20 | sep_verbalized | SPLIT-thought | 4765 | 0.303 | — |
| 21 | posthoc_num | SPLIT-action | 4764 | 0.286 | — |
| 22 | sep_verbalized | SPLIT-action | 4765 | 0.286 | — |
| 23 | posthoc_num | AGG-mean | 4764 | 0.266 | — |
| 24 | sep_verbalized | AGG-mean | 4765 | 0.249 | — |

## alfworld / Mistral-7B-Instruct-v0.3

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | chat_ingen | AGG-true | 6480 | 0.657 | — |
| 2 | ptrue | SPLIT-thought | 6482 | 0.623 | — |
| 3 | ptrue | AGG-true | 6482 | 0.616 | — |
| 4 | ptrue | AGG-mean | 6482 | 0.611 | — |
| 5 | ptrue | SPLIT-action | 6482 | 0.608 | — |
| 6 | sep_verbalized | SPLIT-action | 6482 | 0.599 | — |
| 7 | MaxTE | SPLIT-action | 6482 | 0.587 | — |
| 8 | SP | AGG-mean | 6482 | 0.584 | — |
| 9 | SP | SPLIT-action | 6482 | 0.584 | — |
| 10 | sep_verbalized | AGG-mean | 6482 | 0.577 | — |
| 11 | posthoc_num | SPLIT-action | 6482 | 0.576 | — |
| 12 | targeted_posthoc | SPLIT-thought | 6482 | 0.569 | — |
| 13 | MaxTE | AGG-mean | 6482 | 0.564 | — |
| 14 | PPL | SPLIT-action | 6482 | 0.562 | — |
| 15 | MTE | SPLIT-action | 6482 | 0.555 | — |
| 16 | sep_verbalized | SPLIT-thought | 6482 | 0.550 | — |
| 17 | posthoc_num | AGG-mean | 6482 | 0.546 | — |
| 18 | posthoc_num | SPLIT-thought | 6482 | 0.535 | — |
| 19 | SP | SPLIT-thought | 6482 | 0.520 | — |
| 20 | MaxTE | SPLIT-thought | 6482 | 0.503 | — |
| 21 | MTE | AGG-mean | 6482 | 0.490 | — |
| 22 | PPL | AGG-mean | 6482 | 0.489 | — |
| 23 | PPL | SPLIT-thought | 6482 | 0.465 | — |
| 24 | MTE | SPLIT-thought | 6482 | 0.458 | — |

## alfworld / Phi-4-mini-instruct

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | chat_ingen | AGG-true | 6604 | 0.622 | — |
| 2 | sep_verbalized | SPLIT-action | 6604 | 0.574 | — |
| 3 | posthoc_num | SPLIT-action | 6577 | 0.574 | — |
| 4 | posthoc_num | AGG-mean | 6566 | 0.570 | — |
| 5 | ptrue | SPLIT-thought | 6604 | 0.534 | — |
| 6 | sep_verbalized | AGG-mean | 6604 | 0.534 | — |
| 7 | posthoc_num | SPLIT-thought | 6588 | 0.522 | — |
| 8 | MaxTE | SPLIT-thought | 6604 | 0.515 | — |
| 9 | sep_verbalized | SPLIT-thought | 6604 | 0.505 | — |
| 10 | ptrue | AGG-mean | 6604 | 0.501 | — |
| 11 | SP | SPLIT-thought | 6604 | 0.499 | — |
| 12 | MaxTE | AGG-mean | 6604 | 0.494 | — |
| 13 | MaxTE | SPLIT-action | 6604 | 0.491 | — |
| 14 | SP | AGG-mean | 6604 | 0.487 | — |
| 15 | SP | SPLIT-action | 6604 | 0.487 | — |
| 16 | ptrue | SPLIT-action | 6604 | 0.483 | — |
| 17 | PPL | SPLIT-action | 6604 | 0.481 | — |
| 18 | ptrue | AGG-true | 6604 | 0.475 | — |
| 19 | MTE | SPLIT-action | 6604 | 0.474 | — |
| 20 | PPL | SPLIT-thought | 6604 | 0.465 | — |
| 21 | PPL | AGG-mean | 6604 | 0.462 | — |
| 22 | MTE | SPLIT-thought | 6604 | 0.452 | — |
| 23 | MTE | AGG-mean | 6604 | 0.450 | — |
| 24 | targeted_posthoc | SPLIT-thought | 6604 | 0.449 | — |

## alfworld / Qwen3.6-35B-A3B

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | ptrue | AGG-mean | 3197 | 0.708 | — |
| 2 | ptrue | SPLIT-action | 3197 | 0.702 | — |
| 3 | ptrue | AGG-true | 3197 | 0.697 | — |
| 4 | MaxTE | AGG-mean | 3200 | 0.693 | — |
| 5 | ptrue | SPLIT-thought | 3197 | 0.690 | — |
| 6 | MaxTE | SPLIT-thought | 3200 | 0.679 | — |
| 7 | MTE | AGG-mean | 3200 | 0.662 | — |
| 8 | PPL | AGG-mean | 3200 | 0.656 | — |
| 9 | SP | SPLIT-thought | 3200 | 0.645 | — |
| 10 | MTE | SPLIT-thought | 3200 | 0.631 | — |
| 11 | PPL | SPLIT-thought | 3200 | 0.628 | — |
| 12 | chat_ingen | AGG-true | 2806 | 0.578 | — |
| 13 | MTE | SPLIT-action | 3200 | 0.566 | — |
| 14 | PPL | SPLIT-action | 3200 | 0.562 | — |
| 15 | SP | AGG-mean | 3200 | 0.561 | — |
| 16 | SP | SPLIT-action | 3200 | 0.559 | — |
| 17 | MaxTE | SPLIT-action | 3200 | 0.555 | — |
| 18 | posthoc_num | SPLIT-action | 3192 | 0.554 | — |
| 19 | posthoc_num | AGG-mean | 3192 | 0.536 | — |
| 20 | posthoc_num | SPLIT-thought | 3197 | 0.530 | — |
| 21 | targeted_posthoc | SPLIT-thought | 3197 | 0.428 | — |
| 22 | sep_verbalized | SPLIT-thought | 3197 | 0.399 | — |
| 23 | sep_verbalized | SPLIT-action | 3197 | 0.390 | — |
| 24 | sep_verbalized | AGG-mean | 3197 | 0.362 | — |

## alfworld / deepseek-v4-flash

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | SP | SPLIT-thought | 3304 | 0.799 | — |
| 2 | ptrue | SPLIT-thought | 3304 | 0.760 | — |
| 3 | MTE | AGG-mean | 3304 | 0.743 | — |
| 4 | ptrue | AGG-mean | 3304 | 0.743 | — |
| 5 | MaxTE | SPLIT-thought | 3304 | 0.740 | — |
| 6 | PPL | AGG-mean | 3304 | 0.730 | — |
| 7 | MTE | SPLIT-thought | 3304 | 0.726 | — |
| 8 | MaxTE | AGG-mean | 3304 | 0.722 | — |
| 9 | ptrue | AGG-true | 2322 | 0.720 | — |
| 10 | PPL | SPLIT-thought | 3304 | 0.711 | — |
| 11 | ptrue | SPLIT-action | 3304 | 0.709 | — |
| 12 | MTE | SPLIT-action | 3304 | 0.652 | — |
| 13 | PPL | SPLIT-action | 3304 | 0.642 | — |
| 14 | SP | AGG-mean | 3304 | 0.638 | — |
| 15 | SP | SPLIT-action | 3304 | 0.633 | — |
| 16 | MaxTE | SPLIT-action | 3304 | 0.627 | — |
| 17 | chat_ingen | AGG-true | 3303 | 0.573 | — |

## alfworld / gemma-3-4b-it

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | ptrue | SPLIT-action | 6790 | 0.642 | — |
| 2 | posthoc_num | SPLIT-action | 6790 | 0.589 | — |
| 3 | sep_verbalized | SPLIT-action | 6790 | 0.565 | — |
| 4 | sep_verbalized | AGG-mean | 6790 | 0.563 | — |
| 5 | posthoc_num | AGG-mean | 6790 | 0.562 | — |
| 6 | ptrue | AGG-mean | 6790 | 0.559 | — |
| 7 | targeted_posthoc | SPLIT-thought | 6790 | 0.558 | — |
| 8 | sep_verbalized | SPLIT-thought | 6790 | 0.551 | — |
| 9 | posthoc_num | SPLIT-thought | 6790 | 0.515 | — |
| 10 | SP | SPLIT-thought | 6790 | 0.514 | — |
| 11 | MaxTE | SPLIT-thought | 6790 | 0.498 | — |
| 12 | ptrue | AGG-true | 6790 | 0.477 | — |
| 13 | MTE | SPLIT-thought | 6790 | 0.475 | — |
| 14 | PPL | SPLIT-thought | 6790 | 0.468 | — |
| 15 | chat_ingen | AGG-true | 2813 | 0.464 | — |
| 16 | MaxTE | AGG-mean | 6790 | 0.460 | — |
| 17 | ptrue | SPLIT-thought | 6790 | 0.460 | — |
| 18 | SP | SPLIT-action | 6790 | 0.452 | — |
| 19 | MaxTE | SPLIT-action | 6790 | 0.451 | — |
| 20 | SP | AGG-mean | 6790 | 0.450 | — |
| 21 | MTE | SPLIT-action | 6790 | 0.449 | — |
| 22 | PPL | SPLIT-action | 6790 | 0.448 | — |
| 23 | MTE | AGG-mean | 6790 | 0.448 | — |
| 24 | PPL | AGG-mean | 6790 | 0.445 | — |

## hotpotqa / Llama-3.3-70B-Instruct

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | ptrue | AGG-true | 2530 | 0.820 | — |
| 2 | ptrue | SPLIT-action | 2530 | 0.820 | — |
| 3 | ptrue | AGG-mean | 2530 | 0.790 | — |
| 4 | MTE | SPLIT-action | 2530 | 0.721 | — |
| 5 | ptrue | SPLIT-thought | 2530 | 0.714 | — |
| 6 | PPL | SPLIT-action | 2530 | 0.708 | — |
| 7 | SP | AGG-mean | 2530 | 0.703 | — |
| 8 | SP | SPLIT-action | 2530 | 0.702 | — |
| 9 | MaxTE | SPLIT-action | 2530 | 0.701 | — |
| 10 | MaxTE | AGG-mean | 2530 | 0.665 | — |
| 11 | MTE | AGG-mean | 2530 | 0.659 | — |
| 12 | PPL | AGG-mean | 2530 | 0.622 | — |
| 13 | SP | SPLIT-thought | 2530 | 0.595 | — |
| 14 | MaxTE | SPLIT-thought | 2530 | 0.557 | — |
| 15 | PPL | SPLIT-thought | 2530 | 0.514 | — |
| 16 | MTE | SPLIT-thought | 2530 | 0.513 | — |
| 17 | posthoc_num | SPLIT-thought | 2530 | 0.305 | — |
| 18 | chat_ingen | AGG-true | 2529 | 0.304 | — |
| 19 | sep_verbalized | SPLIT-thought | 2530 | 0.295 | — |
| 20 | posthoc_num | SPLIT-action | 2530 | 0.279 | — |
| 21 | posthoc_num | AGG-mean | 2530 | 0.267 | — |
| 22 | sep_verbalized | SPLIT-action | 2530 | 0.261 | — |
| 23 | sep_verbalized | AGG-mean | 2530 | 0.253 | — |

## hotpotqa / Mistral-7B-Instruct-v0.3

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | ptrue | SPLIT-action | 3224 | 0.723 | — |
| 2 | ptrue | AGG-true | 3224 | 0.668 | — |
| 3 | SP | SPLIT-thought | 3224 | 0.608 | — |
| 4 | ptrue | AGG-mean | 3224 | 0.602 | — |
| 5 | MaxTE | SPLIT-thought | 3224 | 0.580 | — |
| 6 | MaxTE | AGG-mean | 3224 | 0.567 | — |
| 7 | SP | AGG-mean | 3224 | 0.547 | — |
| 8 | SP | SPLIT-action | 3224 | 0.546 | — |
| 9 | MaxTE | SPLIT-action | 3224 | 0.541 | — |
| 10 | MTE | AGG-mean | 3224 | 0.540 | — |
| 11 | MTE | SPLIT-thought | 3224 | 0.535 | — |
| 12 | PPL | AGG-mean | 3224 | 0.530 | — |
| 13 | ptrue | SPLIT-thought | 3224 | 0.528 | — |
| 14 | PPL | SPLIT-thought | 3224 | 0.527 | — |
| 15 | MTE | SPLIT-action | 3224 | 0.522 | — |
| 16 | PPL | SPLIT-action | 3224 | 0.521 | — |
| 17 | chat_ingen | AGG-true | 3224 | 0.421 | — |
| 18 | sep_verbalized | SPLIT-thought | 3224 | 0.417 | — |
| 19 | sep_verbalized | SPLIT-action | 3216 | 0.400 | — |
| 20 | sep_verbalized | AGG-mean | 3216 | 0.397 | — |
| 21 | posthoc_num | SPLIT-thought | 3224 | 0.384 | — |
| 22 | posthoc_num | SPLIT-action | 3224 | 0.372 | — |
| 23 | posthoc_num | AGG-mean | 3224 | 0.363 | — |

## hotpotqa / Phi-4-mini-instruct

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | SP | SPLIT-thought | 2716 | 0.622 | — |
| 2 | ptrue | SPLIT-action | 2716 | 0.616 | — |
| 3 | MTE | AGG-mean | 2716 | 0.616 | — |
| 4 | MTE | SPLIT-thought | 2716 | 0.612 | — |
| 5 | PPL | AGG-mean | 2716 | 0.610 | — |
| 6 | PPL | SPLIT-thought | 2716 | 0.609 | — |
| 7 | MaxTE | SPLIT-thought | 2716 | 0.600 | — |
| 8 | MaxTE | AGG-mean | 2716 | 0.584 | — |
| 9 | ptrue | AGG-mean | 2716 | 0.576 | — |
| 10 | MTE | SPLIT-action | 2716 | 0.569 | — |
| 11 | SP | SPLIT-action | 2716 | 0.558 | — |
| 12 | SP | AGG-mean | 2716 | 0.558 | — |
| 13 | PPL | SPLIT-action | 2716 | 0.554 | — |
| 14 | MaxTE | SPLIT-action | 2716 | 0.552 | — |
| 15 | ptrue | AGG-true | 2716 | 0.550 | — |
| 16 | ptrue | SPLIT-thought | 2716 | 0.525 | — |
| 17 | posthoc_num | SPLIT-action | 2714 | 0.465 | — |
| 18 | posthoc_num | SPLIT-thought | 2713 | 0.452 | — |
| 19 | posthoc_num | AGG-mean | 2711 | 0.436 | — |
| 20 | chat_ingen | AGG-true | 2713 | 0.435 | — |
| 21 | sep_verbalized | SPLIT-thought | 2716 | 0.416 | — |
| 22 | sep_verbalized | SPLIT-action | 2716 | 0.404 | — |
| 23 | sep_verbalized | AGG-mean | 2716 | 0.403 | — |

## hotpotqa / Qwen3.6-35B-A3B

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | ptrue | AGG-true | 2192 | 0.842 | — |
| 2 | ptrue | AGG-mean | 2192 | 0.838 | — |
| 3 | ptrue | SPLIT-action | 2192 | 0.836 | — |
| 4 | ptrue | SPLIT-thought | 2192 | 0.810 | — |
| 5 | MTE | AGG-mean | 2193 | 0.770 | — |
| 6 | MaxTE | AGG-mean | 2193 | 0.763 | — |
| 7 | SP | SPLIT-thought | 2193 | 0.760 | — |
| 8 | PPL | AGG-mean | 2193 | 0.757 | — |
| 9 | MTE | SPLIT-thought | 2193 | 0.748 | — |
| 10 | MaxTE | SPLIT-thought | 2193 | 0.744 | — |
| 11 | PPL | SPLIT-thought | 2193 | 0.743 | — |
| 12 | MTE | SPLIT-action | 2193 | 0.706 | — |
| 13 | SP | AGG-mean | 2193 | 0.703 | — |
| 14 | SP | SPLIT-action | 2193 | 0.701 | — |
| 15 | MaxTE | SPLIT-action | 2193 | 0.699 | — |
| 16 | PPL | SPLIT-action | 2193 | 0.698 | — |
| 17 | posthoc_num | SPLIT-thought | 2191 | 0.257 | — |
| 18 | chat_ingen | AGG-true | 2160 | 0.255 | — |
| 19 | posthoc_num | SPLIT-action | 2191 | 0.252 | — |
| 20 | posthoc_num | AGG-mean | 2191 | 0.225 | — |
| 21 | sep_verbalized | SPLIT-thought | 2192 | 0.220 | — |
| 22 | sep_verbalized | SPLIT-action | 2192 | 0.202 | — |
| 23 | sep_verbalized | AGG-mean | 2192 | 0.189 | — |

## hotpotqa / gemma-3-4b-it

| rank | metric | scope | n | AUROC | 95% CI |
|---|---|---|---|---|---|
| 1 | ptrue | AGG-true | 2565 | 0.725 | — |
| 2 | ptrue | SPLIT-action | 2565 | 0.714 | — |
| 3 | SP | SPLIT-thought | 2565 | 0.691 | — |
| 4 | MTE | SPLIT-thought | 2565 | 0.654 | — |
| 5 | PPL | SPLIT-thought | 2565 | 0.650 | — |
| 6 | MaxTE | SPLIT-thought | 2565 | 0.635 | — |
| 7 | PPL | AGG-mean | 2565 | 0.635 | — |
| 8 | MTE | AGG-mean | 2565 | 0.630 | — |
| 9 | ptrue | AGG-mean | 2565 | 0.616 | — |
| 10 | ptrue | SPLIT-thought | 2565 | 0.603 | — |
| 11 | MaxTE | AGG-mean | 2565 | 0.589 | — |
| 12 | SP | AGG-mean | 2565 | 0.476 | — |
| 13 | chat_ingen | AGG-true | 1102 | 0.404 | — |
| 14 | MaxTE | SPLIT-action | 2565 | 0.390 | — |
| 15 | SP | SPLIT-action | 2565 | 0.389 | — |
| 16 | MTE | SPLIT-action | 2565 | 0.386 | — |
| 17 | PPL | SPLIT-action | 2565 | 0.385 | — |
| 18 | sep_verbalized | SPLIT-action | 2565 | 0.377 | — |
| 19 | posthoc_num | SPLIT-thought | 2565 | 0.372 | — |
| 20 | sep_verbalized | SPLIT-thought | 2565 | 0.350 | — |
| 21 | sep_verbalized | AGG-mean | 2565 | 0.349 | — |
| 22 | posthoc_num | AGG-mean | 2565 | 0.346 | — |
| 23 | posthoc_num | SPLIT-action | 2565 | 0.330 | — |

