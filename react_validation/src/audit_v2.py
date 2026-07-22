"""audit_v2 — regeneration-gate checks for the v4 corpora (format-native confidence).

Usage: python audit_v2.py <uq_log.jsonl> <arm: decoupled|entangled>
Exits 0 with "GATE: PASS" only if there are zero BLOCKING findings.

Confidence is a plain trailing label (THOUGHT_CONFIDENCE:/ACTION_CONFIDENCE:), no XML.
A tau=None on a NON-EMPTY, command-shaped action is a genuine model error (e.g. a hallucinated
verb) — reported as an unrecognized-action RATE (warning), never a hard block unless the rate is
so high it signals a harness defect (>15%). Empty actions and confidence-label leakage into the
passed thought remain blocking.
"""
import json, sys, re
from tau_map import tau_dict

path, arm = sys.argv[1], sys.argv[2]
R = [json.loads(l) for l in open(path)]
calls = [r for r in R if r["kind"] == "call"]
steps = [r for r in R if r["kind"] == "step"]
eps = [r for r in R if r["kind"] == "episode"]
blocking, warn = [], []


def B(cond, msg):
    (warn if cond else blocking).append(("ok " if cond else "FAIL ") + msg)


def W(msg):
    warn.append("~ " + msg)


CONF_LABEL = re.compile(r"THOUGHT_TARGET:|THOUGHT_CONFIDENCE:|ACTION_CONFIDENCE:", re.I)

# 1. presence / schema
B(len(calls) and len(steps) and len(eps), "records present (call/step/episode)")
B(all("config" in c and "seed" in c["config"] for c in calls), "every call has config.seed")
B(all("gen_logprobs" in c and "spans" in c for c in calls), "every call has gen_logprobs + spans")

# 2. spans reconstruct to a prefix of completion_raw
recon_fail = 0
for c in calls:
    g, raw = c["gen_logprobs"], c["completion_raw"]
    for st in ("thought", "action"):
        sp = c["spans"].get(st)
        if not sp:
            continue
        txt = "".join(t["token"] for t in g[sp[0]:sp[1]])
        if txt not in raw and not raw.startswith(txt):
            recon_fail += 1
B(recon_fail == 0, "span tokens reconstruct into completion_raw (%d fail)" % recon_fail)

# 3. tau: verb-consistent (blocking); tau-None on non-empty action = unrecognized-action RATE (warn,
#    blocking only if egregious). Empty actions are handled by check 8, not counted here.
tau_missing = [s for s in steps if (s.get("action_parsed") or "").strip() and s.get("tau") is None]
tau_bad = [s for s in steps if s.get("tau") and s["tau"] != tau_dict(s["action_parsed"])]
B(not tau_bad, "tau verb-consistent with action_parsed (%d mismatched)" % len(tau_bad))
n_nonempty = sum(1 for s in steps if (s.get("action_parsed") or "").strip())
rate = (len(tau_missing) / n_nonempty) if n_nonempty else 0.0
W("unrecognized-action rate %.1f%% (%d/%d non-empty) — genuine model errors kept, not blocked"
  % (100 * rate, len(tau_missing), n_nonempty))
if tau_missing:
    ex = {}
    for s in tau_missing:
        a = s["action_parsed"]
        ex[a] = ex.get(a, 0) + 1
    W("  unrecognized actions: " + ", ".join("%r x%d" % (a, n) for a, n in sorted(ex.items(), key=lambda kv: -kv[1])[:8]))
B(rate <= 0.15, "unrecognized-action rate <=15%% (%.1f%%)" % (100 * rate))

# 4. per-step seeds per formula: 1000 + task*100000 + step*100 + call_offset
seed_ok = seed_tot = 0
task_order = []
for c in calls:
    if c["task_id"] not in task_order:
        task_order.append(c["task_id"])
for c in calls:
    ti = task_order.index(c["task_id"])
    off = 0 if c["call_kind"] in ("thought", "joint") else 1
    exp = 1000 + ti * 100000 + c["step_idx"] * 100 + off
    seed_tot += 1
    seed_ok += 1 if c["config"]["seed"] == exp else 0
B(seed_ok == seed_tot, "per-step seeds match formula (%d/%d)" % (seed_ok, seed_tot))

# 5. confidence label parsed OR skip logged (format-native, non-blocking parse)
if arm == "decoupled":
    miss = [s for s in steps if s.get("U_T_targeted_ingen") is None
            and "thought_confidence_parse_failed" not in (s.get("skip_reasons") or [])]
    B(not miss, "THOUGHT_CONFIDENCE (targeted u(q_t)) parsed or skip logged, every step (%d unaccounted)" % len(miss))
    qmiss = [s for s in steps if s.get("q_t_text") is None
             and "thought_target_parse_failed" not in (s.get("skip_reasons") or [])]
    B(not qmiss, "THOUGHT_TARGET (q_t) parsed or skip logged, every step (%d unaccounted)" % len(qmiss))
    amiss = [s for s in steps if (s.get("action_parsed") or "").strip() and s.get("U_A_targeted_ingen") is None
             and "action_confidence_parse_failed" not in (s.get("skip_reasons") or [])]
    B(not amiss, "ACTION_CONFIDENCE (u_A(g_t)) parsed or skip logged, every non-empty step (%d unaccounted)" % len(amiss))
    # 6. thought_clean excludes the confidence label AND trailing admissible-command lines
    label_in_thought = sum(1 for s in steps if CONF_LABEL.search(s.get("thought_clean") or ""))
    cmd_trailing = 0
    for s in steps:
        tclean = s.get("thought_clean") or ""
        cset = {re.sub(r"\s+", " ", x.strip().lower()).strip(" .") for x in (s.get("admissible") or [])}
        last = re.sub(r"\s+", " ", tclean.rstrip().split("\n")[-1].strip().lower()).strip(" .") if tclean else ""
        if last in cset and last:
            cmd_trailing += 1
    B(label_in_thought == 0, "no confidence label inside thought_clean (%d found)" % label_in_thought)
    B(cmd_trailing == 0, "thought_clean has no trailing admissible-command line (%d found)" % cmd_trailing)
    # 7. strip-before-pass: no confidence label in the PASSED THOUGHT (the "YOUR CURRENT REASONING:"
    # section of the action prompt); the template's own ACTION_CONFIDENCE instruction is expected.
    def _reasoning_section(p):
        seg = p.split("YOUR CURRENT REASONING:", 1)[-1]
        return seg.split("AVAILABLE COMMANDS:", 1)[0]
    label_in_passed = sum(1 for c in calls if c["call_kind"] == "action"
                          and CONF_LABEL.search(_reasoning_section(c.get("prompt_templated", ""))))
    B(label_in_passed == 0, "no confidence label in the passed thought (action prompt reasoning) (%d found)" % label_in_passed)
else:  # entangled
    miss = [s for s in steps if s.get("U_T_verbalized") is None
            and "thought_confidence_parse_failed" not in (s.get("skip_reasons") or [])]
    B(not miss, "THOUGHT_CONFIDENCE parsed or skip logged, every step (%d unaccounted)" % len(miss))
    fmt_ok = all(("THOUGHT_CONFIDENCE:" in c.get("prompt_templated", "")
                  and "ACTION_CONFIDENCE:" in c.get("prompt_templated", "")) for c in calls)
    B(fmt_ok, "4-label format (THOUGHT/THOUGHT_CONFIDENCE/ACTION/ACTION_CONFIDENCE) in every joint prompt")
    midcalls = [c for c in calls if c["step_idx"] >= 2]
    def _hist(c):
        return c.get("prompt_templated", "").split("ENVIRONMENT HISTORY:")[-1].split("AVAILABLE COMMANDS")[0]
    hist_ok = all("> " in _hist(c) for c in midcalls) if midcalls else True
    B(hist_ok, "history carries prior action+observation from step 2 on")
    retains_thought = any("CONFIDENCE:" in _hist(c) for c in midcalls)
    W("history retention: %s" % ("full/AUQ (thought+confidence persisted)" if retains_thought
                                 else "action+observation only (default)"))

# 8. bad-step rate (empty action)
empty = sum(1 for s in steps if not (s.get("action_parsed") or "").strip())
B(empty <= max(1, len(steps) // 10), "empty-action rate <=10%% (%d/%d)" % (empty, len(steps)))

# 9. context-overflow episodes (graceful guard fired) — a warning, not blocking; a high rate
#    means the served context is too small for this arm (entangled accumulates full history).
overflow = [e for e in eps if e.get("terminal_reason") == "context_overflow"]
if overflow:
    W("context_overflow ended %d/%d episodes — served context may be too small for this arm"
      % (len(overflow), len(eps)))

print("=== audit_v2 : %s (%d calls, %d steps, %d episodes) ===" % (arm, len(calls), len(steps), len(eps)))
for m in warn:
    print("  " + m)
for m in blocking:
    print("  " + m)
print("\nGATE: %s  (%d blocking finding%s)" % ("PASS" if not blocking else "FAIL",
                                               len(blocking), "" if len(blocking) == 1 else "s"))
sys.exit(0 if not blocking else 1)
