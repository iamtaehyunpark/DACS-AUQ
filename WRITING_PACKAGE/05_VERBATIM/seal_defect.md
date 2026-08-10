# GATE-4 seal-defect disclosure (h-noself)
**Source: `GATE4_SUMMARY.md` §Forecast lock (verbatim). Debt 11: ship as-is.**

> **Defect in the seal, disclosed:** both sealed variants are in fact **h-noself**. The
> reference set is read from `crossprobe/<ds>/<target>/`, and the cross-probe pipeline
> skips the diagonal, so the judge's own cell was never present to be dropped. GATE-3's
> h **did** include self-cells. The h-primary forecast was therefore never sealed, and it
> cannot be sealed now that outcomes are visible. Everything below is a validation of
> **h-noself** — a registered A34.1 variant, so this is a real result, but it is not the
> h-with-self that GATE-3 validated.

Lock block (same section, for the appendix):

| | |
|---|---|
| lock commit | `5a4938fd841a823c1023e10c7383fe20fde9cec8` |
| lock timestamp | 2026-08-10T09:12:40+09:00 |
| `forecasts_A34.csv` sha256 | `69b926a0a70608ed77d24515d3421645c59f016c3ac168535a4674cf2091156c` |
| forecasts sealed | 20 (10 cells × 2 variants) |
| evaluation run | after the lock commit |

> The seal was computed by a code path (`gate4_partA.py --seal`) that is **never handed a
> label file**. The lock is therefore structural, not a promise: the function that
> produced π̂ cannot read an outcome.
