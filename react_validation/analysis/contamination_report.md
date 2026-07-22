# Contamination extraction — decoupled arm

The pilot's decoupled thought completions contain the committed action, so the post-hoc thought-stage probes were read off a thought that already reveals the decision. This re-runs `ptrue` and `posthoc_numeric` on a TRIMMED thought (trailing admissible-command line(s) dropped) with the pilot's exact prompt/seed/sampling, and pairs against the recorded full-thought U.

- Decoupled steps re-run: **702**
- Steps where a trailing command line was trimmed (`trimmed_bool=True`): **313** (44.6%)

`U` is uncertainty (higher = less confident). If conditioning on the committed action inflated confidence, the full-thought U is *lower* than the trimmed U, so signed `mean(U_full - U_trim)` is **negative** and `mean|ΔU|` is its magnitude.

## All paired steps

| probe | N paired | mean \|ΔU\| | mean signed (full−trim) | corr | mean U_full | mean U_trim |
|---|---:|---:|---:|---:|---:|---:|
| ptrue | 702 | 0.0354 | 0.0023 | 0.936 | 0.4188 | 0.4165 |
| posthoc_numeric | 702 | 0.0172 | -0.0050 | 0.931 | 0.1377 | 0.1427 |

## Split by trimmed_bool (was a command line actually removed?)

| probe | subset | N | mean \|ΔU\| | mean signed | corr |
|---|---|---:|---:|---:|---:|
| ptrue | trimmed=True | 313 | 0.0768 | 0.0045 | 0.793 |
| ptrue | trimmed=False | 389 | 0.0020 | 0.0005 | 1.000 |
| posthoc_numeric | trimmed=True | 313 | 0.0353 | -0.0104 | 0.728 |
| posthoc_numeric | trimmed=False | 389 | 0.0027 | -0.0006 | 0.993 |

## Parse-ok bookkeeping

| probe | N full parse_ok | N trim parse_ok | N both (used) |
|---|---:|---:|---:|
| ptrue | 702 | 702 | 702 |
| posthoc_numeric | 702 | 702 | 702 |

## Did the contamination matter?

- **ptrue**: mean|ΔU| = 0.0354 across all paired steps; on trimmed=True steps it is 0.0768 (larger than on trimmed=False, 0.0020). Signed shift on trimmed=True = 0.0045 (negative ⇒ full thought read as more confident).
- **posthoc_numeric**: mean|ΔU| = 0.0172 across all paired steps; on trimmed=True steps it is 0.0353 (larger than on trimmed=False, 0.0027). Signed shift on trimmed=True = -0.0104 (negative ⇒ full thought read as more confident).

