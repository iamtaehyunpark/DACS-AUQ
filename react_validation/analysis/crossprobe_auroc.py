#!/usr/bin/env python3
"""Cross-evaluator P(True) AUROC: does a BIG evaluator rescue small-model uncertainty?

Same trajectories, same 3-judge labels — only the evaluator changes:
  SELF  = the small model scored its own steps   (probes_<tag>.jsonl)
  QWEN  = Qwen3.6-35B scored the same steps      (probes_<tag>.qwenjudge.jsonl)

Scopes: SPLIT-thought (U_T_ptrue), SPLIT-action (U_A_ptrue),
        AGG-mean (mean of the two), AGG-true (U_R_ptrue, whole response).

Reading:
  AUROC jumps under QWEN  -> EVALUATOR problem (small models can't self-assess)
  AUROC stays flat        -> GENERATOR problem (trajectories carry no signal)
"""
import json, os, sys, collections

RES = sys.argv[1] if len(sys.argv) > 1 else "result/models4"
TAGS = ["decoupled_phi4mini", "decoupled_gemma4b",
        "entangled_phi4mini", "entangled_gemma4b"]


def soft_auroc(vals, cs):
    """cs = fraction of judges voting CORRECT; positive class = incorrect."""
    wpos = [1 - c for c in cs]; wneg = list(cs)
    P, N = sum(wpos), sum(wneg)
    if P <= 0 or N <= 0:
        return None
    idx = sorted(range(len(vals)), key=lambda i: vals[i])
    num = cum = 0.0; i = 0
    while i < len(idx):
        j = i
        while j < len(idx) and vals[idx[j]] == vals[idx[i]]:
            j += 1
        gp = sum(wpos[idx[k]] for k in range(i, j)); gn = sum(wneg[idx[k]] for k in range(i, j))
        num += gp * (cum + 0.5 * gn); cum += gn; i = j
    return num / (P * N)


def load_probe(path, out):
    if not os.path.exists(path):
        return 0
    n = 0
    for l in open(path):
        try:
            r = json.loads(l)
        except Exception:
            continue
        mf = r.get("metric_field"); U = r.get("U")
        if mf in ("U_T_ptrue", "U_A_ptrue", "U_R_ptrue") and isinstance(U, (int, float)) \
                and r.get("parse_ok") is not False:
            out[(r["task_id"], r["step_idx"])][mf] = float(U); n += 1
    return n


for tag in TAGS:
    jf = os.path.join(RES, "judge_%s.jsonl" % tag.replace("decoupled_", "").replace("entangled_", "")
                      if not os.path.exists(os.path.join(RES, "judge_%s.jsonl" % tag))
                      else "judge_%s.jsonl" % tag)
    corr = {}
    if os.path.exists(jf):
        for l in open(jf):
            r = json.loads(l)
            vv = [v.get("incorrect") for v in (r.get("votes") or {}).values()
                  if isinstance(v, dict) and v.get("incorrect") in (0, 1)]
            if r.get("step_idx") is not None and vv:
                corr[(r["task_id"], r["step_idx"])] = sum(1 for v in vv if v == 0) / len(vv)

    # SELF probes were written by the original queue as probes_<model>.jsonl (no arm prefix);
    # the cross-eval pass uses probes_<arm>_<model>.qwenjudge.jsonl.
    model = tag.split("_", 1)[1]
    ev = {}
    for label, base, sfx in (("SELF", "probes_%s" % model, ""),
                             ("QWEN", "probes_%s" % tag, ".qwenjudge")):
        f = collections.defaultdict(dict)
        a = load_probe(os.path.join(RES, "%s%s.jsonl" % (base, sfx)), f)
        b = load_probe(os.path.join(RES, "%s%s.aggtrue_ptrue.jsonl" % (base, sfx)), f)
        ev[label] = (f, a + b)

    print("\n" + "=" * 76)
    print("%s   (judged steps=%d)" % (tag, len(corr)))
    print("=" * 76)
    print("  %-16s %12s %12s %10s" % ("scope", "SELF", "QWEN-eval", "delta"))
    print("  " + "-" * 54)

    for scope, getter in (
        ("SPLIT-thought", lambda d: d.get("U_T_ptrue")),
        ("SPLIT-action",  lambda d: d.get("U_A_ptrue")),
        ("AGG-mean",      lambda d: (d["U_T_ptrue"] + d["U_A_ptrue"]) / 2
                          if ("U_T_ptrue" in d and "U_A_ptrue" in d) else None),
        ("AGG-true",      lambda d: d.get("U_R_ptrue")),
    ):
        row = {}
        for label in ("SELF", "QWEN"):
            feats, _ = ev[label]
            xs, cs = [], []
            for k, c in corr.items():
                v = getter(feats.get(k, {}))
                if v is not None:
                    xs.append(v); cs.append(c)
            row[label] = (soft_auroc(xs, cs), len(xs))
        s, qn = row["SELF"], row["QWEN"]
        d = (qn[0] - s[0]) if (s[0] is not None and qn[0] is not None) else None
        print("  %-16s %12s %12s %10s   (n=%d/%d)" % (
            scope,
            ("%.3f" % s[0]) if s[0] is not None else "n/a",
            ("%.3f" % qn[0]) if qn[0] is not None else "n/a",
            ("%+.3f" % d) if d is not None else "n/a",
            s[1], qn[1]))
