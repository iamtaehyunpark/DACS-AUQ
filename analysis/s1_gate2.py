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
    """Point every gate's label reader at an A30 construct.  Returns the replacement
    function so the caller can also bind it onto modules that define their OWN
    load_labels rather than importing the shared one -- verdict_vs_value.py does, and
    patching only gate2b_cut_transfer would have left b1 silently reading L1.

    construct == "L1" installs nothing: the gates read judge.jsonl exactly as when
    they were banked.  That is the reproduction control of spec section 7 -- if the
    L1 pass does not match the banked tables to 0.001, the harness is wrong and no
    L2 number from it can be trusted."""
    if construct == "L1":
        return None
    by_arm = SL.load(labels_csv, construct, in_matrix_only=in_matrix_only)

    def load_labels(path):
        ds, model = path_to_arm(path)
        steps = by_arm.get((ds, model))
        if not steps:
            return {}
        # gate code reads P(correct) and calls `< 0.5` incorrect; y=1 is incorrect.
        return {k: (0.0 if y == 1 else 1.0) for k, (y, _w) in steps.items()}

    G.load_labels = load_labels
    return load_labels


RUNNER = (
    # (gate, module, extra argv)  -- b1 is verdict_vs_value, the gate-2b1 primary
    ("b1", "verdict_vs_value", ["--pivot", "{pivot}", "--scope", "{scope}",
                                "--out", "{od}/S1d_b1.csv"]),
    ("A28", "gate2b_cut_transfer", ["--pivot", "{pivot}", "--scope", "{scope}",
                                    "--outdir", "{od}"]),
    ("A28.1", "gate2b1_indexed_cut", ["--pivot", "{pivot}", "--scope", "{scope}",
                                      "--outdir", "{od}", "--figdir", "{fd}"]),
)

# The gate modules are invoked by IMPORTING them and calling main(), never by
# re-executing the file.  runpy.run_path would build a fresh module object whose
# `import gate2b_cut_transfer` resolves to the cached-but-then-shadowed module, so
# the label patch would silently not apply and every "L2" number would really be L1.
CHILD = r"""
import os, sys, importlib
sys.path.insert(0, {here!r})
import s1_gate2
patched = s1_gate2.install(os.environ['S1_CONSTRUCT'], os.environ['S1_LABELS'],
                           os.environ.get('S1_IN_MATRIX') == '1')
m = importlib.import_module({mod!r})
if patched is not None and 'load_labels' in vars(m):
    m.load_labels = patched          # module defines its own reader
if patched is not None:
    import gate2b_cut_transfer as G
    assert G.load_labels is patched, 'label patch did not reach the shared reader'
sys.argv = [{mod!r}] + {argv!r}
sys.exit(m.main() or 0)
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--labels", default="reports/gate1/labels_gate1.csv")
    ap.add_argument("--scope", default="AGG-true")
    ap.add_argument("--outdir", default="tables_S1")
    ap.add_argument("--figdir", default="figures_S1")
    ap.add_argument("--constructs", default=",".join(SL.CONSTRUCTS))
    ap.add_argument("--labelpass", default="L2")
    ap.add_argument("--gates", default="b1,A28,A28.1")
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    want = set(a.gates.split(","))
    results = []

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

        for gate, mod, extra in RUNNER:
            if gate not in want:
                continue
            argv = [x.format(pivot=a.pivot, scope=a.scope, od=od, fd=fd)
                    for x in extra]
            log = os.path.join(od, "S1d_%s_console.txt" % gate.replace(".", "_"))
            code = CHILD.format(here=here, mod=mod, argv=argv)
            with open(log, "w") as f:
                f.write("$ construct=%s gate=%s %s\n\n" % (c, gate, " ".join(argv)))
                f.flush()
                rc = subprocess.call([sys.executable, "-c", code],
                                     stdout=f, stderr=subprocess.STDOUT, env=env)
            results.append((c, gate, rc, log))
            print("[%-20s] %-6s rc=%d -> %s" % (c, gate, rc, log), flush=True)

    bad = [r for r in results if r[2] != 0]
    print("\nS1d: %d runs, %d failed" % (len(results), len(bad)))
    for c, gate, rc, log in bad:
        print("  FAILED %s/%s rc=%d see %s" % (c, gate, rc, log))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
