"""Generic format-native smoke audit: python smoke_audit_generic.py <uqlog.jsonl> <LABEL>

Checks whether a model follows the decoupled format-native contract:
  q_t_text / U_T_targeted_ingen  (THOUGHT_TARGET: + THOUGHT_CONFIDENCE:)
  U_A_targeted_ingen             (ACTION_CONFIDENCE:)
plus span+logprob capture and tau/admissible action validity.
"""
import json, sys, collections

path, label = sys.argv[1], sys.argv[2]
steps, calls, eps = [], [], []
try:
    for l in open(path):
        l = l.strip()
        if not l:
            continue
        r = json.loads(l)
        k = r.get("kind")
        if k == "step": steps.append(r)
        elif k == "call": calls.append(r)
        elif k == "episode": eps.append(r)
except FileNotFoundError:
    print("%-12s NO OUTPUT FILE (%s)" % (label, path)); sys.exit()

n = len(steps)
if n == 0:
    print("%-12s 0 steps produced — check the run log" % label); sys.exit()

def pop(field, numeric=True):
    if numeric:
        return sum(1 for s in steps if isinstance(s.get(field), (int, float)))
    return sum(1 for s in steps if isinstance(s.get(field), str) and s.get(field).strip())

qt = pop("q_t_text", False)
ut = pop("U_T_targeted_ingen")
ua = pop("U_A_targeted_ingen")
adm = [s.get("admissible") for s in steps if "admissible" in s]
adm_ok = sum(1 for a in adm if a)
sp_ok = sum(1 for c in calls if c.get("spans") and any((c["spans"] or {}).get(x) for x in ("thought", "action")))
lp_ok = sum(1 for c in calls if c.get("gen_logprobs"))
succ = sum(1 for e in eps if e.get("success"))

def pct(a, b):
    return "%3.0f%%" % (100.0 * a / b) if b else "  n/a"

verdict = "PASS" if (ut / n >= 0.8 and ua / n >= 0.8 and qt / n >= 0.8) else \
          "WEAK" if (ut / n >= 0.5 or ua / n >= 0.5) else "FAIL"
print("%-12s steps=%-4d eps=%d succ=%d | q_t %s  U_T %s  U_A %s | spans %s logprobs %s | adm %s | %s"
      % (label, n, len(eps), succ, pct(qt, n), pct(ut, n), pct(ua, n),
         pct(sp_ok, len(calls)), pct(lp_ok, len(calls)), pct(adm_ok, len(adm)) if adm else " n/a", verdict))
