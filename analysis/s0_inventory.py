#!/usr/bin/env python3
"""S0 — repo/state inventory.  Spec: docs/specs/S0_SPEC.md

Builds runs/manifest.json: the file every later stage reads to size itself and
writes its spec hash into.  Computes no scientific quantity; inventories and halts.

Read-only with respect to result/.
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys

SPEC = "docs/specs/S0_SPEC.md"

# Label columns S0 requires; absence is STOP condition 1 (spec §STOP).
REQUIRED_LABEL_COLS = ["A1", "A2", "A3", "A4", "y_tier_b", "y_env",
                       "y_ensemble", "in_matrix"]

# Scripts later stages name.  Missing ones are recorded, not fatal — a stage that
# needs one halts on its own branch (ground rule 6).
TRACKED_SCRIPTS = [
    "analysis/gate2b_cut_transfer.py", "analysis/gate2b1_indexed_cut.py",
    "analysis/crossprobe_matrix_auroc.py", "analysis/uncertainty_levels.py",
    "analysis/percentile_consistency.py", "analysis/verdict_vs_value.py",
    "analysis/selfassess_auroc.py", "analysis/selfassess_table.py",
    "analysis/ptrue_binary_consensus.py", "analysis/gate1_manifest.py",
    "analysis/gate1_assemble.py", "analysis/s0_inventory.py",
]

# Inherited throughput; §1 requires a 500-step probe before any GPU stage sizes
# itself, so this ships flagged unverified and no stage may size against it as-is.
THROUGHPUT_INHERITED = {"assessments": 3300, "minutes": 5, "device": "A100",
                        "verified": False,
                        "note": "500-step probe required before any GPU stage sizes itself"}


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def count_lines(path, buf=1 << 22):
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            n += b.count(b"\n")
    return n


def file_record(path, want_sha=True):
    st = os.stat(path)
    r = {"path": path, "bytes": st.st_size, "mtime": int(st.st_mtime)}
    r["lines"] = count_lines(path)
    r["sha256"] = sha256(path) if want_sha else None
    return r


def scan_cells(pivot, want_sha=True):
    """Enumerate self and cross cells.  Returns (cells, shard_provenance)."""
    cells, shards = [], []
    for dataset in sorted(os.listdir(pivot)):
        dpath = os.path.join(pivot, dataset)
        if not os.path.isdir(dpath) or dataset == "crossprobe":
            continue
        for model in sorted(os.listdir(dpath)):
            mpath = os.path.join(dpath, model)
            if not os.path.isdir(mpath):
                continue
            files = {}
            for fname, scope in (("probes.aggtrue.jsonl", "AGG-true"),
                                 ("probes.jsonl", "SPLIT"),
                                 ("judge.jsonl", "labels"),
                                 ("uq.jsonl", "generation")):
                fp = os.path.join(mpath, fname)
                if os.path.exists(fp):
                    files[scope] = file_record(fp, want_sha)
            if files:
                cells.append({"family": "self", "dataset": dataset,
                              "target": model, "assessor": model, "files": files})

    cpath = os.path.join(pivot, "crossprobe")
    if os.path.isdir(cpath):
        for dataset in sorted(os.listdir(cpath)):
            dpath = os.path.join(cpath, dataset)
            if not os.path.isdir(dpath):
                continue
            for target in sorted(os.listdir(dpath)):
                tpath = os.path.join(dpath, target)
                if not os.path.isdir(tpath):
                    continue
                by_assessor = {}
                for fname in sorted(os.listdir(tpath)):
                    if not fname.startswith("ptrue.") or not fname.endswith(".jsonl"):
                        continue
                    stem = fname[len("ptrue."):-len(".jsonl")]
                    # stem is "<assessor>.response" / "<assessor>.stages" for merged
                    # output, "<assessor>.response.w3" for a worker shard.  Model
                    # names contain dots, so split from the RIGHT and never assume
                    # field count (the f.split('.')[1] bug).
                    parts = stem.rsplit(".", 1)
                    if len(parts) == 2 and parts[1].startswith("w") and parts[1][1:].isdigit():
                        shards.append(os.path.join(tpath, fname))
                        continue
                    if len(parts) != 2 or parts[1] not in ("response", "stages"):
                        continue
                    assessor, kind = parts
                    scope = "AGG-true" if kind == "response" else "SPLIT"
                    by_assessor.setdefault(assessor, {})[scope] = file_record(
                        os.path.join(tpath, fname), want_sha)
                for assessor, files in sorted(by_assessor.items()):
                    cells.append({"family": "cross", "dataset": dataset,
                                  "target": target, "assessor": assessor,
                                  "files": files})
    return cells, shards


def scan_labels(csv_path):
    """Column presence + per-arm construct counts.  Inventory only: no rates."""
    if not os.path.exists(csv_path):
        return {"present": False}
    with open(csv_path) as f:
        r = csv.DictReader(f)
        cols = list(r.fieldnames or [])
        missing = [c for c in REQUIRED_LABEL_COLS if c not in cols]
        arms = {}
        total = 0
        for x in r:
            total += 1
            key = "%s/%s" % (x.get("dataset", ""), x.get("model", ""))
            a = arms.setdefault(key, {"steps": 0, "in_matrix": 0,
                                      "violation": 0, "outcome": 0,
                                      "judgment": 0, "y_env_1": 0,
                                      "y_env_0": 0, "y_env_null": 0})
            a["steps"] += 1
            if x.get("in_matrix") == "1":
                a["in_matrix"] += 1
            # A30 constructs.  Violation = A1/A2/A3 fired.  Outcome = A4 or any
            # Tier-B verdict.  Judgment = an ensemble label exists.  These overlap
            # by construction and are counted independently, not partitioned.
            if any(x.get(k) == "1" for k in ("A1", "A2", "A3")):
                a["violation"] += 1
            if x.get("A4") == "1" or x.get("y_tier_b", "") != "":
                a["outcome"] += 1
            if x.get("y_ensemble", "") != "":
                a["judgment"] += 1
            ye = x.get("y_env", "")
            a["y_env_1" if ye == "1" else "y_env_0" if ye == "0" else "y_env_null"] += 1
    return {"present": True, "path": csv_path, "columns": cols,
            "missing_required": missing, "rows": total, "arms": arms}


def gate2_referenced_cells(table_path):
    """(dataset, assessor, target) triples an existing gate-2 table depends on."""
    if not os.path.exists(table_path):
        return []
    out = []
    with open(table_path) as f:
        for x in csv.DictReader(f):
            out.append((x["dataset"], x["assessor"], x["target"]))
    return out


def gpus():
    try:
        q = ("index,name,memory.total,memory.used,memory.free,utilization.gpu")
        r = subprocess.run(["nvidia-smi", "--query-gpu=" + q,
                            "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return {"available": False, "error": r.stderr.strip()[:200]}
        devs = []
        for line in r.stdout.strip().splitlines():
            p = [c.strip() for c in line.split(",")]
            devs.append({"index": int(p[0]), "name": p[1],
                         "mem_total_mib": int(p[2]), "mem_used_mib": int(p[3]),
                         "mem_free_mib": int(p[4]), "util_pct": int(p[5])})
        return {"available": True, "devices": devs}
    except Exception as e:                                  # noqa: BLE001
        return {"available": False, "error": repr(e)[:200]}


def env_txt(path):
    lines = ["python %s" % sys.version.replace("\n", " ")]
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                           capture_output=True, text=True, timeout=180)
        lines += r.stdout.strip().splitlines()
    except Exception as e:                                  # noqa: BLE001
        lines.append("pip freeze failed: %r" % (e,))
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, timeout=30)
        lines.insert(0, "git HEAD %s" % r.stdout.strip())
    except Exception:                                       # noqa: BLE001
        pass
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return len(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--gate2-table",
                    default="figures/tables_gate2b1/gate2b1_cells_AGG-true_full.csv")
    ap.add_argument("--outdir", default="runs")
    ap.add_argument("--summary", default="S0_SUMMARY.md")
    ap.add_argument("--no-sha", action="store_true",
                    help="skip sha256 (size+lines only) — pin is weaker, recorded as such")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    mpath = os.path.join(a.outdir, "manifest.json")
    if os.path.exists(mpath) and not a.force:
        try:
            if json.load(open(mpath)).get("status") in ("OK", "STOP"):
                print("S0 already complete -> %s (use --force to rebuild)" % mpath)
                return 0
        except Exception:                                   # noqa: BLE001
            pass

    print("S0: scanning %s ..." % a.pivot)
    cells, shards = scan_cells(a.pivot, want_sha=not a.no_sha)
    print("S0: %d cells, %d worker shards" % (len(cells), len(shards)))

    labels = scan_labels(a.labels)
    scripts = {}
    for s in TRACKED_SCRIPTS:
        scripts[s] = {"present": os.path.exists(s),
                      "sha256": sha256(s) if os.path.exists(s) else None}

    # ---- STOP conditions ------------------------------------------------
    stops = []
    if not labels.get("present"):
        stops.append({"cond": 1, "detail": "labels file absent: %s" % a.labels})
    elif labels["missing_required"]:
        stops.append({"cond": 1, "detail": "label columns missing: %s"
                      % ",".join(labels["missing_required"])})

    have = set()
    for c in cells:
        have.add((c["dataset"], c["assessor"], c["target"]))
    absent = [t for t in gate2_referenced_cells(a.gate2_table) if t not in have]
    if absent:
        stops.append({"cond": 2, "detail": "gate-2 table references %d cells with no "
                      "score file on disk" % len(absent),
                      "cells": ["%s|%s->%s" % t for t in sorted(set(absent))]})

    status = "STOP" if stops else "OK"
    spec_sha = sha256(SPEC) if os.path.exists(SPEC) else None

    manifest = {
        "stage": "S0", "status": status, "spec": SPEC, "spec_sha256": spec_sha,
        "seed": 13,
        "stop_conditions": stops,
        "cells": cells,
        "worker_shards": {"count": len(shards), "note": "provenance only; never counted as cells"},
        "labels": labels,
        "scripts": scripts,
        "gpu": gpus(),
        "throughput": THROUGHPUT_INHERITED,
        "specs_recorded": {},   # later stages write {stage: sha256} here
    }
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=False)
    nenv = env_txt(os.path.join(a.outdir, "env.txt"))

    # ---- summary --------------------------------------------------------
    nself = sum(1 for c in cells if c["family"] == "self")
    ncross = sum(1 for c in cells if c["family"] == "cross")
    nbytes = sum(fr["bytes"] for c in cells for fr in c["files"].values())
    nlines = sum(fr["lines"] for c in cells for fr in c["files"].values())
    g = manifest["gpu"]
    L = []
    L.append("# S0 SUMMARY — repo/state inventory\n")
    L.append("Spec: `%s` (sha256 `%s`)\n" % (SPEC, (spec_sha or "ABSENT")[:16]))
    L.append("**Status: %s**\n" % status)
    L.append("## Cells\n")
    L.append("| family | cells |")
    L.append("|---|---|")
    L.append("| self | %d |" % nself)
    L.append("| cross | %d |" % ncross)
    L.append("| **total** | **%d** |" % len(cells))
    L.append("")
    L.append("%d score files, %.1f GB, %s lines. %d worker shards recorded as "
             "provenance only.\n" % (
                 sum(len(c["files"]) for c in cells), nbytes / 1e9,
                 "{:,}".format(nlines), len(shards)))
    L.append("## Labels\n")
    if labels.get("present"):
        L.append("`%s` — %s rows, %d columns, required provenance columns %s.\n"
                 % (a.labels, "{:,}".format(labels["rows"]), len(labels["columns"]),
                    "ALL PRESENT" if not labels["missing_required"]
                    else "MISSING " + ",".join(labels["missing_required"])))
        L.append("| arm | steps | in_matrix | violation | outcome | judgment |")
        L.append("|---|---|---|---|---|---|")
        for k in sorted(labels["arms"]):
            v = labels["arms"][k]
            L.append("| %s | %d | %d | %d | %d | %d |"
                     % (k, v["steps"], v["in_matrix"], v["violation"],
                        v["outcome"], v["judgment"]))
        L.append("\nConstruct counts overlap by construction (a step can be both a "
                 "violation and an outcome); they are an inventory, not a partition.\n")
    else:
        L.append("ABSENT — STOP condition 1.\n")
    L.append("## Capacity\n")
    if g.get("available"):
        L.append("| gpu | name | free MiB | util pct |")
        L.append("|---|---|---|---|")
        for d in g["devices"]:
            L.append("| %d | %s | %d | %d |" % (d["index"], d["name"],
                                                d["mem_free_mib"], d["util_pct"]))
    else:
        L.append("nvidia-smi unavailable: %s" % g.get("error", "?"))
    L.append("")
    L.append("Throughput constant %d assessments / %d min / %s is INHERITED and "
             "**unverified** — §1 requires a 500-step probe before any GPU stage "
             "sizes itself against it.\n"
             % (THROUGHPUT_INHERITED["assessments"], THROUGHPUT_INHERITED["minutes"],
                THROUGHPUT_INHERITED["device"]))
    L.append("## STOP\n")
    if stops:
        for s in stops:
            L.append("- **condition %d** — %s" % (s["cond"], s["detail"]))
            for c in s.get("cells", [])[:20]:
                L.append("  - `%s`" % c)
    else:
        L.append("None. Conditions checked: (1) label provenance columns present; "
                 "(2) every cell referenced by `%s` has a score file on disk.\n"
                 % a.gate2_table)
    L.append("\n`runs/manifest.json` written (%d env lines in `runs/env.txt`). "
             "Later stages record their spec sha256 under `specs_recorded`.\n" % nenv)
    with open(a.summary, "w") as f:
        f.write("\n".join(L) + "\n")

    print("S0 status=%s  cells=%d  -> %s, %s" % (status, len(cells), mpath, a.summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
