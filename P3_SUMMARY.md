# Priority-3 free stages — S7.1, bootstrap ladder, CI top-up

Spec: EXECUTION_HANDOVER v2 §3. Seed 13, 2000 draws, construct primary violation+judgment unless stated.

## S7.1 — prequential replay under h (and h-noself)

| variant | cells | mean batch BA | mean post-warm-up | mean penalty |
|---|---|---|---|---|
| h | 22 | 0.7986 | 0.7982 | -0.0004 |
| h-noself | 22 | 0.7982 | 0.7979 | -0.0003 |

## Bootstrap ladder — what each deployment tier costs and buys

| construct | tier | labels required | source | time to deploy | cells | mean BA | 95% CI |
|---|---|---|---|---|---|---|---|
| violation+judgment | day1_violation_calibrated | 0 human labels | environment emits automatically | immediate | 22 | 0.8012 | [0.7776, 0.8212] |
| violation+judgment | label_200_fitted | ~200 labelled episodes on the target | human or judge ensemble | one labelling round | 22 | 0.8083 | [0.7858, 0.8292] |
| violation+judgment | steady_state_h | 0 labels on the target | other targets of same judge x env | immediate once h exists | 22 | 0.7986 | [0.7719, 0.8228] |
| judgment | day1_violation_calibrated | 0 human labels | environment emits automatically | immediate | 22 | 0.8081 | [0.7867, 0.8259] |
| judgment | label_200_fitted | ~200 labelled episodes on the target | human or judge ensemble | one labelling round | 22 | 0.8162 | [0.7940, 0.8342] |
| judgment | steady_state_h | 0 labels on the target | other targets of same judge x env | immediate once h exists | 22 | 0.8068 | [0.7847, 0.8264] |
| violation | day1_violation_calibrated | 0 human labels | environment emits automatically | immediate | 22 | 0.8011 | [0.7616, 0.8423] |
| violation | label_200_fitted | ~200 labelled episodes on the target | human or judge ensemble | one labelling round | 22 | 0.8173 | [0.7755, 0.8607] |
| violation | steady_state_h | 0 labels on the target | other targets of same judge x env | immediate once h exists | 22 | 0.7984 | [0.7586, 0.8388] |
| outcome | day1_violation_calibrated | 0 human labels | environment emits automatically | immediate | 22 | 0.6717 | [0.6346, 0.7101] |
| outcome | label_200_fitted | ~200 labelled episodes on the target | human or judge ensemble | one labelling round | 22 | 0.7175 | [0.6767, 0.7621] |
| outcome | steady_state_h | 0 labels on the target | other targets of same judge x env | immediate once h exists | 22 | 0.6995 | [0.6616, 0.7391] |
| y_env | day1_violation_calibrated | 0 human labels | environment emits automatically | immediate | 22 | 0.6976 | [0.6658, 0.7314] |
| y_env | label_200_fitted | ~200 labelled episodes on the target | human or judge ensemble | one labelling round | 22 | 0.7422 | [0.7059, 0.7798] |
| y_env | steady_state_h | 0 labels on the target | other targets of same judge x env | immediate once h exists | 22 | 0.7270 | [0.6947, 0.7616] |

## CI top-up — GATE-3/4 headlines that lacked intervals

| claim | estimate | 95% CI | null | status |
|---|---|---|---|---|
| C-h-passrate — arm0_h_rule pass-rate vs V | 0.9091 | [0.7727, 1.0000] | 0.80 | **soften** |
| C-h-capture — arm0_h_rule pooled capture | 0.9394 | [0.7964, 1.0408] | 0.50 | **ok** |
| C-viol-passrate — arm2_violation pass-rate vs V | 0.8636 | [0.7273, 1.0000] | 0.80 | **soften** |
| C-viol-capture — arm2_violation pooled capture | 0.9685 | [0.8822, 1.0318] | 0.50 | **ok** |
| C-crossenv-h — cross-environment h degradation | -0.0024 | [-0.0047, 0.0001] | 0.00 | **soften** |

