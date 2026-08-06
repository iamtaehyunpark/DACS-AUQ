#!/usr/bin/env python3
"""S1d — gate-2 reruns (b1 / A28 / A28.1) on L2 labels, per A30 construct.

Spec: docs/specs/S1_SPEC.md §5.  "Primaries unchanged from their specs; only the
label input moves" — so this does NOT reimplement the gates.  It swaps the label
source under the banked scripts and calls them, which is the only way the L1
reproduction check in spec §7 can mean anything.

The swap is a monkeypatch of gate2b_cut_transfer.load_labels.  That function is the
single point where every gate reads labels: it maps a judge.jsonl path to
{(task_id, step_idx): P(correct)}, and callers test `< 0.5` for incorrect.  The
replacement keys off the (dataset, target) encoded in the path and returns 0.0/1.0
from the construct.  Hard labels: the gate arms fit balanced-accuracy cuts and never
consume the soft weight, so nothing is silently dropped by discarding it.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate2b_cut_transfer as G          # noqa: E402
import s1_labels as SL                   # noqa: E402

SPEC = "docs/specs/S1_SPEC.md"


def path_to_arm(path):
    """result/pivot/<dataset>/<model>/judge.jsonl -> (dataset, model)."""
    parts = os.path.normpath(path).split(os.sep)
    try:
        return parts[-3], parts[-2]
    except IndexError:
        return None, None


def install(construct, labels_csv, in_matrix_only=True):
    """Point every gate's label reader at an A30 construct.  Returns the arm map so
    callers can assert coverage rather than discover an empty join as a zero result."""
    by_arm = SL.load(labels_csv, construct, in_matrix_only=in_matrix_only)

    def load_labels(path):
        ds, model = path_to_arm(path)
        steps = by_arm.get((ds, model))
        if not steps:
            return {}
        # gate code reads P(correct) and calls `< 0.5` incorrect; y=1 is incorrect.
        return {k: (0.0 if y == 1 else 1.0) for k, (y, _w) in steps.items()}

    G.load_labels = load_labels
    return by_arm


def run(script, args, log):
    """Run a gate script in-process-free (subprocess) so its own __main__ guard,
    argument parsing and console output are exercised exactly as when it was banked."""
    cmd = [sys.executable, script] + args
    with open(log, "w") as f:
        f.write("$ %s\n\n" % " ".join(cmd))
        f.flush()
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--scope", default="AGG-true")
    ap.add_argument("--outdir", default="tables_S1")
    ap.add_argument("--figdir", default="figures_S1")
    ap.add_argument("--constructs", default=",".join(SL.CONSTRUCTS))
    ap.add_argument("--labelpass", default="L2")
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(a.outdir, exist_ok=True)
    os.makedirs(a.figdir, exist_ok=True)

    for c in a.constructs.split(","):
        if not c:
            continue
        tag = "%s_%s" % (a.labelpass, c.replace("+", "-"))
        od = os.path.join(a.outdir, tag)
        fd = os.path.join(a.figdir, tag)
        os.makedirs(od, exist_ok=True)
        os.makedirs(fd, exist_ok=True)
        env = os.environ.copy()
        env["S1_CONSTRUCT"] = c
        env["S1_LABELS"] = a.labels
        env["S1_IN_MATRIX"] = "1"
        # The gate scripts import gate2b_cut_transfer themselves; the patch has to be
        # in THEIR process, so it is installed via sitecustomize-style bootstrap.
        boot = os.path.join(od, "_s1_bootstrap.py")
        with open(boot, "w") as f:
            f.write(
                "import os, sys\n"
                "sys.path.insert(0, %r)\n"
                "import s1_gate2\n"
                "s1_gate2.install(os.environ['S1_CONSTRUCT'], os.environ['S1_LABELS'],\n"
                "                 os.environ.get('S1_IN_MATRIX') == '1')\n" % here)
        env["PYTHONSTARTUP"] = boot

        for gate, script, extra in (
            ("A28", os.path.join(here, "gate2b_cut_transfer.py"),
             ["--pivot", a.pivot, "--scope", a.scope, "--outdir", od]),
            ("A28.1", os.path.join(here, "gate2b1_indexed_cut.py"),
             ["--pivot", a.pivot, "--scope", a.scope, "--outdir", od,
              "--figdir", fd]),
        ):
            log = os.path.join(od, "S1d_%s_console.txt" % gate.replace(".", "_"))
            cmd = [sys.executable, "-c",
                   "import runpy,os,sys;"
                   "sys.path.insert(0, %r);"
                   "import s1_gate2;"
                   "s1_gate2.install(os.environ['S1_CONSTRUCT'], os.environ['S1_LABELS'],"
                   " os.environ.get('S1_IN_MATRIX')=='1');"
                   "sys.argv=[%r]+%r;"
                   "runpy.run_path(%r, run_name='__main__')"
                   % (here, script, extra, script)]
            with open(log, "w") as f:
                f.write("$ construct=%s %s %s\n\n" % (c, script, " ".join(extra)))
                f.flush()
                rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
            print("[%s] %-20s rc=%d -> %s" % (c, gate, rc, log))
        os.remove(boot)
    print("-> %s" % a.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
