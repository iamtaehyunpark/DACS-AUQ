#!/usr/bin/env python3
"""Is a PERCENTILE rule consistent across targets, where an absolute threshold is not?

The operating-point result was negative: for a fixed assessor, mu_inc and mu_cor move so
much across targets that no absolute cut point transfers (uncertainty_levels.py). But a
deployed gate does not need an absolute cut — it needs "inspect the most suspicious k% of
this run", which is what a budget policy does.

This asks whether that rule means the same thing everywhere: if an assessor's top 10% by
U is enriched for incorrect steps by the same factor regardless of which model produced
the trajectory or which environment it came from, the policy is characterisable once even
though the threshold is not.

Reported per (assessor, target, dataset, k):
  base     fraction of steps that are judge-incorrect (the target's error rate)
  prec     fraction of the top-k% by U that are incorrect
  lift     prec / base   — the base-rate-free quantity. 1.0 = ranking is worthless.
  recall   share of all incorrect steps captured in the top k%

Raw precision is NOT comparable across targets: a target with an 89% error rate yields
high precision from any slice. Lift is, which is why stability is judged on lift.

  percentile_consistency.py [--pivot result/pivot] [--scope SPLIT-action]
                            [--ks 5,10,20,30] [--out ...md] [--csv ...csv]
"""
import argparse
import collections
import csv
import json
import os
import statistics

SCOPES = ["SPLIT-thought", "SPLIT-action", "AGG-mean", "AGG-true"]


def load_labels(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        r = json.loads(line)
        votes = [v.get("incorrect") for v in (r.get("votes") or {}).values()]
        votes = [v for v in votes if v is not None]
        if votes:
            out[(r["task_id"], r["step_idx"])] = sum(1 for v in votes if v == 0) / len(votes)
    return out


def load_ptrue(paths):
    out = collections.defaultdict(dict)
    for path in paths:
        if not os.path.exists(path):
            continue
        for line in open(path):
            r = json.loads(line)
            if r.get("probe_kind") != "ptrue":
                continue
            u = r.get("U")
            if u is None:
                continue
            f = r.get("metric_field") or ""
            k = ("T" if f.startswith("U_T") else "A" if f.startswith("U_A")
                 else "R" if f.startswith("U_R") else None)
            if k is None:
                k = {"thought": "T", "action": "A", "response": "R"}.get(r.get("stage"))
            if k:
                out[(r.get("task_id"), r.get("step_idx"))][k] = float(u)
    return out


def scoped(v, scope):
    if scope == "SPLIT-thought":
        return v.get("T")
    if scope == "SPLIT-action":
        return v.get("A")
    if scope == "AGG-true":
        return v.get("R")
    if scope == "AGG-mean":
        t, a = v.get("T"), v.get("A")
        return None if t is None or a is None else (t + a) / 2.0
    return None


def rank_stats(pairs):
    """Where does the INCORRECT pool sit once U is converted to a percentile rank
    within this cell?

    Absolute U is not comparable across targets (uncertainty_levels.py), so rank-transform
    it: 0 = lowest U in this cell, 100 = highest. Then ask where the incorrect steps land.
    If an assessor puts them at the same percentile regardless of target, the cut point is
    characterisable in percentile space even though it is not in raw score units.

    Ties share the average rank, which matters for judges whose scores saturate — Llama
    pins ~67% of its judgments at exactly 0 or 1, and competition ranking would otherwise
    hand the whole tied block an arbitrary spread.
    """
    n = len(pairs)
    if n < 20:
        return None
    order = sorted(range(n), key=lambda i: pairs[i][0])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and pairs[order[j]][0] == pairs[order[i]][0]:
            j += 1
        avg = (i + j - 1) / 2.0
        for t in range(i, j):
            ranks[order[t]] = 100.0 * avg / max(n - 1, 1)
        i = j
    inc = [ranks[i] for i in range(n) if pairs[i][1]]
    cor = [ranks[i] for i in range(n) if not pairs[i][1]]
    if len(inc) < 10 or len(cor) < 10:
        return None
    inc_s, cor_s = sorted(inc), sorted(cor)

    # The cut that best separates, expressed as a percentile of the cell's own scores.
    best = (-1.0, None)
    P, N = len(inc), len(cor)
    for q in range(1, 100):
        thr = 100.0 * q / 100.0
        tp = sum(1 for r in inc if r >= thr)
        fp = sum(1 for r in cor if r >= thr)
        j = tp / P - fp / N
        if j > best[0]:
            best = (j, thr)
    return {"inc_med": inc_s[len(inc_s) // 2],
            "inc_mean": sum(inc) / len(inc),
            "inc_q25": inc_s[len(inc_s) // 4],
            "inc_q75": inc_s[3 * len(inc_s) // 4],
            "cor_med": cor_s[len(cor_s) // 2],
            "cut_pctile": 100.0 - best[1]}   # as "top X% flagged"


def topk_stats(pairs, k_pct):
    """pairs = [(u, is_incorrect)]. Ties at the cut are included, so the slice can be
    slightly larger than k% — excluding them arbitrarily would bias precision upward for
    judges whose scores saturate (Llama pins ~67% of its judgments at 0 or 1)."""
    n = len(pairs)
    if n == 0:
        return None
    base = sum(1 for _, y in pairs if y) / n
    if base in (0.0, 1.0):
        return None
    want = max(1, int(round(n * k_pct / 100.0)))
    srt = sorted(pairs, key=lambda p: -p[0])
    cut = srt[want - 1][0]
    sel = [p for p in srt if p[0] >= cut]
    hits = sum(1 for _, y in sel if y)
    prec = hits / len(sel)
    total_inc = sum(1 for _, y in pairs if y)
    return {"base": base, "n_sel": len(sel), "prec": prec,
            "lift": prec / base, "recall": hits / total_inc}



# ---------------------------------------------------------------- gate 1
# Gate 1 swaps the LABEL INPUT and nothing else. No statistic below this line
# changes: the dict shape returned here — {(task_id, step_idx): fraction of
# judges voting CORRECT} — is exactly what the ensemble loader returned, with
# environment labels entering as hard 0.0 / 1.0.
def _gate1_labels(args, dataset, target, tdir):
    which = getattr(args, "labels", "ensemble")
    if which == "ensemble":
        return load_labels(os.path.join(tdir, "judge.jsonl"))
    import gate1_label_source
    if which == "ensemble_on_env_support":
        return gate1_label_source.load_ensemble_labels(
            args.label_file, dataset, target, mode=args.label_mode,
            column=args.label_column)
    return gate1_label_source.load_env_labels(
        args.label_file, dataset, target, mode=args.label_mode,
        column=args.label_column)


def _gate1_add_args(ap):
    ap.add_argument("--labels", default="ensemble",
                    choices=["ensemble", "env", "ensemble_on_env_support"],
                    help="ensemble: the published 3-judge label over all judged steps. "
                         "env: gate-1 y_env. ensemble_on_env_support: the 3-judge label "
                         "over exactly the y_env-labelable steps, so a side-by-side "
                         "isolates the label change from the step-set change")
    ap.add_argument("--label-file", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--label-mode", choices=["restricted", "full"], default="restricted",
                    help="restricted: only y_env-labelable steps. "
                         "full: all steps, unlabelled as negative-class-with-noise")
    ap.add_argument("--label-column", default="y_env")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--scope", default="SPLIT-action")
    ap.add_argument("--ks", default="5,10,20,30")
    ap.add_argument("--out", default="reports/tables/percentile_consistency.md")
    ap.add_argument("--csv", default="reports/tables/percentile_consistency.csv")
    _gate1_add_args(ap)
    a = ap.parse_args()
    KS = [int(x) for x in a.ks.split(",") if x.strip()]

    rows = []
    rank_rows = []
    xp = os.path.join(a.pivot, "crossprobe")
    for dataset in sorted(d for d in os.listdir(a.pivot)
                          if os.path.isdir(os.path.join(a.pivot, d)) and d != "crossprobe"):
        for target in sorted(os.listdir(os.path.join(a.pivot, dataset))):
            tdir = os.path.join(a.pivot, dataset, target)
            if not os.path.isdir(tdir):
                continue
            labels = _gate1_labels(a, dataset, target, tdir)
            if not labels:
                continue
            sources = {target: [os.path.join(tdir, "probes.jsonl"),
                                os.path.join(tdir, "probes.aggtrue.jsonl")]}
            xdir = os.path.join(xp, dataset, target)
            if os.path.isdir(xdir):
                seen = set()
                for f in os.listdir(xdir):
                    if not f.startswith("ptrue.") or not f.endswith(".jsonl"):
                        continue
                    stem = f[len("ptrue."):-len(".jsonl")]
                    for suf in (".stages", ".response"):
                        if stem.endswith(suf):
                            stem = stem[:-len(suf)]
                            break
                    else:
                        continue
                    seen.add(stem)
                for asr in seen:
                    sources[asr] = [os.path.join(xdir, "ptrue.%s.%s.jsonl" % (asr, p))
                                    for p in ("stages", "response")]

            for assessor, paths in sources.items():
                probes = load_ptrue(paths)
                pairs = []
                for key, v in probes.items():
                    if key not in labels:
                        continue
                    u = scoped(v, a.scope)
                    if u is None:
                        continue
                    pairs.append((u, labels[key] < 0.5))
                if len(pairs) < 100:
                    continue
                for k in KS:
                    st = topk_stats(pairs, k)
                    if st:
                        rows.append(dict(dataset=dataset, target=target, assessor=assessor,
                                         arm="self" if assessor == target else "cross",
                                         k=k, n=len(pairs), **st))
                rs = rank_stats(pairs)
                if rs:
                    rank_rows.append(dict(dataset=dataset, target=target, assessor=assessor,
                                          arm="self" if assessor == target else "cross",
                                          n=len(pairs), **rs))

    os.makedirs(os.path.dirname(a.csv), exist_ok=True)
    cols = ["dataset", "target", "assessor", "arm", "k", "n", "n_sel",
            "base", "prec", "lift", "recall"]
    with open(a.csv, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] if isinstance(r[c], (str, int)) else "%.4f" % r[c] for c in cols])

    lines = ["# Percentile-rule consistency — scope %s" % a.scope, "",
             "An absolute threshold does not transfer across targets. This asks whether a",
             "PERCENTILE rule does: is the top-k% by U enriched for incorrect steps by the",
             "same factor everywhere?", "",
             "`lift` = precision / base rate. Base-rate free, so it IS comparable across",
             "targets; raw precision is not. lift 1.0 = ranking worthless.",
             "Labels are the 3-judge ensemble — provisional until gate 1.", ""]

    for k in KS:
        lines += ["## Consistency of lift@%d%% across targets, per assessor" % k, "",
                  "| dataset | assessor | targets | lift mean | lift range | recall mean |",
                  "|---|---|---|---|---|---|"]
        for dataset in sorted({r["dataset"] for r in rows}):
            for asr in sorted({r["assessor"] for r in rows if r["dataset"] == dataset}):
                sub = [r for r in rows if r["dataset"] == dataset
                       and r["assessor"] == asr and r["k"] == k]
                if len(sub) < 3:
                    continue
                lf = [r["lift"] for r in sub]
                rc = [r["recall"] for r in sub]
                lines.append("| %s | %s | %d | %.2f | %.2f–%.2f | %.2f |" % (
                    dataset, asr, len(sub), statistics.mean(lf), min(lf), max(lf),
                    statistics.mean(rc)))
        lines.append("")

    lines += ["## Per-cell detail (k=10%)", "",
              "| dataset | assessor | target | arm | base | prec | lift | recall |",
              "|---|---|---|---|---|---|---|---|"]
    for r in sorted([x for x in rows if x["k"] == 10],
                    key=lambda x: (x["dataset"], x["assessor"], x["target"])):
        lines.append("| %s | %s | %s | %s | %.3f | %.3f | %.2f | %.3f |" % (
            r["dataset"], r["assessor"], r["target"], r["arm"],
            r["base"], r["prec"], r["lift"], r["recall"]))

    # ---- the percentile-position question ----
    lines += ["", "## Where does the INCORRECT pool sit, in percentile rank?", "",
              "U is rank-transformed within each cell (0 = lowest U here, 100 = highest),",
              "so this is comparable across targets where raw U is not. `inc med` is the",
              "median percentile of incorrect steps; `cut` is the separating cut expressed",
              "as 'flag the top X%'. Stability of these across an assessor's targets is",
              "what would make a percentile policy characterisable once.", "",
              "| dataset | assessor | targets | inc med mean | inc med range | cor med mean | cut mean | cut range |",
              "|---|---|---|---|---|---|---|---|"]
    for dataset in sorted({r["dataset"] for r in rank_rows}):
        for asr in sorted({r["assessor"] for r in rank_rows if r["dataset"] == dataset}):
            sub = [r for r in rank_rows if r["dataset"] == dataset and r["assessor"] == asr]
            if len(sub) < 3:
                continue
            im = [r["inc_med"] for r in sub]
            cm = [r["cor_med"] for r in sub]
            ct = [r["cut_pctile"] for r in sub]
            lines.append("| %s | %s | %d | %.1f | %.1f–%.1f | %.1f | %.1f | %.1f–%.1f |" % (
                dataset, asr, len(sub), statistics.mean(im), min(im), max(im),
                statistics.mean(cm), statistics.mean(ct), min(ct), max(ct)))
    lines.append("")
    lines += ["### Per-cell", "",
              "| dataset | assessor | target | arm | inc med | inc q25-q75 | cor med | cut |",
              "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rank_rows, key=lambda x: (x["dataset"], x["assessor"], x["target"])):
        lines.append("| %s | %s | %s | %s | %.1f | %.1f-%.1f | %.1f | %.1f |" % (
            r["dataset"], r["assessor"], r["target"], r["arm"],
            r["inc_med"], r["inc_q25"], r["inc_q75"], r["cor_med"], r["cut_pctile"]))

    rcols = ["dataset", "target", "assessor", "arm", "n", "inc_med", "inc_mean",
             "inc_q25", "inc_q75", "cor_med", "cut_pctile"]
    with open(a.csv.replace(".csv", "_ranks.csv"), "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(rcols)
        for r in rank_rows:
            w.writerow([r[c] if isinstance(r[c], (str, int)) else "%.3f" % r[c] for c in rcols])

    with open(a.out, "w") as fo:
        fo.write("\n".join(lines) + "\n")
    print("rows: %d" % len(rows))
    print("wrote %s and %s" % (a.out, a.csv))


if __name__ == "__main__":
    main()
