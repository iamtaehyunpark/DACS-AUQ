# S8_CRITERIA — qualification floors proposal (DECISION PACKAGE, then STOP)

**2026-08-08 · EXECUTION_HANDOVER v2 §2 · HALTED for author sign-off**

> **R1 FAILED as registered.** Gate-1's pre-registered qualification floors were not
> met: the lowest capable-judge *f* was 0.669 against a 0.70 floor, and the ordering
> inverted (Qwen 0.752 > Llama 0.669). Nothing below un-fails that gate. **Any floor
> set adopted here is a NEW registration**, not a revision of the old one, and it
> requires author sign-off before it is used to qualify anything.

## What changed since R1 was written

R1's floors were set on *f* under L1 ensemble labels, before the construct taxonomy
existed. Three things now bear on them:

- **Constructs decide verdicts.** S1d showed the same gate flips PASS/FAIL by
  construct (A28.1: PASS under `judgment`, FAIL under `violation+judgment`). A floor
  stated without a construct is not a floor.
- **h replaced g.** GATE-3 put the h-rule at capture 0.940 [0.796, 1.041], pass-rate
  20/22 [0.773, 1.000]. Floors expressed against g-era numbers no longer describe
  the deployed rule.
- **Frontier-ness is not the axis.** S5 resolved G2-R4: gpt-4o is *behind* the
  capable open judges (−0.030 primary construct) and ahead of the small tier
  (+0.138). Qualification should gate on measured capability, not on model class.

## Candidate floor sets

Each is stated per construct on the primary (`violation+judgment`) unless noted.
"Passes" is evaluated on the 22 capable-stratum cells plus the 34 non-capable ones.

### Set A — capability floor only (simplest)

| criterion | threshold |
|---|---|
| external AUROC on the target | ≥ 0.70 |
| measured on | primary construct, L2 labels |

**Passes:** both capable judges on every arm (Llama 0.70–0.90, Qwen 0.76–0.95).
**Fails:** all four non-capable judges on most arms (gemma/Phi/Mistral cluster
0.42–0.66).
**Cost:** one labelled evaluation per judge, reusable across targets.
**Weakness:** silent about *transfer*. A judge could clear 0.70 on the arms it was
measured on and still fail to place a cut on a new target.

### Set B — capability + transfer (matches what the paper actually claims)

| criterion | threshold |
|---|---|
| external AUROC on the target | ≥ 0.70, primary construct |
| h-rule pass-rate vs V | ≥ 80% of that judge's countable cells |
| h-rule pooled capture | ≥ 0.5 |

**Passes:** the capable stratum (h: 20/22 = 90.9%, capture 0.940).
**Fails:** the non-capable stratum outright.
**Weakness, stated:** the two h statistics are the ones S2/CI-top-up flagged as
`soften` — pass-rate 0.909 CI [0.773, 1.000] spans the 0.80 bar. A floor set at 80%
is being set at a value the data cannot separate from 77% or 100%.

### Set C — capability + transfer + construct stability (strictest)

Set B, plus: **the judge must clear the AUROC floor under BOTH `violation` and
`judgment` separately**, not only the composite.

**Passes:** Llama-70B and Qwen3.6-35B — but see the caveat below.
**Fails:** everything else, and it would have failed the g-rule era entirely.
**Rationale:** S1a shows construct-dependent AUROC (violation 0.785 vs judgment
0.717 mean). A judge strong only on violations detects gross failures and misses
subtle ones; C is the set that refuses to qualify it.

## What each set implies for the paper's roster

| judge | Set A | Set B | Set C |
|---|---|---|---|
| Llama-3.3-70B | qualifies | qualifies | qualifies |
| Qwen3.6-35B-A3B | qualifies | qualifies | qualifies* |
| gpt-4o (frontier) | qualifies | untested for transfer | untested |
| Mistral-7B / Phi-4-mini / gemma-3-4b | no | no | no |

\* Qwen3.6's ALFWorld fit is the one GATE-4 Part C flagged: 11.7 percentile points
of jackknife swing against an ±8 budget, with its own self-cell as the leverage
point. Under Set C that is a disclosure, not a disqualification — but the author
may reasonably decide it should be one.

## What is NOT proposed

No floor is proposed on *f* (gate-1's original quantity). R1 failed on it, the
ordering inverted under it, and no analysis since has rehabilitated it as a
qualification axis. Reusing it because it is the incumbent would be the wrong
reason.

No floor is proposed on frontier/API status. S5 measured that axis and it does not
predict quality.

## The decision

1. Adopt Set A, B, or C — or reject all three and leave qualification unspecified,
   which is a defensible outcome given R1's failure.
2. If adopting, acknowledge explicitly that this is a **new registration** and that
   the h-rule thresholds inside Sets B and C sit on statistics whose CIs span them.
3. Decide whether Qwen3.6's ALFWorld fit instability is a disclosure or a
   disqualification under Set C.

**Nothing downstream uses these floors until acked.** The final bundle's criteria
section stays empty and `OPEN_DECISIONS.md` carries this item.
