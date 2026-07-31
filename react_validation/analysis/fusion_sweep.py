#!/usr/bin/env python3
"""fusion_sweep.py — find the best two-stage uncertainty combination, honestly.

Does, in one run per arm:
  1. CANDIDATES  — computes every (stage, metric) feature from the corpus, ranks by
                   single-feature grouped-CV AUROC, keeps the top thought-side and
                   top action-side features (+ top-2 overall).
  2. NORMALIZE   — percentile transform per feature (fit on train folds only), so
                   nats / PPL / [0,1]-confidences become commensurable; polarity is
                   auto-fixed per feature on train (flip if train AUROC < 0.5).
  3. STRATEGIES  — the ladder, all evaluated with grouped 5-fold CV (fold = task):
       L0  best single feature                                (baseline to beat)
       L1  fixed combiners on percentiles: mean, max, product  (0 params)
       L2  RATIO SWEEP: w*f_T + (1-w)*f_A, w in {0,.02,...,1}  (the sweet-spot curve;
           every point is out-of-fold, so the curve itself is honest)
       L2b per-fold-selected w (w chosen on train, applied to test — fully honest
           version of "the sweet spot")
       L3  isotonic-calibrated noisy-OR: P(err)=1-(1-pT)(1-pA)  (0 fusion params;
           the theory-supplied combiner)
       L4  logistic on [f_T, f_A] (+interaction), grouped CV    (3-4 params)
  4. REPORT      — markdown: candidate table, sweet-spot curve, strategy-vs-L0 table
                   with per-fold paired deltas, one verdict line.

Usage (per arm):
  python fusion_sweep.py --calls uq_X.jsonl --probes probes_X.jsonl --judge judge_X.jsonl \
      --out fusion_X.md [--pair "P(True)@thought,MaxTE@action"]
"""
import argparse, json, math, random, statistics, collections

LOGPROBS, TOPK, SPANS = "gen_logprobs", "top", "spans"
INGEN = {"U_T_targeted_ingen": ("thought", "u(q_t) in-gen"),
         "U_A_targeted_ingen": ("action", "u_A(g_t) in-gen"),
         "U_verbalized": ("joint", "c-hat in-gen")}
PROBE_MAP = {"ptrue": "P(True)", "posthoc_numeric": "post-hoc num", "targeted": "targeted post-hoc"}

# ---------- data loading (same schema as table1 v2) ----------
def ent_top(top):
    ps = [(e.get("prob") if e.get("prob") is not None else math.exp(e["logprob"])) for e in top]
    z = sum(ps)
    return -sum((p/z)*math.log(p/z) for p in ps if p > 0) if z > 0 else None

def load(calls_f, probes_f, judge_f):
    corr = {}
    for l in open(judge_f):
        r = json.loads(l)
        votes = [v.get("incorrect") for v in r.get("votes", {}).values()]
        votes = [v for v in votes if v is not None]
        if votes: corr[(r["task_id"], r["step_idx"])] = sum(1 for v in votes if v == 0)/len(votes)
    feats = collections.defaultdict(dict)  # (task,step) -> {"metric@stage": value}
    for l in open(calls_f):
        r = json.loads(l); k = r.get("kind"); key = (r.get("task_id"), r.get("step_idx"))
        if k == "call":
            glp = r.get(LOGPROBS) or []; spans = r.get(SPANS) or {}
            for sname in ("thought", "action"):
                sp = spans.get(sname)
                if not sp: continue
                seg = glp[sp[0]:sp[1]]
                if not seg: continue
                lps = [e["logprob"] for e in seg]
                ents = [x for x in (ent_top(e[TOPK]) for e in seg if e.get(TOPK)) if x is not None]
                n = len(lps)
                if ents:
                    feats[key][f"MTE@{sname}"] = sum(ents)/len(ents)
                    feats[key][f"MaxTE@{sname}"] = max(ents)
                feats[key][f"PPL@{sname}"] = math.exp(-sum(lps)/n)
                feats[key][f"SP@{sname}"] = 1 - math.exp(sum(lps))
        elif k == "step":
            for f, (stage, name) in INGEN.items():
                v = r.get(f)
                if isinstance(v, (int, float)): feats[key][f"{name}@{stage}"] = float(v)
    for l in open(probes_f):
        p = json.loads(l); nm = PROBE_MAP.get(p.get("probe_kind"))
        if nm and isinstance(p.get("U"), (int, float)) and p.get("stage") in ("thought", "action"):
            feats[(p["task_id"], p["step_idx"])][f"{nm}@{p['stage']}"] = float(p["U"])
    steps = [k for k in feats if k in corr]
    return feats, corr, steps

# ---------- metrics ----------
def soft_auroc(vals, cs):
    wpos = [1-c for c in cs]; wneg = list(cs)
    P, N = sum(wpos), sum(wneg)
    if P <= 0 or N <= 0: return None
    idx = sorted(range(len(vals)), key=lambda i: vals[i])
    num = cum = 0.0; i = 0
    while i < len(idx):
        j = i
        while j < len(idx) and vals[idx[j]] == vals[idx[i]]: j += 1
        gp = sum(wpos[idx[k]] for k in range(i, j)); gn = sum(wneg[idx[k]] for k in range(i, j))
        num += gp*(cum+0.5*gn); cum += gn; i = j
    return num/(P*N)

# ---------- fold machinery ----------
def make_folds(steps, k=5, seed=13):
    tasks = sorted({s[0] for s in steps}); random.Random(seed).shuffle(tasks)
    fold_of = {t: i % k for i, t in enumerate(tasks)}
    return [( [s for s in steps if fold_of[s[0]] != f], [s for s in steps if fold_of[s[0]] == f]) for f in range(k)]

def pct_transform(train_vals):
    sv = sorted(train_vals); n = len(sv)
    import bisect
    def f(v):
        lo = bisect.bisect_left(sv, v); hi = bisect.bisect_right(sv, v)
        return ((lo+hi)/2)/n
    return f

def isotonic(xs, ys):
    """PAV: xs sorted ascending, ys in [0,1]; returns step function."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    x = [xs[i] for i in order]; y = [float(ys[i]) for i in order]; w = [1.0]*len(y)
    i = 0
    while i < len(y)-1:
        if y[i] > y[i+1]:
            ny = (y[i]*w[i]+y[i+1]*w[i+1])/(w[i]+w[i+1])
            y[i] = ny; w[i] += w[i+1]
            del y[i+1], w[i+1], x[i+1]
            if i > 0: i -= 1
        else: i += 1
    import bisect
    def f(v):
        j = bisect.bisect_right(x, v)-1
        return y[max(0, min(j, len(y)-1))]
    return f

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", required=True); ap.add_argument("--probes", required=True)
    ap.add_argument("--judge", required=True); ap.add_argument("--out", default="fusion.md")
    ap.add_argument("--pair", default=None, help="override: 'F1,F2' feature names metric@stage")
    ap.add_argument("--topk", type=int, default=6)
    a = ap.parse_args()
    feats, corr, steps = load(a.calls, a.probes, a.judge)
    folds = make_folds(steps)

    all_names = sorted({n for k in steps for n in feats[k]})
    # ---- 1. candidate ranking: single-feature CV AUROC with train-side polarity fix
    def single_cv(name):
        aurocs = []
        for tr, te in folds:
            trv = [(feats[k][name], corr[k]) for k in tr if name in feats[k]]
            tev = [(feats[k][name], corr[k]) for k in te if name in feats[k]]
            if len(trv) < 100 or len(tev) < 30: continue
            flip = (soft_auroc([v for v, _ in trv], [c for _, c in trv]) or 0.5) < 0.5
            vals = [(-v if flip else v) for v, _ in tev]
            au = soft_auroc(vals, [c for _, c in tev])
            if au is not None: aurocs.append(au)
        return statistics.mean(aurocs) if aurocs else None
    ranking = sorted(((single_cv(n), n) for n in all_names), key=lambda x: -(x[0] or 0))
    ranking = [(au, n) for au, n in ranking if au is not None]
    best_thought = next((n for au, n in ranking if n.endswith("@thought")), None)
    best_action = next((n for au, n in ranking if n.endswith("@action")), None)
    if a.pair: f1, f2 = [x.strip() for x in a.pair.split(",")]
    else: f1, f2 = best_thought, best_action
    L0_name, L0_au = ranking[0][1], ranking[0][0]

    def prep_fold(tr, te, names):
        """returns train/test lists of (percentile-transformed feature vector, c)."""
        common_tr = [k for k in tr if all(n in feats[k] for n in names)]
        common_te = [k for k in te if all(n in feats[k] for n in names)]
        if len(common_tr) < 100 or len(common_te) < 30: return None
        out_tr, out_te = [], []
        fns = {}
        for n in names:
            trv = [feats[k][n] for k in common_tr]
            flip = (soft_auroc(trv, [corr[k] for k in common_tr]) or 0.5) < 0.5
            pf = pct_transform([-v for v in trv] if flip else trv)
            fns[n] = (flip, pf)
        for ks, out in ((common_tr, out_tr), (common_te, out_te)):
            for k in ks:
                vec = []
                for n in names:
                    flip, pf = fns[n]
                    v = feats[k][n]
                    vec.append(pf(-v if flip else v))
                out.append((vec, corr[k]))
        return out_tr, out_te

    def cv_eval(score_fn_builder, names):
        """score_fn_builder(train)->fn(vec); returns (mean auroc, per-fold aurocs)."""
        res = []
        for tr, te in folds:
            pp = prep_fold(tr, te, names)
            if not pp: continue
            train, test = pp
            fn = score_fn_builder(train)
            au = soft_auroc([fn(v) for v, _ in test], [c for _, c in test])
            if au is not None: res.append(au)
        return (statistics.mean(res) if res else None), res

    results = {}
    # L1 fixed combiners
    for nm, comb in [("L1 mean", lambda v: (v[0]+v[1])/2), ("L1 max", max),
                     ("L1 product", lambda v: v[0]*v[1])]:
        results[nm] = cv_eval(lambda train, c=comb: (lambda v: c(v)), [f1, f2])
    # L2 ratio sweep (each w evaluated out-of-fold) + honest per-fold-selected w
    curve = []
    for wi in range(0, 51):
        w = wi/50.0
        au, _ = cv_eval(lambda train, w=w: (lambda v: w*v[0]+(1-w)*v[1]), [f1, f2])
        if au is not None: curve.append((w, au))
    best_w, best_w_au = max(curve, key=lambda x: x[1]) if curve else (None, None)
    def sel_w(train):
        ws = [wi/50.0 for wi in range(0, 51)]
        aus = [(w, soft_auroc([w*v[0]+(1-w)*v[1] for v, _ in train], [c for _, c in train]) or 0) for w in ws]
        wbest = max(aus, key=lambda x: x[1])[0]
        return lambda v: wbest*v[0]+(1-wbest)*v[1]
    results["L2b selected-w (train-fit)"] = cv_eval(sel_w, [f1, f2])
    # L3 calibrated noisy-OR
    def noisy_or(train):
        iso1 = isotonic([v[0] for v, _ in train], [1-c for _, c in train])
        iso2 = isotonic([v[1] for v, _ in train], [1-c for _, c in train])
        return lambda v: 1-(1-iso1(v[0]))*(1-iso2(v[1]))
    results["L3 calibrated noisy-OR"] = cv_eval(noisy_or, [f1, f2])
    # L4 logistic (+interaction)
    def logistic(train, interact=False):
        X = [(v[0], v[1], v[0]*v[1]) if interact else (v[0], v[1]) for v, _ in train]
        y = [1.0 if c < 0.5 else 0.0 for _, c in train]
        d = len(X[0]); w = [0.0]*d; b = 0.0; lr = 0.5
        for _ in range(400):
            gw = [0.0]*d; gb = 0.0
            for xi, yi in zip(X, y):
                p = 1/(1+math.exp(-(sum(wj*xj for wj, xj in zip(w, xi))+b)))
                dd = p-yi
                for j in range(d): gw[j] += dd*xi[j]
                gb += dd
            n = len(X)
            for j in range(d): w[j] -= lr*gw[j]/n
            b -= lr*gb/n
        def fn(v):
            x = (v[0], v[1], v[0]*v[1]) if interact else (v[0], v[1])
            return sum(wj*xj for wj, xj in zip(w, x))+b
        return fn
    results["L4 logistic"] = cv_eval(lambda t: logistic(t, False), [f1, f2])
    results["L4 logistic+interaction"] = cv_eval(lambda t: logistic(t, True), [f1, f2])

    with open(a.out, "w") as fh:
        fh.write("# Fusion sweep — two-stage combination vs best single\n\n")
        fh.write("## Candidates (single-feature grouped-CV AUROC, polarity auto-fixed on train)\n\n")
        fh.write("| feature | CV AUROC |\n|---|---|\n")
        for au, n in ranking[:a.topk]: fh.write("| %s | %.3f |\n" % (n, au))
        fh.write("\n**Pair fused:** `%s` (thought side) + `%s` (action side)\n" % (f1, f2))
        fh.write("**L0 baseline (best single overall):** `%s` = %.3f\n\n" % (L0_name, L0_au))
        fh.write("## Sweet-spot curve — w·%s + (1−w)·%s (each point out-of-fold)\n\n" % (f1, f2))
        fh.write("| w | CV AUROC |\n|---|---|\n")
        for w, au in curve[::5]: fh.write("| %.2f | %.3f |\n" % (w, au))
        if best_w is not None:
            fh.write("\n**curve max:** w=%.2f, AUROC=%.3f  (argmax over the curve — mildly optimistic; ")
            fh.write("the honest number is L2b below)\n\n" % () if False else "")
            fh.write("**curve max:** w=%.2f → AUROC=%.3f\n\n" % (best_w, best_w_au))
        fh.write("## Strategies (grouped 5-fold CV) vs L0 = %.3f\n\n" % L0_au)
        fh.write("| strategy | CV AUROC | gain vs L0 | per-fold |\n|---|---|---|---|\n")
        for nm, (au, pf) in results.items():
            if au is None: fh.write("| %s | n/a | — | — |\n" % nm); continue
            fh.write("| %s | %.3f | %+.3f | %s |\n" % (nm, au, au-L0_au, " ".join("%.3f" % x for x in pf)))
        best_nm, (best_au, _) = max(((nm, r) for nm, r in results.items() if r[0] is not None),
                                    key=lambda x: x[1][0])
        fh.write("\n## Verdict\n\n")
        if best_au > L0_au + 0.005:
            fh.write("Best fusion **%s = %.3f** beats best single (%.3f) by %+.3f.\n" % (best_nm, best_au, L0_au, best_au-L0_au))
        else:
            fh.write("No fusion beats the best single feature (%s = %.3f) by more than 0.005 — "
                     "stage SELECTION, not combination, is the story on this arm.\n" % (L0_name, L0_au))
    print("wrote", a.out)

if __name__ == "__main__":
    main()
