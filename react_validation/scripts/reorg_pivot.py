#!/usr/bin/env python3
"""Collect the ENTANGLED raw data into result/pivot/<dataset>/<exact model name>/.

The corpus grew one arm at a time, so it ended up spread across result/models4,
result/llama3.3-70b, result/qwen3.6-35b/e1b, result/deepseek4flash, result/hotpot_*
and runs/hotpot_500, with per-arm filename conventions (uq_entangled_l70.jsonl,
uq_hotpot_entangled.jsonl, uq_entangled_e1.jsonl ...). The pivot treats
(dataset x model) as the unit, so the layout should too.

Model directories use the EXACT upstream model name, not the internal short tag:
l70/llama70b -> Llama-3.3-70B-Instruct, e1 -> Qwen3.6-35B-A3B, ds -> deepseek-v4-flash.
Short tags are ambiguous across environments and lose the version (v0.3, 3.3, 3.6).

Filenames are normalised so downstream code needs no per-arm special-casing:
  uq.jsonl · probes.jsonl · probes.aggtrue_ptrue.jsonl ·
  probes.qwenjudge.jsonl · probes.qwenjudge.aggtrue_ptrue.jsonl · judge.jsonl

Uses os.rename (same filesystem) — instant and needs no free space, which matters
on a disk at 87%. Decoupled data is left where it is: this is an entangled pivot.

  reorg_pivot.py            dry run, prints the plan
  reorg_pivot.py --apply    perform the moves and write MANIFEST.json
"""
import json
import os
import sys

RD = "/data5/kje/MULTIAGENT/DACS-AUQ/react_validation"

# (dataset, exact model name, source dir, arm tag)
# arm tag None => whole-directory arm (the hotpot_* dirs hold one arm each)
ARMS = [
    ("alfworld", "Phi-4-mini-instruct",       "result/models4",          "phi4mini"),
    ("alfworld", "gemma-3-4b-it",             "result/models4",          "gemma4b"),
    ("alfworld", "Mistral-7B-Instruct-v0.3",  "result/models4",          "mistral7b"),
    ("alfworld", "Llama-3.3-70B-Instruct",    "result/llama3.3-70b",     "l70"),
    ("alfworld", "Qwen3.6-35B-A3B",           "result/qwen3.6-35b/e1b",  "e1"),
    ("alfworld", "deepseek-v4-flash",         "result/deepseek4flash",   "ds"),
    ("hotpotqa", "Phi-4-mini-instruct",       "result/hotpot_phi4mini",  None),
    ("hotpotqa", "gemma-3-4b-it",             "result/hotpot_gemma4b",   None),
    ("hotpotqa", "Mistral-7B-Instruct-v0.3",  "result/hotpot_mistral7b", None),
    ("hotpotqa", "Llama-3.3-70B-Instruct",    "result/hotpot_llama70b",  None),
    ("hotpotqa", "Qwen3.6-35B-A3B",           "runs/hotpot_500",         None),
]

# result/hotpot_phi4mini_smoke is deliberately absent: a 20-episode pipeline test.


def target_name(fname):
    """Normalised destination filename, or None to leave the file alone."""
    # Exactly three files per (dataset x model) cell: the trajectories, the
    # self-probe scores, and the judge labels. Everything else stays where it is —
    # .qwenjudge.* are cross-probe OUTPUTS (a different assessor reading this arm,
    # so they belong to the assessor x target matrix, not to the arm's raw data),
    # .aggtrue_ptrue.* is a secondary probe scope, and .bak is a repair snapshot.
    if not fname.endswith(".jsonl"):
        return None
    stem = fname[: -len(".jsonl")]
    if ".qwenjudge" in stem or ".aggtrue_ptrue" in stem:
        return None
    head = stem.split("_")[0]
    if head not in ("uq", "probes", "judge"):
        return None
    return head + ".jsonl"


def is_entangled(fname, tag):
    if ".w" in fname and fname.split(".w")[-1].split(".")[0].isdigit():
        return False          # per-worker shard, superseded by the merged file
    if "entangled" not in fname:
        return False
    if tag and tag not in fname:
        return False
    return True


def plan():
    moves, skipped = [], []
    for dataset, model, src, tag in ARMS:
        src_abs = os.path.join(RD, src)
        if not os.path.isdir(src_abs):
            skipped.append("MISSING SOURCE %s" % src)
            continue
        dst_rel = os.path.join("result/pivot", dataset, model)
        for fname in sorted(os.listdir(src_abs)):
            path = os.path.join(src_abs, fname)
            if not os.path.isfile(path):
                continue
            if not is_entangled(fname, tag):
                continue
            new = target_name(fname)
            if not new:
                skipped.append("UNCLASSIFIED %s/%s" % (src, fname))
                continue
            moves.append((os.path.join(src, fname), os.path.join(dst_rel, new)))
    return moves, skipped


def main():
    apply_it = "--apply" in sys.argv
    moves, skipped = plan()

    dests = {}
    for old, new in moves:
        dests.setdefault(new, []).append(old)
    collisions = {k: v for k, v in dests.items() if len(v) > 1}
    if collisions:
        print("COLLISIONS — refusing to run:", file=sys.stderr)
        for k, v in collisions.items():
            print("  %s <- %s" % (k, v), file=sys.stderr)
        sys.exit(1)

    cur = None
    for old, new in moves:
        d = os.path.dirname(new)
        if d != cur:
            print("\n%s/" % d)
            cur = d
        size = os.path.getsize(os.path.join(RD, old)) / 1e9
        print("  %-56s <- %s  (%.2f GB)" % (os.path.basename(new), old, size))
    for s in skipped:
        print("  skip: %s" % s)
    print("\n%d files" % len(moves))

    if not apply_it:
        print("\ndry run — pass --apply to perform the moves")
        return

    manifest = []
    for old, new in moves:
        src, dst = os.path.join(RD, old), os.path.join(RD, new)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            print("  exists, skipping: %s" % new)
            continue
        os.rename(src, dst)
        manifest.append({"from": old, "to": new})
    mpath = os.path.join(RD, "result/pivot/MANIFEST.json")
    with open(mpath, "w") as fo:
        json.dump({"moves": manifest}, fo, indent=2)
    print("\nmoved %d files; manifest -> result/pivot/MANIFEST.json" % len(manifest))


if __name__ == "__main__":
    main()
