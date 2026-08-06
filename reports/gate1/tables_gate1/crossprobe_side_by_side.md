# Gate-1 Phase 5 — crossprobe AUROC, ensemble label vs environment label

Positive class = incorrect. `ensemble` is the published number. `ens@env` is the same 3-judge label restricted to the steps `y_env` can label, so `ens@env` -> `env_restricted` isolates the label change. `R3` flags any cell whose AUROC moves by more than 0.05 from `ensemble`.

| dataset | target | assessor | scope | ensemble | ensemble_on_env_support | env_restricted | env_full | n(env) | Δ vs ensemble | R3 |
|---|---|---|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | AGG-mean | 0.872 | 0.874 | 0.705 | 0.680 | 4492 | -0.167 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | AGG-true | 0.839 | 0.845 | 0.706 | 0.667 | 4492 | -0.134 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | SPLIT-action | 0.883 | 0.885 | 0.720 | 0.691 | 4492 | -0.163 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | SPLIT-thought | 0.796 | 0.800 | 0.672 | 0.636 | 4492 | -0.124 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.718 | 0.724 | 0.683 | 0.632 | 4492 | -0.035 |  |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | AGG-true | 0.671 | 0.680 | 0.723 | 0.638 | 4492 | +0.052 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.723 | 0.729 | 0.687 | 0.637 | 4492 | -0.037 |  |
| alfworld | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.696 | 0.704 | 0.683 | 0.627 | 4492 | -0.013 |  |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | AGG-mean | 0.601 | 0.604 | 0.699 | 0.639 | 4492 | +0.098 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | AGG-true | 0.548 | 0.548 | 0.662 | 0.612 | 4492 | +0.115 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | SPLIT-action | 0.584 | 0.589 | 0.692 | 0.628 | 4492 | +0.108 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | SPLIT-thought | 0.617 | 0.617 | 0.701 | 0.649 | 4492 | +0.084 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | AGG-mean | 0.883 | 0.881 | 0.723 | 0.707 | 4492 | -0.160 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | AGG-true | 0.877 | 0.875 | 0.719 | 0.702 | 4492 | -0.158 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | SPLIT-action | 0.893 | 0.893 | 0.747 | 0.719 | 4492 | -0.146 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | SPLIT-thought | 0.844 | 0.840 | 0.689 | 0.686 | 4492 | -0.155 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | AGG-mean | 0.524 | 0.525 | 0.613 | 0.584 | 4492 | +0.089 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | AGG-true | 0.498 | 0.499 | 0.605 | 0.573 | 4492 | +0.107 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | SPLIT-action | 0.555 | 0.560 | 0.632 | 0.591 | 4492 | +0.077 | **FLAG** |
| alfworld | Llama-3.3-70B-Instruct | gemma-3-4b-it | SPLIT-thought | 0.391 | 0.385 | 0.544 | 0.535 | 4492 | +0.153 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | AGG-mean | 0.836 | 0.836 | 0.747 | 0.736 | 6321 | -0.089 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | AGG-true | 0.831 | 0.830 | 0.754 | 0.741 | 6321 | -0.077 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | SPLIT-action | 0.868 | 0.868 | 0.793 | 0.776 | 6321 | -0.076 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | SPLIT-thought | 0.738 | 0.739 | 0.662 | 0.656 | 6321 | -0.076 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.611 | 0.614 | 0.637 | 0.585 | 6321 | +0.025 |  |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | AGG-true | 0.616 | 0.624 | 0.677 | 0.588 | 6321 | +0.061 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.608 | 0.613 | 0.670 | 0.598 | 6321 | +0.062 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.623 | 0.624 | 0.593 | 0.571 | 6321 | -0.030 |  |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | AGG-mean | 0.522 | 0.519 | 0.633 | 0.604 | 6321 | +0.110 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | AGG-true | 0.478 | 0.478 | 0.601 | 0.558 | 6321 | +0.123 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | SPLIT-action | 0.504 | 0.505 | 0.659 | 0.597 | 6321 | +0.155 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | SPLIT-thought | 0.553 | 0.544 | 0.583 | 0.594 | 6321 | +0.030 |  |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | AGG-mean | 0.821 | 0.819 | 0.779 | 0.749 | 6321 | -0.043 |  |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | AGG-true | 0.848 | 0.847 | 0.783 | 0.757 | 6321 | -0.065 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | SPLIT-action | 0.856 | 0.855 | 0.818 | 0.777 | 6321 | -0.039 |  |
| alfworld | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | SPLIT-thought | 0.735 | 0.732 | 0.683 | 0.676 | 6321 | -0.053 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | AGG-mean | 0.520 | 0.519 | 0.541 | 0.545 | 6321 | +0.021 |  |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | AGG-true | 0.421 | 0.422 | 0.548 | 0.516 | 6321 | +0.127 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | SPLIT-action | 0.541 | 0.543 | 0.595 | 0.567 | 6321 | +0.054 | **FLAG** |
| alfworld | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | SPLIT-thought | 0.471 | 0.462 | 0.456 | 0.521 | 6321 | -0.015 |  |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | AGG-mean | 0.783 | 0.782 | 0.574 | 0.590 | 6445 | -0.209 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | AGG-true | 0.797 | 0.798 | 0.638 | 0.626 | 6445 | -0.159 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | SPLIT-action | 0.823 | 0.822 | 0.642 | 0.641 | 6445 | -0.181 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | SPLIT-thought | 0.699 | 0.699 | 0.511 | 0.535 | 6452 | -0.189 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.594 | 0.596 | 0.554 | 0.517 | 6445 | -0.040 |  |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | AGG-true | 0.583 | 0.590 | 0.642 | 0.555 | 6445 | +0.059 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.599 | 0.603 | 0.597 | 0.542 | 6445 | -0.002 |  |
| alfworld | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.614 | 0.615 | 0.538 | 0.514 | 6452 | -0.076 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | AGG-mean | 0.501 | 0.505 | 0.608 | 0.553 | 6445 | +0.107 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | AGG-true | 0.475 | 0.480 | 0.558 | 0.519 | 6445 | +0.083 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | SPLIT-action | 0.483 | 0.489 | 0.617 | 0.559 | 6445 | +0.134 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Phi-4-mini-instruct | SPLIT-thought | 0.534 | 0.536 | 0.572 | 0.542 | 6452 | +0.038 |  |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | AGG-mean | 0.765 | 0.763 | 0.603 | 0.604 | 6445 | -0.162 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | AGG-true | 0.805 | 0.803 | 0.619 | 0.621 | 6445 | -0.186 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | SPLIT-action | 0.815 | 0.814 | 0.659 | 0.647 | 6445 | -0.156 | **FLAG** |
| alfworld | Phi-4-mini-instruct | Qwen3.6-35B-A3B | SPLIT-thought | 0.690 | 0.688 | 0.545 | 0.559 | 6452 | -0.145 | **FLAG** |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | AGG-mean | 0.507 | 0.509 | 0.525 | 0.514 | 6445 | +0.017 |  |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | AGG-true | 0.431 | 0.433 | 0.506 | 0.485 | 6445 | +0.075 | **FLAG** |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | SPLIT-action | 0.524 | 0.527 | 0.538 | 0.514 | 6445 | +0.015 |  |
| alfworld | Phi-4-mini-instruct | gemma-3-4b-it | SPLIT-thought | 0.474 | 0.469 | 0.493 | 0.530 | 6452 | +0.019 |  |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | AGG-mean | — | — | 0.768 | 0.744 | 3032 | — |  |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | SPLIT-action | — | — | 0.791 | 0.759 | 3032 | — |  |
| alfworld | Qwen3.5-27B | Qwen3.5-27B | SPLIT-thought | — | — | 0.773 | 0.752 | 3236 | — |  |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | AGG-mean | 0.653 | 0.653 | 0.664 | 0.648 | 3981 | +0.012 |  |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | AGG-true | 0.625 | 0.625 | 0.656 | 0.641 | 3981 | +0.031 |  |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | SPLIT-action | 0.657 | 0.658 | 0.680 | 0.660 | 3981 | +0.023 |  |
| alfworld | Qwen3.5-4B | Qwen3.5-4B | SPLIT-thought | 0.638 | 0.638 | 0.689 | 0.677 | 4470 | +0.051 | **FLAG** |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | AGG-mean | 0.710 | 0.707 | 0.658 | 0.647 | 4024 | -0.052 | **FLAG** |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | AGG-true | 0.672 | 0.667 | 0.657 | 0.640 | 4024 | -0.015 |  |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | SPLIT-action | 0.715 | 0.713 | 0.695 | 0.667 | 4024 | -0.020 |  |
| alfworld | Qwen3.5-9B | Qwen3.5-9B | SPLIT-thought | 0.695 | 0.692 | 0.669 | 0.666 | 4349 | -0.026 |  |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | AGG-mean | 0.815 | 0.816 | 0.682 | 0.674 | 3110 | -0.133 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | AGG-true | 0.757 | 0.758 | 0.687 | 0.678 | 3110 | -0.070 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | SPLIT-action | 0.823 | 0.824 | 0.698 | 0.689 | 3110 | -0.125 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | SPLIT-thought | 0.759 | 0.760 | 0.671 | 0.664 | 3252 | -0.088 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.622 | 0.626 | 0.665 | 0.642 | 3110 | +0.043 |  |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | AGG-true | 0.574 | 0.579 | 0.680 | 0.653 | 3110 | +0.107 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.627 | 0.632 | 0.683 | 0.658 | 3110 | +0.055 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.572 | 0.576 | 0.637 | 0.619 | 3252 | +0.065 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | AGG-mean | 0.540 | 0.539 | 0.681 | 0.667 | 3110 | +0.141 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | AGG-true | 0.448 | 0.448 | 0.608 | 0.600 | 3110 | +0.160 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | SPLIT-action | 0.573 | 0.574 | 0.719 | 0.702 | 3110 | +0.146 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Phi-4-mini-instruct | SPLIT-thought | 0.509 | 0.508 | 0.659 | 0.648 | 3252 | +0.150 | **FLAG** |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | AGG-mean | 0.708 | 0.708 | 0.718 | 0.705 | 3110 | +0.009 |  |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | AGG-true | 0.697 | 0.696 | 0.692 | 0.680 | 3110 | -0.005 |  |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | SPLIT-action | 0.702 | 0.701 | 0.728 | 0.714 | 3110 | +0.026 |  |
| alfworld | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | SPLIT-thought | 0.690 | 0.689 | 0.709 | 0.699 | 3252 | +0.020 |  |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | AGG-mean | 0.585 | 0.588 | 0.560 | 0.562 | 3110 | -0.025 |  |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | AGG-true | 0.571 | 0.574 | 0.538 | 0.534 | 3110 | -0.033 |  |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | SPLIT-action | 0.632 | 0.636 | 0.599 | 0.596 | 3110 | -0.032 |  |
| alfworld | Qwen3.6-35B-A3B | gemma-3-4b-it | SPLIT-thought | 0.411 | 0.409 | 0.480 | 0.490 | 3252 | +0.069 | **FLAG** |
| alfworld | deepseek-v4-flash | Llama-3.3-70B-Instruct | AGG-mean | 0.863 | 0.866 | 0.692 | 0.651 | 3016 | -0.172 | **FLAG** |
| alfworld | deepseek-v4-flash | Llama-3.3-70B-Instruct | AGG-true | 0.823 | 0.828 | 0.708 | 0.659 | 3016 | -0.115 | **FLAG** |
| alfworld | deepseek-v4-flash | Llama-3.3-70B-Instruct | SPLIT-action | 0.859 | 0.862 | 0.728 | 0.673 | 3016 | -0.131 | **FLAG** |
| alfworld | deepseek-v4-flash | Llama-3.3-70B-Instruct | SPLIT-thought | 0.812 | 0.816 | 0.649 | 0.617 | 3025 | -0.163 | **FLAG** |
| alfworld | deepseek-v4-flash | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.617 | 0.623 | 0.666 | 0.609 | 3016 | +0.049 |  |
| alfworld | deepseek-v4-flash | Mistral-7B-Instruct-v0.3 | AGG-true | 0.573 | 0.585 | 0.722 | 0.620 | 3016 | +0.149 | **FLAG** |
| alfworld | deepseek-v4-flash | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.632 | 0.640 | 0.688 | 0.619 | 3016 | +0.056 | **FLAG** |
| alfworld | deepseek-v4-flash | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.561 | 0.564 | 0.621 | 0.582 | 3025 | +0.060 | **FLAG** |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | AGG-mean | 0.538 | 0.539 | 0.736 | 0.656 | 3016 | +0.198 | **FLAG** |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | AGG-true | 0.483 | 0.487 | 0.685 | 0.621 | 3016 | +0.202 | **FLAG** |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | SPLIT-action | 0.545 | 0.551 | 0.761 | 0.666 | 3016 | +0.216 | **FLAG** |
| alfworld | deepseek-v4-flash | Phi-4-mini-instruct | SPLIT-thought | 0.532 | 0.531 | 0.713 | 0.647 | 3025 | +0.181 | **FLAG** |
| alfworld | deepseek-v4-flash | Qwen3.6-35B-A3B | AGG-mean | 0.854 | 0.852 | 0.745 | 0.701 | 3016 | -0.109 | **FLAG** |
| alfworld | deepseek-v4-flash | Qwen3.6-35B-A3B | AGG-true | 0.853 | 0.852 | 0.726 | 0.682 | 3016 | -0.127 | **FLAG** |
| alfworld | deepseek-v4-flash | Qwen3.6-35B-A3B | SPLIT-action | 0.849 | 0.849 | 0.778 | 0.716 | 3016 | -0.072 | **FLAG** |
| alfworld | deepseek-v4-flash | Qwen3.6-35B-A3B | SPLIT-thought | 0.830 | 0.826 | 0.699 | 0.675 | 3025 | -0.131 | **FLAG** |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | AGG-mean | 0.743 | 0.745 | 0.718 | 0.670 | 3016 | -0.025 |  |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | AGG-true | 0.720 | 0.728 | 0.713 | 0.619 | 2150 | -0.007 |  |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | SPLIT-action | 0.709 | 0.713 | 0.730 | 0.671 | 3016 | +0.021 |  |
| alfworld | deepseek-v4-flash | deepseek-v4-flash | SPLIT-thought | 0.760 | 0.761 | 0.703 | 0.663 | 3025 | -0.057 | **FLAG** |
| alfworld | deepseek-v4-flash | gemma-3-4b-it | AGG-mean | 0.495 | 0.499 | 0.551 | 0.537 | 3016 | +0.056 | **FLAG** |
| alfworld | deepseek-v4-flash | gemma-3-4b-it | AGG-true | 0.522 | 0.520 | 0.512 | 0.513 | 3016 | -0.010 |  |
| alfworld | deepseek-v4-flash | gemma-3-4b-it | SPLIT-action | 0.543 | 0.556 | 0.626 | 0.568 | 3016 | +0.083 | **FLAG** |
| alfworld | deepseek-v4-flash | gemma-3-4b-it | SPLIT-thought | 0.359 | 0.346 | 0.424 | 0.480 | 3025 | +0.065 | **FLAG** |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | AGG-mean | 0.847 | 0.845 | 0.652 | 0.675 | 6730 | -0.196 | **FLAG** |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | AGG-true | 0.865 | 0.863 | 0.679 | 0.697 | 6730 | -0.186 | **FLAG** |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | SPLIT-action | 0.891 | 0.890 | 0.697 | 0.713 | 6730 | -0.194 | **FLAG** |
| alfworld | gemma-3-4b-it | Llama-3.3-70B-Instruct | SPLIT-thought | 0.772 | 0.770 | 0.591 | 0.624 | 6730 | -0.181 | **FLAG** |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.666 | 0.668 | 0.628 | 0.602 | 6730 | -0.038 |  |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | AGG-true | 0.700 | 0.705 | 0.733 | 0.674 | 6730 | +0.033 |  |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.706 | 0.710 | 0.659 | 0.624 | 6730 | -0.047 |  |
| alfworld | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.653 | 0.654 | 0.657 | 0.625 | 6730 | +0.004 |  |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | AGG-mean | 0.611 | 0.613 | 0.640 | 0.599 | 6730 | +0.029 |  |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | AGG-true | 0.524 | 0.527 | 0.538 | 0.518 | 6730 | +0.013 |  |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | SPLIT-action | 0.615 | 0.617 | 0.635 | 0.609 | 6730 | +0.020 |  |
| alfworld | gemma-3-4b-it | Phi-4-mini-instruct | SPLIT-thought | 0.608 | 0.610 | 0.638 | 0.591 | 6730 | +0.030 |  |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | AGG-mean | 0.857 | 0.856 | 0.719 | 0.706 | 6730 | -0.138 | **FLAG** |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | AGG-true | 0.887 | 0.886 | 0.724 | 0.718 | 6730 | -0.163 | **FLAG** |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | SPLIT-action | 0.909 | 0.908 | 0.780 | 0.763 | 6730 | -0.129 | **FLAG** |
| alfworld | gemma-3-4b-it | Qwen3.6-35B-A3B | SPLIT-thought | 0.774 | 0.772 | 0.644 | 0.644 | 6730 | -0.129 | **FLAG** |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | AGG-mean | 0.559 | 0.561 | 0.522 | 0.519 | 6730 | -0.037 |  |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | AGG-true | 0.477 | 0.480 | 0.440 | 0.434 | 6730 | -0.037 |  |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | SPLIT-action | 0.642 | 0.646 | 0.612 | 0.584 | 6730 | -0.029 |  |
| alfworld | gemma-3-4b-it | gemma-3-4b-it | SPLIT-thought | 0.460 | 0.459 | 0.465 | 0.481 | 6730 | +0.006 |  |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | AGG-mean | 0.790 | 0.776 | 0.764 | 0.710 | 1163 | -0.026 |  |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | AGG-true | 0.820 | 0.801 | 0.804 | 0.726 | 1163 | -0.016 |  |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | SPLIT-action | 0.820 | 0.798 | 0.756 | 0.745 | 1163 | -0.064 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Llama-3.3-70B-Instruct | SPLIT-thought | 0.714 | 0.682 | 0.736 | 0.662 | 1163 | +0.022 |  |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.652 | 0.637 | 0.818 | 0.594 | 1163 | +0.165 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | AGG-true | 0.668 | 0.655 | 0.871 | 0.614 | 1163 | +0.203 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.714 | 0.677 | 0.793 | 0.636 | 1163 | +0.079 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.531 | 0.563 | 0.828 | 0.532 | 1163 | +0.296 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | AGG-mean | 0.693 | 0.654 | 0.871 | 0.666 | 1163 | +0.179 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | AGG-true | 0.677 | 0.652 | 0.884 | 0.640 | 1163 | +0.206 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | SPLIT-action | 0.719 | 0.681 | 0.839 | 0.670 | 1163 | +0.120 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Phi-4-mini-instruct | SPLIT-thought | 0.626 | 0.608 | 0.892 | 0.641 | 1163 | +0.266 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | AGG-mean | 0.810 | 0.767 | 0.824 | 0.726 | 1163 | +0.014 |  |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | AGG-true | 0.822 | 0.781 | 0.869 | 0.726 | 1163 | +0.047 |  |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | SPLIT-action | 0.829 | 0.788 | 0.854 | 0.743 | 1163 | +0.026 |  |
| hotpotqa | Llama-3.3-70B-Instruct | Qwen3.6-35B-A3B | SPLIT-thought | 0.748 | 0.709 | 0.754 | 0.682 | 1163 | +0.006 |  |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | AGG-mean | 0.603 | 0.534 | 0.428 | 0.574 | 1163 | -0.175 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | AGG-true | 0.646 | 0.657 | 0.683 | 0.577 | 1163 | +0.037 |  |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | SPLIT-action | 0.691 | 0.570 | 0.242 | 0.627 | 1163 | -0.449 | **FLAG** |
| hotpotqa | Llama-3.3-70B-Instruct | gemma-3-4b-it | SPLIT-thought | 0.551 | 0.563 | 0.715 | 0.523 | 1163 | +0.164 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | AGG-mean | 0.839 | 0.809 | 0.925 | 0.771 | 2375 | +0.086 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | AGG-true | 0.858 | 0.825 | 0.962 | 0.796 | 2375 | +0.104 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | SPLIT-action | 0.881 | 0.856 | 0.951 | 0.828 | 2375 | +0.070 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Llama-3.3-70B-Instruct | SPLIT-thought | 0.719 | 0.683 | 0.819 | 0.667 | 2375 | +0.100 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.602 | 0.571 | 0.904 | 0.592 | 2375 | +0.303 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | AGG-true | 0.668 | 0.634 | 0.932 | 0.643 | 2375 | +0.264 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.723 | 0.687 | 0.888 | 0.673 | 2375 | +0.166 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.528 | 0.500 | 0.887 | 0.552 | 2375 | +0.359 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | AGG-mean | 0.541 | 0.466 | 0.923 | 0.602 | 2375 | +0.381 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | AGG-true | 0.530 | 0.468 | 0.924 | 0.573 | 2375 | +0.394 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | SPLIT-action | 0.586 | 0.495 | 0.889 | 0.646 | 2375 | +0.303 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Phi-4-mini-instruct | SPLIT-thought | 0.502 | 0.452 | 0.934 | 0.557 | 2375 | +0.432 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | AGG-mean | 0.822 | 0.772 | 0.944 | 0.771 | 2375 | +0.121 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | AGG-true | 0.836 | 0.783 | 0.965 | 0.784 | 2375 | +0.129 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | SPLIT-action | 0.850 | 0.798 | 0.967 | 0.812 | 2375 | +0.116 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | Qwen3.6-35B-A3B | SPLIT-thought | 0.737 | 0.700 | 0.849 | 0.679 | 2375 | +0.112 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | AGG-mean | 0.590 | 0.551 | 0.553 | 0.576 | 2375 | -0.037 |  |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | AGG-true | 0.643 | 0.620 | 0.667 | 0.596 | 2375 | +0.024 |  |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | SPLIT-action | 0.696 | 0.627 | 0.251 | 0.662 | 2375 | -0.445 | **FLAG** |
| hotpotqa | Mistral-7B-Instruct-v0.3 | gemma-3-4b-it | SPLIT-thought | 0.564 | 0.544 | 0.808 | 0.553 | 2375 | +0.245 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | AGG-mean | 0.889 | 0.861 | 0.803 | 0.785 | 1885 | -0.086 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | AGG-true | 0.904 | 0.871 | 0.816 | 0.804 | 1885 | -0.088 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | SPLIT-action | 0.928 | 0.905 | 0.843 | 0.851 | 1885 | -0.085 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Llama-3.3-70B-Instruct | SPLIT-thought | 0.727 | 0.693 | 0.671 | 0.646 | 1885 | -0.056 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.620 | 0.603 | 0.724 | 0.583 | 1885 | +0.104 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | AGG-true | 0.676 | 0.664 | 0.840 | 0.611 | 1885 | +0.164 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.741 | 0.706 | 0.692 | 0.669 | 1885 | -0.049 |  |
| hotpotqa | Phi-4-mini-instruct | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.531 | 0.530 | 0.810 | 0.530 | 1885 | +0.279 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | AGG-mean | 0.576 | 0.535 | 0.835 | 0.599 | 1885 | +0.258 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | AGG-true | 0.550 | 0.533 | 0.863 | 0.554 | 1885 | +0.313 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | SPLIT-action | 0.616 | 0.557 | 0.760 | 0.631 | 1885 | +0.144 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Phi-4-mini-instruct | SPLIT-thought | 0.525 | 0.505 | 0.884 | 0.550 | 1885 | +0.358 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | AGG-mean | 0.867 | 0.808 | 0.832 | 0.772 | 1885 | -0.035 |  |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | AGG-true | 0.904 | 0.858 | 0.883 | 0.804 | 1885 | -0.020 |  |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | SPLIT-action | 0.922 | 0.880 | 0.911 | 0.834 | 1885 | -0.012 |  |
| hotpotqa | Phi-4-mini-instruct | Qwen3.6-35B-A3B | SPLIT-thought | 0.733 | 0.686 | 0.695 | 0.652 | 1885 | -0.038 |  |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | AGG-mean | 0.600 | 0.528 | 0.407 | 0.614 | 1885 | -0.194 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | AGG-true | 0.705 | 0.694 | 0.635 | 0.631 | 1885 | -0.070 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | SPLIT-action | 0.717 | 0.597 | 0.245 | 0.730 | 1885 | -0.472 | **FLAG** |
| hotpotqa | Phi-4-mini-instruct | gemma-3-4b-it | SPLIT-thought | 0.567 | 0.564 | 0.727 | 0.529 | 1885 | +0.161 | **FLAG** |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | AGG-mean | 0.803 | 0.755 | 0.873 | 0.757 | 1375 | +0.070 | **FLAG** |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | AGG-true | 0.792 | 0.748 | 0.857 | 0.754 | 1375 | +0.065 | **FLAG** |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | SPLIT-action | 0.815 | 0.771 | 0.831 | 0.798 | 1375 | +0.016 |  |
| hotpotqa | Qwen3.5-4B | Qwen3.5-4B | SPLIT-thought | 0.757 | 0.706 | 0.883 | 0.732 | 1483 | +0.126 | **FLAG** |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | AGG-mean | 0.793 | 0.734 | 0.888 | 0.772 | 1309 | +0.095 | **FLAG** |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | AGG-true | 0.813 | 0.759 | 0.860 | 0.782 | 1309 | +0.047 |  |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | SPLIT-action | 0.823 | 0.765 | 0.832 | 0.816 | 1309 | +0.009 |  |
| hotpotqa | Qwen3.5-9B | Qwen3.5-9B | SPLIT-thought | 0.750 | 0.687 | 0.894 | 0.746 | 1389 | +0.144 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | AGG-mean | 0.792 | 0.752 | 0.800 | 0.734 | 1114 | +0.008 |  |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | AGG-true | 0.816 | 0.785 | 0.860 | 0.741 | 1114 | +0.044 |  |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | SPLIT-action | 0.814 | 0.778 | 0.789 | 0.755 | 1114 | -0.025 |  |
| hotpotqa | Qwen3.6-35B-A3B | Llama-3.3-70B-Instruct | SPLIT-thought | 0.764 | 0.717 | 0.784 | 0.718 | 1156 | +0.020 |  |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.658 | 0.674 | 0.892 | 0.606 | 1114 | +0.233 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | AGG-true | 0.736 | 0.730 | 0.899 | 0.643 | 1114 | +0.163 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.769 | 0.744 | 0.862 | 0.677 | 1114 | +0.094 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.547 | 0.605 | 0.873 | 0.554 | 1156 | +0.326 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | AGG-mean | 0.625 | 0.627 | 0.914 | 0.649 | 1114 | +0.289 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | AGG-true | 0.592 | 0.617 | 0.915 | 0.617 | 1114 | +0.323 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | SPLIT-action | 0.651 | 0.631 | 0.894 | 0.678 | 1114 | +0.243 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Phi-4-mini-instruct | SPLIT-thought | 0.607 | 0.632 | 0.924 | 0.616 | 1156 | +0.316 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | AGG-mean | 0.838 | 0.776 | 0.865 | 0.782 | 1114 | +0.027 |  |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | AGG-true | 0.842 | 0.782 | 0.883 | 0.781 | 1114 | +0.040 |  |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | SPLIT-action | 0.836 | 0.767 | 0.863 | 0.805 | 1114 | +0.027 |  |
| hotpotqa | Qwen3.6-35B-A3B | Qwen3.6-35B-A3B | SPLIT-thought | 0.810 | 0.752 | 0.843 | 0.754 | 1156 | +0.033 |  |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | AGG-mean | 0.530 | 0.536 | 0.556 | 0.524 | 1114 | +0.026 |  |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | AGG-true | 0.676 | 0.696 | 0.754 | 0.583 | 1114 | +0.078 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | SPLIT-action | 0.663 | 0.544 | 0.187 | 0.617 | 1114 | -0.476 | **FLAG** |
| hotpotqa | Qwen3.6-35B-A3B | gemma-3-4b-it | SPLIT-thought | 0.522 | 0.600 | 0.853 | 0.522 | 1156 | +0.330 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | AGG-mean | 0.910 | 0.890 | 0.818 | 0.820 | 1658 | -0.092 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | AGG-true | 0.910 | 0.891 | 0.825 | 0.816 | 1658 | -0.085 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | SPLIT-action | 0.931 | 0.922 | 0.832 | 0.848 | 1658 | -0.099 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Llama-3.3-70B-Instruct | SPLIT-thought | 0.828 | 0.796 | 0.749 | 0.758 | 1658 | -0.079 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | AGG-mean | 0.651 | 0.671 | 0.878 | 0.603 | 1658 | +0.227 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | AGG-true | 0.704 | 0.722 | 0.907 | 0.639 | 1658 | +0.203 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | SPLIT-action | 0.749 | 0.749 | 0.863 | 0.673 | 1658 | +0.114 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Mistral-7B-Instruct-v0.3 | SPLIT-thought | 0.570 | 0.601 | 0.848 | 0.552 | 1658 | +0.278 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | AGG-mean | 0.624 | 0.602 | 0.925 | 0.645 | 1658 | +0.301 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | AGG-true | 0.586 | 0.583 | 0.942 | 0.601 | 1658 | +0.356 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | SPLIT-action | 0.644 | 0.600 | 0.881 | 0.661 | 1658 | +0.237 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Phi-4-mini-instruct | SPLIT-thought | 0.594 | 0.602 | 0.946 | 0.619 | 1658 | +0.351 | **FLAG** |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | AGG-mean | 0.906 | 0.880 | 0.910 | 0.815 | 1658 | +0.004 |  |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | AGG-true | 0.916 | 0.895 | 0.911 | 0.810 | 1658 | -0.006 |  |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | SPLIT-action | 0.927 | 0.905 | 0.922 | 0.837 | 1658 | -0.005 |  |
| hotpotqa | gemma-3-4b-it | Qwen3.6-35B-A3B | SPLIT-thought | 0.836 | 0.808 | 0.856 | 0.757 | 1658 | +0.020 |  |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | AGG-mean | 0.616 | 0.577 | 0.634 | 0.603 | 1658 | +0.019 |  |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | AGG-true | 0.725 | 0.740 | 0.798 | 0.651 | 1658 | +0.073 | **FLAG** |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | SPLIT-action | 0.714 | 0.602 | 0.328 | 0.682 | 1658 | -0.387 | **FLAG** |
| hotpotqa | gemma-3-4b-it | gemma-3-4b-it | SPLIT-thought | 0.603 | 0.623 | 0.841 | 0.579 | 1658 | +0.238 | **FLAG** |

**R3: 161 of 243 cells move by more than 0.05.**
