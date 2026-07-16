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

    paired = [r for r in labeled if r["probes"].get(DECISION_KEY) is not None
              and all(r["probes"].get(k) is not None for k in ENTROPY_KEYS)]
    delta = None
    if len(paired) >= 2:
        y = [_label(r) for r in paired]
        g = [r["task_id"] for r in paired]
        v = [r["probes"][DECISION_KEY] for r in paired]
        best = max(ENTROPY_KEYS,
                   key=lambda k: auroc([r["probes"][k] for r in paired], y))
        delta = {"best_entropy_probe": best, "n": len(paired),
                 **paired_auroc_delta(v, [r["probes"][best] for r in paired], y, g,
                                      n_boot=n_boot, seed=seed)}
    return {"probes": rows, "decision_delta": delta,
            "n_records": len(records), "n_labeled": len(labeled)}
