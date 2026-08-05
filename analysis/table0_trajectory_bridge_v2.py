#!/usr/bin/env python3
"""table0_trajectory_bridge_v2.py — trajectory bridge table, per-metric blocks, honest scopes.

Changes vs v1:
  * Scopes renamed/restructured (same semantics as table1 v2):
      AGG-true  = whole-response reading (pooled thought+action tokens; in-gen c-hat)
      AGG-mean  = mean(thought,action) per step, then aggregated  (split-then-merge)
      SPLIT-thought / SPLIT-action
  * Per-metric blocks; each block ends with the block verdict vs the LENGTH NULL.
  * Headline summary: how many rows beat the length null (expected: none) — the table's
    entire point is that trajectory-level evaluation is length-confounded on ALFWorld.
  * Aggregators unchanged: mean/min/max/last (NO SUMS).

Usage (per arm):
  python table0_trajectory_bridge_v2.py --calls uq_X.jsonl --probes probes_X.jsonl --out t0_X.md
"""
import argparse, json, math, random, statistics, collections

LOGPROBS, TOPK, SPANS = "gen_logprobs", "top", "spans"
INGEN = {"U_T_targeted_ingen": ("T", "u(q_t) in-gen"),
         "U_A_targeted_ingen": ("A", "u_A(g_t) in-gen"),
         "U_verbalized": ("J", "c-hat in-gen")}
PROBE_MAP = {"ptrue": "P(True)", "posthoc_numeric": "post-hoc num", "targeted": "targeted post-hoc"}
TOKEN_METRICS = ("MTE", "MaxTE", "PPL", "SP")
AGGS = {"mean": statistics.mean, "min": min, "max": max, "last": lambda v: v[-1]}

def ent_top(top):
    ps = [(e.get("prob") if e.get("prob") is not None else math.exp(e["logprob"])) for e in top]
    z = sum(ps)
    return -sum((p/z)*math.log(p/z) for p in ps if p > 0) if z > 0 else None

def seg_stats(seg):
    lps = [e["logprob"] for e in seg]
    ents = [x for x in (ent_top(e[TOPK]) for e in seg if e.get(TOPK)) if x is not None]
    return lps, ents

def token_metrics_from(lps, ents):
    out = {}; n = len(lps)
    if not n: return out
    if ents:
        out["MTE"] = sum(ents)/len(ents); out["MaxTE"] = max(ents)
    out["PPL"] = math.exp(-sum(lps)/n); out["SP"] = 1 - math.exp(sum(lps))
    return out

def auroc(scores, labels):
    import bisect
    pos = sum(labels); neg = len(labels)-pos
    if pos == 0 or neg == 0: return None
    vals = sorted(scores)
    def avg_rank(v):
        lo = bisect.bisect_left(vals, v); hi = bisect.bisect_right(vals, v)
        return (lo+hi+1)/2.0
    r_pos = sum(avg_rank(scores[k]) for k in range(len(scores)) if labels[k] == 1)
    return (r_pos - pos*(pos+1)/2.0)/(pos*neg)

def boot_ci(scores, labels, n=5000, seed=7):
    rng = random.Random(seed); idx = list(range(len(scores))); out = []
    for _ in range(n):
        s = [rng.choice(idx) for _ in idx]
        a = auroc([scores[i] for i in s], [labels[i] for i in s])
        if a is not None: out.append(a)
    if not out: return None, None
    out.sort()
    return out[int(0.025*len(out))], out[int(0.975*len(out))]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", required=True); ap.add_argument("--probes", required=True)
    ap.add_argument("--out", default="table0_v2.md")
    a = ap.parse_args()

    sv = collections.defaultdict(dict)          # (task, step) -> {(scope,metric): v}
    segs = collections.defaultdict(dict)
    success = {}; length = collections.Counter(); run_id = ""
    for l in open(a.calls):
        r = json.loads(l); run_id = run_id or r.get("run_id", "")
        k = r.get("kind"); task = r.get("task_id"); key = (task, r.get("step_idx"))
        if k == "episode": success[task] = bool(r.get("success"))
        elif k == "step":
            length[task] = max(length[task], r["step_idx"]+1)
            for f, (sc, nm) in INGEN.items():
                v = r.get(f)
                if isinstance(v, (int, float)): sv[key][(sc, nm)] = float(v)
        elif k == "call":
            glp = r.get(LOGPROBS) or []; spans = r.get(SPANS) or {}
            for sname, sc in (("thought", "T"), ("action", "A")):
                sp = spans.get(sname)
                if not sp: continue
                seg = glp[sp[0]:sp[1]]
                if not seg: continue
                lps, ents = seg_stats(seg)
                if sname in segs[key]:
                    plps, pents = segs[key][sname]; lps = plps+lps; ents = pents+ents
                segs[key][sname] = (lps, ents)
    for key, d in segs.items():
        for sname, sc in (("thought", "T"), ("action", "A")):
            if sname in d:
                for m, v in token_metrics_from(*d[sname]).items(): sv[key][(sc, m)] = v
        if "thought" in d and "action" in d:
            lps = d["thought"][0]+d["action"][0]; ents = d["thought"][1]+d["action"][1]
            for m, v in token_metrics_from(lps, ents).items(): sv[key][("W", m)] = v
    for l in open(a.probes):
        p = json.loads(l); nm = PROBE_MAP.get(p.get("probe_kind"))
        if not nm: continue
        v = p.get("U")
        if isinstance(v, (int, float)) and p.get("stage") in ("thought", "action"):
            sv[(p["task_id"], p["step_idx"])][({"thought": "T", "action": "A"}[p["stage"]], nm)] = float(v)

    def scope_val(key, m, scope):
        if scope == "AGG-true":
            if m in TOKEN_METRICS: return sv[key].get(("W", m))
            if m == "c-hat in-gen": return sv[key].get(("J", m))
            return None
        if scope == "AGG-mean":
            t, ac = sv[key].get(("T", m)), sv[key].get(("A", m))
            return (t+ac)/2 if (t is not None and ac is not None) else None
        if scope == "SPLIT-thought": return sv[key].get(("T", m))
        if scope == "SPLIT-action": return sv[key].get(("A", m))

    tasks = [t for t in success]
    metrics = sorted({m for k in sv for (s, m) in sv[k]})
    SCOPES = ["AGG-true", "AGG-mean", "SPLIT-thought", "SPLIT-action"]

    L = [(length[t], 0 if success[t] else 1) for t in tasks if length[t] > 0]
    la = auroc([x for x, _ in L], [y for _, y in L]); llo, lhi = boot_ci([x for x, _ in L], [y for _, y in L])

    beat = 0; total = 0
    blocks = []
    for m in metrics:
        rows = []
        for scope in SCOPES:
            for agg_name, agg in AGGS.items():
                scores, labels = [], []
                for t in tasks:
                    vals = [scope_val((t, st), m, scope) for st in range(length[t])]
                    vals = [v for v in vals if v is not None]
                    if not vals: continue
                    scores.append(agg(vals)); labels.append(0 if success[t] else 1)
                if len(scores) < 8: continue
                au = auroc(scores, labels)
                if au is None: continue
                lo, hi = boot_ci(scores, labels)
                total += 1
                ok = lo is not None and lo > la
                beat += ok
                rows.append((scope, agg_name, len(scores), au, lo, hi, ok))
        blocks.append((m, rows))

    with open(a.out, "w") as fh:
        arm = "ENTANGLED" if "entangled" in run_id else "DECOUPLED"
        fh.write("# Table 0 v2 — trajectory-level AUROC vs episode success (bridge)\n")
        fh.write("## ARM: **%s** (n=%d episodes)\n\n" % (arm, len(tasks)))
        fh.write("**LENGTH NULL: AUROC = %.3f [%.3f, %.3f]** (step count alone)\n\n" % (la, llo, lhi))
        fh.write("**HEADLINE: %d / %d rows beat the length null.** " % (beat, total))
        fh.write("This table demonstrates that trajectory-aggregate evaluation is length-confounded here; ")
        fh.write("real discrimination lives in the step-level table.\n\n")
        for m, rows in blocks:
            if not rows: continue
            fh.write("### %s\n\n| scope | agg | n | AUROC | 95%% CI | beats null |\n|---|---|---|---|---|---|\n" % m)
            for scope, agg_name, n, au, lo, hi, ok in sorted(rows, key=lambda r: -r[3]):
                fh.write("| %s | %s | %d | %.3f | [%.3f, %.3f] | %s |\n"
                         % (scope, agg_name, n, au, lo, hi, "**yes**" if ok else "no"))
            fh.write("\n")
    print("wrote %s (length-null=%.3f, beat=%d/%d)" % (a.out, la, beat, total))

if __name__ == "__main__":
    main()
