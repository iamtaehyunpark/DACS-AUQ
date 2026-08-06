#!/usr/bin/env python3
"""Gate-1 input manifest — pin every raw file the gate reads to an exact byte length.

The corpus is live: at the time gate 1 was run, `judge_hotpot.py` and eight
`run_probes.py` workers were still appending to the `Qwen3.5-*` arms. Appending to a
JSONL file that a later phase re-reads would make the gate non-reproducible — Phase 2
and Phase 5 could disagree for no reason but wall-clock.

So every input is recorded here as (size, sha256, mtime) and every gate-1 reader takes
only the first `size` bytes. A concurrent append is then invisible; a rewrite of
already-written bytes is caught by the hash on re-verification.

  gate1_manifest.py --pivot DIR --out reports/gate1/input_manifest.json
  gate1_manifest.py --verify --out reports/gate1/input_manifest.json
"""
import argparse
import hashlib
import json
import os
import sys

FILES = ("uq.jsonl", "judge.jsonl", "probes.jsonl", "probes.aggtrue.jsonl")


def sha256_prefix(path, nbytes):
    h = hashlib.sha256()
    left = nbytes
    with open(path, "rb") as f:
        while left > 0:
            chunk = f.read(min(1 << 22, left))
            if not chunk:
                break
            h.update(chunk)
            left -= len(chunk)
    return h.hexdigest()


def collect(pivot):
    out = {}
    for dataset in ("alfworld", "hotpotqa"):
        d = os.path.join(pivot, dataset)
        if not os.path.isdir(d):
            continue
        for model in sorted(os.listdir(d)):
            for fname in FILES:
                p = os.path.join(d, model, fname)
                if not os.path.isfile(p):
                    continue
                st = os.stat(p)
                rel = os.path.relpath(p, pivot)
                sys.stderr.write("hashing %s (%.2f GB)\n" % (rel, st.st_size / 1e9))
                sys.stderr.flush()
                out[rel] = {"size": st.st_size, "mtime": st.st_mtime,
                            "sha256": sha256_prefix(p, st.st_size)}
    return out


def load(manifest_path, pivot):
    """rel-path -> pinned byte length, for the readers."""
    blob = json.load(open(manifest_path))
    if os.path.abspath(blob["pivot"]) != os.path.abspath(pivot):
        raise SystemExit("manifest pivot %s != requested %s" % (blob["pivot"], pivot))
    return {k: v["size"] for k, v in blob["files"].items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--out", default="reports/gate1/input_manifest.json")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.verify:
        blob = json.load(open(args.out))
        pivot = blob["pivot"]
        bad, grown = [], []
        for rel, rec in sorted(blob["files"].items()):
            p = os.path.join(pivot, rel)
            if not os.path.isfile(p):
                bad.append("%s MISSING" % rel)
                continue
            size = os.path.getsize(p)
            if size != rec["size"]:
                grown.append("%s %d -> %d bytes" % (rel, rec["size"], size))
            if sha256_prefix(p, rec["size"]) != rec["sha256"]:
                bad.append("%s PREFIX HASH CHANGED — pinned bytes were rewritten" % rel)
        for g in grown:
            print("grew (harmless, reads are pinned): %s" % g)
        for b in bad:
            print("FAIL: %s" % b)
        print("verify: %d files, %d grown, %d corrupt" % (len(blob["files"]), len(grown), len(bad)))
        sys.exit(1 if bad else 0)

    files = collect(args.pivot)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"pivot": os.path.abspath(args.pivot), "files": files}, f, indent=2)
    print("wrote %s (%d files)" % (args.out, len(files)))


if __name__ == "__main__":
    main()
