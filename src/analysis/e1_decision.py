"""E1 decision-variable computation (E1★.4, REBOUND 2026-07-16 pre-data amendment):

    Delta = AUROC(U_T_verbalized) - AUROC(best entropy probe on the SAME steps)

per cell, trajectory-level paired bootstrap. The verbalized (in-generation) probe is the
ONLY decision variable; post-hoc probes appear as additional AUROC rows, never in Delta.
"Best entropy probe" is chosen WITHIN the cell (generous to the baseline).
"""
from __future__ import annotations

from src.analysis.bootstrap import bootstrap_ci, paired_auroc_delta
from src.analysis.discrimination import auroc, prr

ENTROPY_KEYS = ("thought_mte", "thought_ppl", "thought_sp")
DECISION_KEY = "U_T_verbalized"


def _label(r: dict) -> int | None:
    j = r["label"]["judge"]
    return None if j is None else (1 if j == "incorrect" else 0)


def cell_report(records: list[dict], *, n_boot: int = 10000, seed: int = 12345) -> dict:
    """AUROC/PRR per probe (verbalized, post-hoc rows, entropy family) + the decision Delta.
    Steps enter Delta only if the judge labeled them AND the verbalized probe parsed AND all
    entropy probes are present (identical-steps requirement of the paired comparison)."""
    rows: dict[str, dict] = {}
    labeled = [r for r in records if _label(r) is not None]

    for key in (DECISION_KEY, "U_T_posthoc_numeric", "U_T_posthoc_verbal",
                "U_T_posthoc_yesno") + ENTROPY_KEYS:
        pts = [(r["probes"][key], _label(r), r["task_id"]) for r in labeled
               if r["probes"].get(key) is not None]
        if len(pts) < 2:
            rows[key] = {"n": len(pts)}
            continue
        s, y, g = zip(*pts)
        rows[key] = {"n": len(pts),
                     "auroc": bootstrap_ci(s, y, g, auroc, n_boot=n_boot, seed=seed),
                     "prr": bootstrap_ci(s, y, g, prr, n_boot=n_boot, seed=seed)}

    def _delta(pool: list[dict]) -> dict | None:
        if len(pool) < 2:
            return None
        y = [_label(r) for r in pool]
        g = [r["task_id"] for r in pool]
        v = [r["probes"][DECISION_KEY] for r in pool]
        best = max(ENTROPY_KEYS, key=lambda k: auroc([r["probes"][k] for r in pool], y))
        return {"best_entropy_probe": best, "n": len(pool),
                **paired_auroc_delta(v, [r["probes"][best] for r in pool], y, g,
                                     n_boot=n_boot, seed=seed)}

    paired = [r for r in labeled if r["probes"].get(DECISION_KEY) is not None
              and all(r["probes"].get(k) is not None for k in ENTROPY_KEYS)]
    n_continued = sum(1 for r in paired if r["probes"].get(f"{DECISION_KEY}_continued"))
    natural_only = [r for r in paired if not r["probes"].get(f"{DECISION_KEY}_continued")]
    return {"probes": rows,
            "decision_delta": _delta(paired),
            # sensitivity: EOS-repaired steps excluded (spec §0.6 repair amendment)
            "decision_delta_natural_only": _delta(natural_only) if n_continued else None,
            "n_verbalized_continued": n_continued,
            "n_records": len(records), "n_labeled": len(labeled)}
