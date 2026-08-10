# GATE-4 Parts B/C/D (Part A pending scoring pass)

Spec: `docs/specs/GATE4_SPEC_A34.md`. Construct **violation+judgment**, capable judges, per (judge, environment).

## Part B — conditional invariance

Criterion: median within-class between-target 1-Wasserstein < 1/3 of the class-separation distance. Self-cells excluded (positive control).

| env | judge | within-median | class-separation | ratio | CI supported |
|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6.375 | 7.880 | 0.809 | **no** |
| alfworld | Qwen3.6-35B-A3B | 1.239 | 3.404 | 0.364 | **no** |
| hotpotqa | Llama-3.3-70B-Instruct | 1.850 | 11.410 | 0.162 | **yes** |
| hotpotqa | Qwen3.6-35B-A3B | 0.585 | 3.869 | 0.151 | **yes** |

## Part C — fit stability (disclosure, not a gate)

Stable iff max jackknife swing <= 8 percentile points in >=3 of 4 fits.

| env | judge | targets | slope | slope 95% CI | max swing (pts) | median swing | stable | leverage |
|---|---|---|---|---|---|---|---|---|
| alfworld | Llama-3.3-70B-Instruct | 6 | -0.494 | [-0.618, -0.378] | 3.4 | 0.4 | **yes** | — |
| alfworld | Qwen3.6-35B-A3B | 6 | -0.620 | [-1.249, -0.258] | 11.7 | 1.0 | **no** | Qwen3.6-35B-A3B(11.7) |
| hotpotqa | Llama-3.3-70B-Instruct | 5 | -0.614 | [-0.670, -0.462] | 1.2 | 0.2 | **yes** | — |
| hotpotqa | Qwen3.6-35B-A3B | 5 | -0.522 | [-0.657, -0.477] | 1.0 | 0.1 | **yes** | — |

**3 of 4 fits stable** (criterion: >=3 of 4).

## Part D — cross-environment h (no success criterion; expected to degrade)

| judge | fit env | applied to | target | BA cross | BA within | delta |
|---|---|---|---|---|---|---|
| Llama-3.3-70B-Instruct | alfworld | hotpotqa | Llama-3.3-70B-Instruct | 0.823 | 0.828 | -0.005 |
| Llama-3.3-70B-Instruct | alfworld | hotpotqa | Mistral-7B-Instruct-v0.3 | 0.823 | 0.829 | -0.006 |
| Llama-3.3-70B-Instruct | alfworld | hotpotqa | Phi-4-mini-instruct | 0.857 | 0.863 | -0.006 |
| Llama-3.3-70B-Instruct | alfworld | hotpotqa | Qwen3.6-35B-A3B | 0.811 | 0.821 | -0.010 |
| Llama-3.3-70B-Instruct | alfworld | hotpotqa | gemma-3-4b-it | 0.856 | 0.866 | -0.009 |
| Qwen3.6-35B-A3B | alfworld | hotpotqa | Llama-3.3-70B-Instruct | 0.810 | 0.814 | -0.003 |
| Qwen3.6-35B-A3B | alfworld | hotpotqa | Mistral-7B-Instruct-v0.3 | 0.832 | 0.830 | +0.002 |
| Qwen3.6-35B-A3B | alfworld | hotpotqa | Phi-4-mini-instruct | 0.868 | 0.870 | -0.002 |
| Qwen3.6-35B-A3B | alfworld | hotpotqa | Qwen3.6-35B-A3B | 0.845 | 0.848 | -0.003 |
| Qwen3.6-35B-A3B | alfworld | hotpotqa | gemma-3-4b-it | 0.872 | 0.876 | -0.004 |
| Llama-3.3-70B-Instruct | hotpotqa | alfworld | Llama-3.3-70B-Instruct | 0.781 | 0.780 | +0.000 |
| Llama-3.3-70B-Instruct | hotpotqa | alfworld | Mistral-7B-Instruct-v0.3 | 0.787 | 0.787 | -0.001 |
| Llama-3.3-70B-Instruct | hotpotqa | alfworld | Phi-4-mini-instruct | 0.766 | 0.766 | +0.001 |
| Llama-3.3-70B-Instruct | hotpotqa | alfworld | Qwen3.6-35B-A3B | 0.678 | 0.691 | -0.012 |
| Llama-3.3-70B-Instruct | hotpotqa | alfworld | deepseek-v4-flash | 0.750 | 0.750 | -0.001 |
| Llama-3.3-70B-Instruct | hotpotqa | alfworld | gemma-3-4b-it | 0.804 | 0.803 | +0.000 |
| Qwen3.6-35B-A3B | hotpotqa | alfworld | Llama-3.3-70B-Instruct | 0.820 | 0.803 | +0.017 |
| Qwen3.6-35B-A3B | hotpotqa | alfworld | Mistral-7B-Instruct-v0.3 | 0.796 | 0.804 | -0.008 |
| Qwen3.6-35B-A3B | hotpotqa | alfworld | Phi-4-mini-instruct | 0.782 | 0.788 | -0.006 |
| Qwen3.6-35B-A3B | hotpotqa | alfworld | Qwen3.6-35B-A3B | 0.629 | 0.629 | +0.000 |
| Qwen3.6-35B-A3B | hotpotqa | alfworld | deepseek-v4-flash | 0.787 | 0.782 | +0.005 |
| Qwen3.6-35B-A3B | hotpotqa | alfworld | gemma-3-4b-it | 0.817 | 0.821 | -0.003 |

Mean cross-environment degradation **-0.002** balanced accuracy (min -0.012, max +0.017), over 22 cells. This number is the measured boundary of "per environment family" and goes verbatim into the limitations section.

