#!/usr/bin/env python3
"""Extract every self-assessment metric each model produces about its OWN steps, from
result/pivot, into one per-step table per cell.

This is the raw-value layer. No AUROC, no ranking, no labels-as-outcome — just the
metric scores, so that everything downstream (AUROC, transfer, invariance) reads from a
single extraction rather than each analysis re-deriving metrics from jsonl.

Metric definitions follow the earlier e1 suite so numbers stay comparable with what was
banked, but this is written for the pivot layout and imports nothing from it.

Token-level, over a stage span of the model's own generation logprobs:
  MTE    mean token entropy (over stored top-k, renormalised)
  MaxTE  max token entropy
  PPL    exp(-mean logprob)
  SP     1 - exp(sum logprob)          sequence improbability; higher = less likely
In-generation, emitted while acting:
  chat_ingen    U_verbalized            one blended confidence for the whole step
  uq_t_ingen    U_T_targeted_ingen      uq_a_ingen  U_A_targeted_ingen
Post-hoc probes over the frozen trajectory:
  ptrue · posthoc_num · targeted_posthoc · sep_verbalized

Columns are <metric>_T (thought), _A (action), _R (whole response), _J (joint/step-level).
Empty where a metric does not exist for that stage — e.g. AGG-true only exists for P(True),
which is the only signal with a genuine whole-response elicitation.

judge_correct_frac is carried alongside (fraction of the 3 judges voting CORRECT) so the
table is self-contained, but it is a LABEL, not a metric.

  selfassess_table.py [--pivot result/pivot] [--outdir reports/tables/selfassess]
"""
import argparse
import collections
import csv
import json
import math
import os

SPECIALS = ("</s>", "<s>", "<|endoftext|>", "<|eot_id|>", "<end_of_turn>", "<|im_end|>")

INGEN_FIELDS = {                       # uq step-record field -> (column stem, stage)
    "U_T_targeted_ingen": ("uq_t_ingen", "T"),
    "U_A_targeted_ingen": ("uq_a_ingen", "A"),
    "U_verbalized":       ("chat_ingen", "J"),
}
PROBE_STEMS = {                        # probe_kind -> column stem
    "ptrue": "ptrue",
    "posthoc_numeric": "posthoc_num",
    "targeted": "targeted_posthoc",
    "sep_verbalized": "sep_verbalized",
}
TOKEN_METRICS = ["MTE", "MaxTE", "PPL", "SP"]


def token_entropy(tok):
    """Entropy over the stored top-k alternatives, renormalised.

    Truncated at the run's top_logprobs (20), so biased low in absolute terms. Every arm
    uses the same k, so cross-arm comparison is unaffected; absolute values are not
    comparable to an untruncated entropy.
    """
    top = tok.get("top") or []
    if not top:
        return None
    ps = [math.exp(a["logprob"]) for a in top]
    Z = sum(ps)
    if Z <= 0:
        return None
    ps = [p / Z for p in ps]
    return -sum(p * math.log(p) for p in ps if p > 0)


def span_token_metrics(gen, span):
    """MTE / MaxTE / PPL / SP over a [lo,hi) token range. Indices are clamped: spans
    written before the whitespace fix can overrun gen, and those rows should degrade
    rather than crash."""
    if not gen or not span:
        return {}
    lo = max(0, min(span[0], len(gen)))
    hi = max(lo, min(span[1], len(gen)))
    toks = [t for t in gen[lo:hi]
            if not any(s in (t.get("token") or "") for s in SPECIALS)]
    lps = [t["logprob"] for t in toks if t.get("logprob") is not None]
    if not lps:
        return {}
    ents = [e for e in (token_entropy(t) for t in toks) if e is not None]
    out = {}
    if ents:
        out["MTE"] = sum(ents) / len(ents)
        out["MaxTE"] = max(ents)
    out["PPL"] = math.exp(-sum(lps) / len(lps))
    out["SP"] = 1 - math.exp(sum(lps))
    return out


def load_cell(cell_dir):
    """-> rows[(task_id, step_idx)][column] = value, plus the label column."""
    rows = collections.defaultdict(dict)

    uq = os.path.join(cell_dir, "uq.jsonl")
    if os.path.exists(uq):
        for line in open(uq):
            r = json.loads(line)
            key = (r.get("task_id"), r.get("step_idx"))
            kind = r.get("kind")
            if kind == "call":
                gen = r.get("gen_logprobs") or []
                spans = r.get("spans") or {}
                for stage, sk in (("thought", "T"), ("action", "A")):
                    for m, v in span_token_metrics(gen, spans.get(stage)).items():
                        rows[key]["%s_%s" % (m, sk)] = v
            elif kind == "step":
                for field, (stem, sk) in INGEN_FIELDS.items():
                    v = r.get(field)
                    if v is not None:
                        rows[key]["%s_%s" % (stem, sk)] = float(v)
                # carried for provenance / stratification, not as metrics
                for f in ("tau", "loop_flag", "obs_changed", "in_admissible"):
                    if r.get(f) is not None:
                        rows[key][f] = r[f]

    for fname in ("probes.jsonl", "probes.aggtrue.jsonl"):
        path = os.path.join(cell_dir, fname)
        if not os.path.exists(path):
            continue
        for line in open(path):
            r = json.loads(line)
            u = r.get("U")
            stem = PROBE_STEMS.get(r.get("probe_kind"))
            if u is None or not stem:
                continue
            field = r.get("metric_field") or ""
            sk = ("T" if field.startswith("U_T") else
                  "A" if field.startswith("U_A") else
                  "R" if field.startswith("U_R") else
                  {"thought": "T", "action": "A", "response": "R"}.get(r.get("stage")))
            if sk:
                rows[(r.get("task_id"), r.get("step_idx"))]["%s_%s" % (stem, sk)] = float(u)

    judge = os.path.join(cell_dir, "judge.jsonl")
    if os.path.exists(judge):
        for line in open(judge):
            r = json.loads(line)
            votes = [v.get("incorrect") for v in (r.get("votes") or {}).values()]
            votes = [v for v in votes if v is not None]
            if votes:
                key = (r["task_id"], r["step_idx"])
                rows[key]["judge_correct_frac"] = sum(1 for v in votes if v == 0) / len(votes)
                rows[key]["judge_n_valid"] = len(votes)
    return rows


def describe(vals):
    n = len(vals)
    if n == 0:
        return None
    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / n) if n > 1 else 0.0
    s = sorted(vals)
    return {"n": n, "mean": mean, "sd": sd, "min": s[0],
            "p50": s[n // 2], "max": s[-1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--outdir", default="reports/tables/selfassess")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    summary_rows = []
    cells = []
    for dataset in sorted(d for d in os.listdir(a.pivot)
                          if os.path.isdir(os.path.join(a.pivot, d)) and d != "crossprobe"):
        for model in sorted(os.listdir(os.path.join(a.pivot, dataset))):
            cell_dir = os.path.join(a.pivot, dataset, model)
            if not os.path.isdir(cell_dir):
                continue
            rows = load_cell(cell_dir)
            if not rows:
                continue

            metric_cols = sorted({c for v in rows.values() for c in v
                                  if c not in ("judge_correct_frac", "judge_n_valid",
                                               "tau", "loop_flag", "obs_changed",
                                               "in_admissible")})
            extra = [c for c in ("tau", "loop_flag", "obs_changed", "in_admissible",
                                 "judge_correct_frac", "judge_n_valid")
                     if any(c in v for v in rows.values())]
            header = ["task_id", "step_idx"] + metric_cols + extra

            path = os.path.join(a.outdir, "%s__%s.csv" % (dataset, model))
            with open(path, "w", newline="") as fo:
                w = csv.writer(fo)
                w.writerow(header)
                for (tid, sidx) in sorted(rows, key=lambda k: (str(k[0]), k[1] or 0)):
                    v = rows[(tid, sidx)]
                    w.writerow([tid, sidx] + [v.get(c, "") for c in header[2:]])

            for c in metric_cols:
                d = describe([v[c] for v in rows.values() if isinstance(v.get(c), float)])
                if d:
                    summary_rows.append(dict(dataset=dataset, model=model, column=c, **d))
            cells.append((dataset, model, len(rows), len(metric_cols), path))
            print("%-9s %-26s steps=%-6d metric-cols=%-3d -> %s"
                  % (dataset, model, len(rows), len(metric_cols), os.path.basename(path)))

    with open(os.path.join(a.outdir, "summary.csv"), "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["dataset", "model", "column", "n", "mean", "sd", "min", "p50", "max"])
        for r in summary_rows:
            w.writerow([r["dataset"], r["model"], r["column"], r["n"],
                        "%.6f" % r["mean"], "%.6f" % r["sd"], "%.6f" % r["min"],
                        "%.6f" % r["p50"], "%.6f" % r["max"]])

    # Coverage matrix: which metrics actually exist per cell, and on how many steps.
    lines = ["# Self-assessment raw metric extraction", "",
             "One CSV per (dataset x model): one row per step, one column per",
             "metric x stage. Suffixes: _T thought, _A action, _R whole response,",
             "_J joint/step-level. Blank where that metric does not exist for that stage.",
             "",
             "`judge_correct_frac` is a LABEL (fraction of 3 judges voting correct),",
             "carried for convenience; tau / loop_flag / obs_changed / in_admissible are",
             "environment facts carried for stratification. Neither are metrics.", ""]
    lines.append("| dataset | model | steps | metric cols | file |")
    lines.append("|---|---|---|---|---|")
    for dataset, model, nsteps, ncols, path in cells:
        lines.append("| %s | %s | %d | %d | `%s` |"
                     % (dataset, model, nsteps, ncols, os.path.basename(path)))
    lines.append("")

    bycol = collections.defaultdict(dict)
    for r in summary_rows:
        bycol[r["column"]][(r["dataset"], r["model"])] = r["n"]
    keys = sorted({(d, m) for d, m, _, _, _ in [(c[0], c[1], 0, 0, 0) for c in cells]})
    lines.append("## Coverage — steps carrying each metric")
    lines.append("")
    lines.append("| metric | " + " | ".join("%s/%s" % (d, m.split("-")[0]) for d, m in keys) + " |")
    lines.append("|---" * (len(keys) + 1) + "|")
    for col in sorted(bycol):
        lines.append("| %s | " % col + " | ".join(str(bycol[col].get(k, 0)) for k in keys) + " |")

    with open(os.path.join(a.outdir, "README.md"), "w") as fo:
        fo.write("\n".join(lines) + "\n")
    print("\nwrote %d cell CSVs + summary.csv + README.md to %s" % (len(cells), a.outdir))


if __name__ == "__main__":
    main()
