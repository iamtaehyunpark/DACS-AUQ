import json, collections, sys

def audit(path, arm, fields):
    steps, calls, eps = [], [], []
    try:
        for l in open(path):
            r = json.loads(l); k = r.get("kind")
            if k == "step": steps.append(r)
            elif k == "call": calls.append(r)
            elif k == "episode": eps.append(r)
    except FileNotFoundError:
        print("[%s] NO FILE %s" % (arm, path)); return
    n = len(steps)
    print("\n===== %s =====  steps=%d calls=%d episodes=%d" % (arm, n, len(calls), len(eps)))
    for f, kind in fields.items():
        vals = [s.get(f) for s in steps]
        if kind == "num":
            pop = sum(1 for v in vals if isinstance(v, (int, float)))
        else:
            pop = sum(1 for v in vals if isinstance(v, str) and v.strip())
        print("  %-26s populated %d/%d = %.0f%%" % (f, pop, n, 100 * pop / max(1, n)))
    sp_ok = sum(1 for c in calls if c.get("spans") and any(c["spans"].get(x) for x in ("thought", "action")))
    lp_ok = sum(1 for c in calls if c.get("gen_logprobs"))
    print("  spans present     %d/%d   gen_logprobs present %d/%d" % (sp_ok, len(calls), lp_ok, len(calls)))
    adm = [s.get("admissible") for s in steps if "admissible" in s]
    if adm:
        ok = sum(1 for a in adm if a)
        print("  admissible(tau-ok) %d/%d = %.0f%%" % (ok, len(adm), 100 * ok / len(adm)))
    # sample confidence distribution
    for f in fields:
        if fields[f] == "num":
            nn = [s.get(f) for s in steps if isinstance(s.get(f), (int, float))]
            if nn:
                print("  %s range [%.2f, %.2f] mean %.3f n=%d" % (f, min(nn), max(nn), sum(nn)/len(nn), len(nn)))

audit("/tmp/smoke_dec_l70.jsonl", "DECOUPLED", {"q_t_text": "txt", "U_T_targeted_ingen": "num", "U_A_targeted_ingen": "num"})
audit("/tmp/smoke_ent_l70.jsonl", "ENTANGLED", {"U_verbalized": "num"})
