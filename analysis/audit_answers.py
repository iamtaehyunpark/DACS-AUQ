#!/usr/bin/env python3
"""A35 answer-distribution audit — run over any scoring output, blocking.

The tripwire (analysis/answer_tripwire.py) is the in-process form, used by drivers
this repo owns.  This is the out-of-process form: it reads finished or in-progress
JSONL and applies the same rule, so a pass produced by a script we should NOT edit
mid-run (src/run_probes.py, with live workers holding it open) is still covered.

Rule: over the first 100 scored records of each file, no single top-1 token may
exceed 95% share.  Exit non-zero if any file trips, so this can gate a stage.

This exists because of the S4 void: 44,573 records with route=main, zero errors, a
clean coverage table, and `The` as the top-1 token on every one of them.
"""
import argparse
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from answer_tripwire import WINDOW, MAX_SHARE      # noqa: E402


def audit(path, key="first_token_top", kind_field="probe_kind", kind="ptrue"):
    counts = collections.Counter()
    n = u_ok = 0
    with open(path) as f:
        for line in f:
            if n >= WINDOW:
                break
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if kind_field in r and r.get(kind_field) != kind:
                continue
            top = r.get(key)
            if not top:
                continue
            n += 1
            if r.get("U") is not None:
                u_ok += 1
            best = max(top, key=lambda t: t["logprob"])
            counts[(best.get("token") or "").strip()] += 1
    if not n:
        return {"path": path, "n": 0, "status": "EMPTY"}
    tok, c = counts.most_common(1)[0]
    share = c / float(n)
    return {"path": path, "n": n, "u_rate": u_ok / float(n), "top_token": tok,
            "share": share, "dist": dict(counts.most_common(4)),
            "status": "TRIPPED" if share > MAX_SHARE else "OK"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("globs", nargs="+", help="jsonl paths or globs")
    ap.add_argument("--key", default="first_token_top")
    a = ap.parse_args()
    files = []
    for g in a.globs:
        files.extend(sorted(glob.glob(g)))
    if not files:
        sys.exit("no files matched")
    bad = []
    print("%-58s %5s %7s %7s  %s" % ("file", "n", "U-rate", "share", "top-1 dist"))
    for f in files:
        r = audit(f, a.key)
        if r["n"] == 0:
            print("%-58s %5s" % (os.path.basename(f)[:58], "EMPTY"))
            continue
        print("%-58s %5d %6.0f%% %6.2f  %s%s"
              % (os.path.basename(f)[:58], r["n"], 100 * r["u_rate"], r["share"],
                 r["dist"], "   <-- TRIPPED" if r["status"] == "TRIPPED" else ""))
        if r["status"] == "TRIPPED":
            bad.append(r)
    if bad:
        print("\nA35 AUDIT FAILED: %d file(s) exceed the %.0f%% single-token limit."
              % (len(bad), 100 * MAX_SHARE))
        print("These records are not answers. Do not treat them as data.")
        return 1
    print("\nA35 audit clear: %d files, no single top-1 token above %.0f%%."
          % (len(files), 100 * MAX_SHARE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
