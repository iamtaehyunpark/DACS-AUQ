#!/usr/bin/env python3
"""table1_step_auroc_v2.py — STEP-LEVEL discrimination table, restructured so the
aggregation-vs-split question is answered IN the table, per metric, with paired stats.

What changed vs v1 (and why):
  * Scopes renamed to what they actually are:
      AGG-true   = one reading of the WHOLE response, no stage attribution anywhere.
                   token metrics: computed over pooled thought+action tokens
                   (MaxTE=max over all, MTE=token-weighted mean, PPL/SP over pooled NLL);
                   in-gen: the entangled ĉ (single blended confidence).
                   (P(True)/post-hoc AGG-true needs a whole-response probe run — absent
                   unless provided; marked "n/a (needs probe run)".)
      AGG-mean   = mean(thought reading, action reading): a SPLIT-THEN-MERGE fusion.
                   This is what v1 mislabeled "undiscriminated".
      SPLIT-thought / SPLIT-action = single-stage readings.
  * Per-metric BLOCKS (scopes adjacent) instead of one sorted list.
  * PAIRED, trajectory-clustered bootstrap deltas per metric:
      d1 = AUROC(best SPLIT) - AUROC(AGG-true)     "does any single stage beat true aggregation?"
      d2 = AUROC(AGG-mean)  - AUROC(AGG-true)      "does split-then-merge beat true aggregation?"
      d3 = AUROC(best SPLIT) - AUROC(other SPLIT)  "do the stages differ?"
    Each with 95% CI; SIG iff CI excludes 0. Same resamples for both scopes (paired).
  * DIRECTION column: mean U on incorrect vs correct steps ( '+' = higher-U-on-errors,
    '-' = inverted). Distinguishes mislogged polarity (uniform '-') from mechanism.
  * COMPLEMENTARITY test per metric: grouped 5-fold CV logistic AUROC of
    (thought, action) two-feature model vs best single feature. Gain>0 with CI ⇒ the
    stages carry non-redundant signal even when single-row AUROCs look similar.
Everything is AUROC (soft, graded judge labels) — no exotic metrics.

Usage (per arm):
  python table1_step_auroc_v2.py --calls uq_X.jsonl --probes probes_X.jsonl \
      --judge judge_X.jsonl --out t1_X.md [--boot 2000]
"""
import argparse, json, math, random, statistics, collections

LOGPROBS, TOPK, SPANS = "gen_logprobs", "top", "spans"
INGEN = {"U_T_targeted_ingen": ("thought", "u(q_t) in-gen"),
         "U_A_targeted_ingen": ("action", "u_A(g_t) in-gen"),
         "U_verbalized": ("joint", "c-hat in-gen")}
PROBE_MAP = {"ptrue": "P(True)", "posthoc_numeric": "post-hoc num", "targeted": "targeted post-hoc"}
TOKEN_METRICS = ("MTE", "MaxTE", "PPL", "SP")

def ent_top(top):
    ps = [(e.get("prob") if e.get("prob") is not None else math.exp(e["logprob"])) for e in top]
    z = sum(ps)
    return -sum((p/z)*math.log(p/z) for p in ps if p > 0) if z > 0 else None

def seg_stats(seg):
    lps = [e["logprob"] for e in seg]
    ents = [x for x in (ent_top(e[TOPK]) for e in seg if e.get(TOPK)) if x is not None]
    return lps, ents

def token_metrics_from(lps, ents):
    out = {}
    n = len(lps)
    if not n: return out
    if ents:
        out["MTE"] = sum(ents)/len(ents)
        out["MaxTE"] = max(ents)
    out["PPL"] = math.exp(-sum(lps)/n)
    out["SP"] = 1 - math.exp(sum(lps))
    return out

def soft_auroc(vals, wpos, wneg):
    P, N = sum(wpos), sum(wneg)
    if P <= 0 or N <= 0: return None
    idx = sorted(range(len(vals)), key=lambda i: vals[i])
    num = cum = 0.0; i = 0
    while i < len(idx):
        j = i
        while j < len(idx) and vals[idx[j]] == vals[idx[i]]: j += 1
        gp = sum(wpos[idx[k]] for k in range(i, j)); gn = sum(wneg[idx[k]] for k in range(i, j))
        num += gp*(cum + 0.5*gn); cum += gn; i = j
    return num/(P*N)

def logistic_cv_auroc(rows, feats, folds=5):
    """rows: list of (task, x_dict, c). feats: feature names. Grouped CV; returns mean AUROC."""
    tasks = sorted({r[0] for r in rows})
    fold_of = {t: i % folds for i, t in enumerate(tasks)}
    # standardize
    stats_ = {}
    for f in feats:
        v = [r[1][f] for r in rows]
        mu = statistics.mean(v); sd = statistics.pstdev(v) or 1.0
        stats_[f] = (mu, sd)
    def z(r): return [ (r[1][f]-stats_[f][0])/stats_[f][1] for f in feats ]
    aurocs = []
    for k in range(folds):
        tr = [r for r in rows if fold_of[r[0]] != k]; te = [r for r in rows if fold_of[r[0]] == k]
        if len(te) < 20 or len(tr) < 50: continue
        w = [0.0]*len(feats); b = 0.0; lr = 0.3
        X = [z(r) for r in tr]; y = [1.0 if r[2] < 0.5 else 0.0 for r in tr]
        for _ in range(300):
            gw = [0.0]*len(feats); gb = 0.0
            for xi, yi in zip(X, y):
                p = 1/(1+math.exp(-(sum(wj*xj for wj, xj in zip(w, xi))+b)))
                d = p - yi
                for j in range(len(feats)): gw[j] += d*xi[j]
                gb += d
            n = len(X)
            for j in range(len(feats)): w[j] -= lr*gw[j]/n
            b -= lr*gb/n
        sc = [sum(wj*xj for wj, xj in zip(w, z(r)))+b for r in te]
        a = soft_auroc(sc, [1-r[2] for r in te], [r[2] for r in te])
        if a is not None: aurocs.append(a)
    return statistics.mean(aurocs) if aurocs else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", required=True); ap.add_argument("--probes", required=True)
    ap.add_argument("--judge", required=True); ap.add_argument("--out", default="table1_v2.md")
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()

    corr = {}
    for l in open(a.judge):
        r = json.loads(l)
        votes = [v.get("incorrect") for v in r.get("votes", {}).values()]
        votes = [v for v in votes if v is not None]
        if votes: corr[(r["task_id"], r["step_idx"])] = sum(1 for v in votes if v == 0)/len(votes)

    # per step: {(scope, metric): value}; scopes: T (thought), A (action), W (whole/pooled), J (joint in-gen)
    sv = collections.defaultdict(dict); run_id = ""
    segs = collections.defaultdict(dict)  # key -> {"thought": (lps,ents), "action": (lps,ents)}
    for l in open(a.calls):
        r = json.loads(l); run_id = run_id or r.get("run_id", "")
        k = r.get("kind"); key = (r.get("task_id"), r.get("step_idx"))
        if k == "call":
            glp = r.get(LOGPROBS) or []; spans = r.get(SPANS) or {}
            for sname in ("thought", "action"):
                sp = spans.get(sname)
                if not sp: continue
                seg = glp[sp[0]:sp[1]]
                if not seg: continue
                lps, ents = seg_stats(seg)
                if sname in segs[key]:  # same span name across calls (shouldn't happen) — pool
                    plps, pents = segs[key][sname]; lps = plps+lps; ents = pents+ents
                segs[key][sname] = (lps, ents)
        elif k == "step":
            for f, (stage, name) in INGEN.items():
                v = r.get(f)
                if isinstance(v, (int, float)):
                    sv[key][({"thought": "T", "action": "A", "joint": "J"}[stage], name)] = float(v)
    for key, d in segs.items():
        for sname, (lps, ents) in d.items():
            for m, v in token_metrics_from(lps, ents).items():
                sv[key][({"thought": "T", "action": "A"}[sname], m)] = v
        if "thought" in d and "action" in d:  # TRUE aggregate: pooled tokens, no attribution
            lps = d["thought"][0]+d["action"][0]; ents = d["thought"][1]+d["action"][1]
            for m, v in token_metrics_from(lps, ents).items():
                sv[key][("W", m)] = v
    for l in open(a.probes):
        p = json.loads(l); nm = PROBE_MAP.get(p.get("probe_kind"))
        if not nm: continue
        v = p.get("U")
        if isinstance(v, (int, float)) and p.get("stage") in ("thought", "action"):
            sv[(p["task_id"], p["step_idx"])][({"thought": "T", "action": "A"}[p["stage"]], nm)] = float(v)

    steps = [k for k in sv if k in corr]
    metrics = sorted({m for k in steps for (s, m) in sv[k]})
    rng = random.Random(11)

    def scope_val(k, m, scope):
        if scope == "AGG-true":
            if m in TOKEN_METRICS: return sv[k].get(("W", m))
            if m == "c-hat in-gen": return sv[k].get(("J", m))
            return None  # probes: needs whole-response probe run
        if scope == "AGG-mean":
            t, ac = sv[k].get(("T", m)), sv[k].get(("A", m))
            return (t+ac)/2 if (t is not None and ac is not None) else None
        if scope == "SPLIT-thought": return sv[k].get(("T", m))
        if scope == "SPLIT-action": return sv[k].get(("A", m))

    SCOPES = ["AGG-true", "AGG-mean", "SPLIT-thought", "SPLIT-action"]

    def auroc_on(keys, m, scope):
        data = [(k, scope_val(k, m, scope), corr[k]) for k in keys]
        data = [d for d in data if d[1] is not None]
        if len(data) < 30: return None, 0, None
        au = soft_auroc([d[1] for d in data], [1-d[2] for d in data], [d[2] for d in data])
        inc = [d[1] for d in data if d[2] < 0.5]; cor = [d[1] for d in data if d[2] >= 0.5]
        direction = "+" if (inc and cor and statistics.mean(inc) > statistics.mean(cor)) else "-"
        return au, len(data), direction

    bytask = collections.defaultdict(list)
    for k in steps: bytask[k[0]].append(k)
    tasks = list(bytask)

    def paired_delta(m, s1, s2):
        """AUROC(s1)-AUROC(s2), paired clustered bootstrap on common steps."""
        common = [k for k in steps if scope_val(k, m, s1) is not None and scope_val(k, m, s2) is not None]
        if len(common) < 30: return None
        cs = set(common); bt = collections.defaultdict(list)
        for k in common: bt[k[0]].append(k)
        ts = list(bt)
        def au(keys, s):
            d = [(scope_val(k, m, s), corr[k]) for k in keys]
            return soft_auroc([x for x, _ in d], [1-c for _, c in d], [c for _, c in d])
        base = (au(common, s1) or 0) - (au(common, s2) or 0)
        ds = []
        for _ in range(a.boot):
            samp = []
            for _ in range(len(ts)): samp.extend(bt[rng.choice(ts)])
            a1, a2 = au(samp, s1), au(samp, s2)
            if a1 is not None and a2 is not None: ds.append(a1-a2)
        if not ds: return None
        ds.sort()
        lo, hi = ds[int(0.025*len(ds))], ds[int(0.975*len(ds))]
        return base, lo, hi

    with open(a.out, "w") as fh:
        arm = "ENTANGLED" if "entangled" in run_id else "DECOUPLED"
        fh.write("# Table 1 v2 — step-level AUROC, aggregation vs split answered per metric\n")
        fh.write("## ARM: **%s** (%d labeled steps)\n\n" % (arm, len(steps)))
        fh.write("READING GUIDE — per metric block:\n")
        fh.write("- **AGG-true**: one reading of the whole response, no stage attribution (the real 'undiscriminated').\n")
        fh.write("- **AGG-mean**: mean(thought,action) — split-then-merge FUSION (v1 called this 'undiscriminated').\n")
        fh.write("- **SPLIT-…**: single-stage readings. dir '+' = higher U on errors (normal), '-' = inverted.\n")
        fh.write("- Verdict deltas (paired, clustered bootstrap, SIG iff CI excludes 0):\n")
        fh.write("  d1 = bestSPLIT − AGGtrue · d2 = AGGmean − AGGtrue · d3 = bestSPLIT − otherSPLIT\n\n")
        for m in metrics:
            fh.write("### %s\n\n| scope | n | AUROC(soft) | dir |\n|---|---|---|---|\n" % m)
            res = {}
            for sc in SCOPES:
                au, n, direction = auroc_on(steps, m, sc)
                res[sc] = au
                fh.write("| %s | %s | %s | %s |\n" % (
                    sc, n or "—", ("%.3f" % au) if au is not None else "n/a (needs probe run)" if sc == "AGG-true" and m not in TOKEN_METRICS and m != "c-hat in-gen" else "n/a",
                    direction or "—"))
            best_split = max(("SPLIT-thought", "SPLIT-action"), key=lambda s: (res.get(s) or -1))
            other = "SPLIT-action" if best_split == "SPLIT-thought" else "SPLIT-thought"
            fh.write("\n")
            for label, s1, s2 in [("d1 bestSPLIT−AGGtrue", best_split, "AGG-true"),
                                  ("d2 AGGmean−AGGtrue", "AGG-mean", "AGG-true"),
                                  ("d3 bestSPLIT−otherSPLIT", best_split, other)]:
                pd = paired_delta(m, s1, s2)
                if pd:
                    d, lo, hi = pd
                    sig = "**SIG**" if (lo > 0 or hi < 0) else "ns"
                    fh.write("- %s = %+.3f [%+.3f, %+.3f] %s\n" % (label, d, lo, hi, sig))
                else:
                    fh.write("- %s: n/a (missing scope)\n" % label)
            # complementarity: 2-feature vs best single, grouped CV
            rows = []
            for k in steps:
                t, ac = scope_val(k, m, "SPLIT-thought"), scope_val(k, m, "SPLIT-action")
                if t is not None and ac is not None: rows.append((k[0], {"t": t, "a": ac}, corr[k]))
            if len(rows) >= 200:
                a2f = logistic_cv_auroc(rows, ["t", "a"])
                a1t = logistic_cv_auroc(rows, ["t"]); a1a = logistic_cv_auroc(rows, ["a"])
                if a2f and a1t and a1a:
                    best1 = max(a1t, a1a)
                    fh.write("- complementarity (grouped 5-fold CV logistic): both=%.3f vs best-single=%.3f (gain %+.3f)\n"
                             % (a2f, best1, a2f-best1))
            fh.write("\n")
    print("wrote", a.out)

if __name__ == "__main__":
    main()
