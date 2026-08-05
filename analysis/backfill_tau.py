#!/usr/bin/env python3
"""A12.2 tau backfill.

Read a Phase-1 UQ log (arg) and, for every `kind:"step"` record, add
`tau: tau_dict(action_parsed)` (the transition-type label I/W/R/C derived purely from the
environment action grammar; unrecognized -> None, which is a real coverage signal, never guessed).
Non-step records are copied through unchanged. Writes an augmented `<log>_tau.jsonl` next to the
input and reports how many step records received a tau plus the count/list of any `action_parsed`
that mapped to None.

Usage:
  backfill_tau.py <uq_log.jsonl>
"""
import json
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
from tau_map import tau_dict  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: backfill_tau.py <uq_log.jsonl>")
    inp = sys.argv[1]
    root, ext = os.path.splitext(inp)
    out = root + "_tau" + ext
    if os.path.abspath(inp) == os.path.abspath(out):
        sys.exit("refusing to overwrite input")

    n_lines = n_steps = n_tau = n_none = 0
    none_actions = Counter()
    with open(inp) as fi, open(out, "w") as fo:
        for line in fi:
            s = line.strip()
            if not s:
                continue
            r = json.loads(s)
            if r.get("kind") == "step":
                n_steps += 1
                act = r.get("action_parsed")
                tau = tau_dict(act)
                r["tau"] = tau
                if tau is None:
                    n_none += 1
                    none_actions[act if act is not None else "<None>"] += 1
                else:
                    n_tau += 1
            fo.write(json.dumps(r) + "\n")
            n_lines += 1

    print("input:  %s" % inp)
    print("output: %s" % out)
    print("lines: %d | step records: %d | tau assigned: %d | tau None (unrecognized): %d"
          % (n_lines, n_steps, n_tau, n_none))
    if none_actions:
        print("unrecognized action_parsed -> tau None (%d distinct):" % len(none_actions))
        for act, c in none_actions.most_common():
            print("  %5d  %r" % (c, act))
    else:
        print("no unrecognized actions: full tau coverage over step records")


if __name__ == "__main__":
    main()
