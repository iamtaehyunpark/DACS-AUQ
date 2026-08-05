#!/usr/bin/env python3
"""One-afternoon contamination extraction (decoupled arm only).

The pilot's decoupled thought completions CONTAIN the chosen action (defect A8 fixes): the whole
completion is the thought span, so many thoughts literally end with the committed command. That
lets the post-hoc thought-stage probes read confidence off a thought that already reveals the
decision, deflating (inflating the *confidence* of) the U_T readings. This script quantifies the
effect.

For each decoupled step it:
  1. reconstructs (task, history, commands, thought, action) EXACTLY as the pilot probe pass did
     (run_probes.group_steps over the frozen UQ log);
  2. TRIMS the thought -- drops trailing line(s) whose normalized form equals an admissible command
     (normalize = lowercase, collapse whitespace, strip surrounding punctuation; admissible list is
     the step's `admissible`); logs `trimmed_bool`;
  3. re-runs the thought-stage probes `ptrue` and `posthoc_numeric` on the TRIMMED thought, reusing
     probes.py with the SAME prompt versions, the SAME seed formula, and the SAME sampling config as
     the pilot probe pass (temp=0, top_p=1.0, top_k=20, presence_penalty=0.0, seed_base=7000 --
     verified from the recorded probe records' record.config), so the ONLY thing that changes is the
     thought text;
  4. pairs U_trimmed against the RECORDED full-thought U (from the probes file) by
     (task_id, step_idx, probe_kind), stage=thought.

Per probe it reports: N paired, mean |U_full - U_trimmed|, mean signed (U_full - U_trimmed),
Pearson correlation, and the trimmed_bool=True vs False split. A markdown table is written to
contamination_report.md.

Env:
  UQ_LOG        (default data/uq_decoupled_30.jsonl)     frozen Phase-1 UQ log (decoupled)
  PROBES_LOG    (default data/probes_decoupled_30.jsonl) recorded full-thought probe log
  OUT_DIR       (default this script's dir)              where outputs are written
  PROBE_MODEL (qwen)  PROBE_BASE_URL (http://localhost:8000/v1)  PROBE_TOKENIZER (Qwen/Qwen3.6-35B-A3B)
  MAX_STEPS     (unset -> all decoupled steps)
"""
import json
import math
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "src")
sys.path.insert(0, _SRC)

import probes            # noqa: E402
import run_probes        # noqa: E402
from openai import OpenAI  # noqa: E402

PROBE_KINDS = ["ptrue", "posthoc_numeric"]
STAGE = "thought"


# --------------------------------------------------------------------------- trimming

def normalize(s):
    """lowercase, collapse whitespace, strip surrounding punctuation/underscores."""
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    s = re.sub(r"^[\W_]+|[\W_]+$", "", s)
    return s


def trim_thought(thought, admissible):
    """Drop trailing line(s) that exactly match (normalized) an admissible command. Trailing blank
    lines exposed by a drop are removed too. Returns (trimmed, trimmed_bool, n_removed)."""
    adm = {na for na in (normalize(a) for a in (admissible or [])) if na}
    lines = thought.split("\n")
    end = len(lines)
    removed = 0
    while end > 0:
        ln = lines[end - 1]
        if ln.strip() == "":
            end -= 1
            continue
        if normalize(ln) in adm:
            end -= 1
            removed += 1
            continue
        break
    trimmed = "\n".join(lines[:end]).rstrip()
    return trimmed, removed > 0, removed


# --------------------------------------------------------------------------- stats

def _finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def summarize(rows):
    """rows: list of (u_full, u_trim). Returns dict of stats."""
    n = len(rows)
    if n == 0:
        return {"n": 0, "mean_abs": None, "mean_signed": None, "corr": None,
                "mean_full": None, "mean_trim": None}
    d = [uf - ut for uf, ut in rows]
    return {
        "n": n,
        "mean_abs": sum(abs(x) for x in d) / n,
        "mean_signed": sum(d) / n,
        "corr": pearson([r[0] for r in rows], [r[1] for r in rows]),
        "mean_full": sum(r[0] for r in rows) / n,
        "mean_trim": sum(r[1] for r in rows) / n,
    }


# --------------------------------------------------------------------------- main

def main():
    uq_log = os.environ.get("UQ_LOG", os.path.join(_HERE, "..", "data", "uq_decoupled_30.jsonl"))
    probes_log = os.environ.get("PROBES_LOG", os.path.join(_HERE, "..", "data", "probes_decoupled_30.jsonl"))
    out_dir = os.environ.get("OUT_DIR", _HERE)
    max_steps = os.environ.get("MAX_STEPS")
    max_steps = int(max_steps) if max_steps else None
    os.makedirs(out_dir, exist_ok=True)

    trimmed_out = os.path.join(out_dir, "contamination_probes_trimmed.jsonl")
    pairs_out = os.path.join(out_dir, "contamination_pairs.jsonl")
    report_out = os.path.join(out_dir, "contamination_report.md")

    # pilot probe-pass config (verified against recorded record.config): only the thought changes.
    cfg = probes.ProbeConfig(
        model=os.environ.get("PROBE_MODEL", "qwen"),
        tokenizer_path=os.environ.get("PROBE_TOKENIZER", "Qwen/Qwen3.6-35B-A3B"),
        base_url=os.environ.get("PROBE_BASE_URL", "http://localhost:8000/v1"),
        temperature=0.0, top_p=1.0, top_k=20, min_p=0.0,
        presence_penalty=0.0, repetition_penalty=1.0, seed_base=7000,
    )
    client = OpenAI(api_key="EMPTY", base_url=cfg.base_url)

    # --- recorded full-thought U lookup -------------------------------------------------
    full = {}   # (task_id, step_idx, probe_kind) -> (U, parse_ok)
    with open(probes_log) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("stage") != STAGE or r.get("probe_kind") not in PROBE_KINDS:
                continue
            full[(r.get("task_id"), r.get("step_idx"), r.get("probe_kind"))] = (r.get("U"), bool(r.get("parse_ok")))

    # --- re-run probes on trimmed thoughts ----------------------------------------------
    records = run_probes._load(uq_log)
    trim_meta = {}   # (task_id, step_idx) -> trimmed_bool
    n_steps = 0
    with open(trimmed_out, "w") as ft:
        for step in run_probes.group_steps(records):
            if max_steps is not None and n_steps >= max_steps:
                break
            n_steps += 1
            admissible = step["ctx"]["commands"].split("\n") if step["ctx"]["commands"] else []
            orig_thought = step["ctx"]["thought"]
            trimmed, trimmed_bool, removed = trim_thought(orig_thought, admissible)
            trim_meta[(step["task_id"], step["step_idx"])] = trimmed_bool

            step2 = dict(step)
            step2["ctx"] = dict(step["ctx"])
            step2["ctx"]["thought"] = trimmed
            try:
                recs = probes.run_step_probes(client, cfg, step2, kinds=PROBE_KINDS, stages=[STAGE])
            except Exception as e:  # never let one step kill the sweep
                sys.stderr.write("ERROR step %s/%s: %r\n" % (step["task_id"], step["step_idx"], e))
                continue
            for pr in recs:
                pr["trimmed_bool"] = trimmed_bool
                pr["n_removed_lines"] = removed
                pr["orig_thought_chars"] = len(orig_thought)
                pr["trimmed_thought_chars"] = len(trimmed)
                ft.write(json.dumps(pr) + "\n")
            ft.flush()
            if n_steps % 50 == 0:
                print("[%d steps re-run] last=%s/%s trimmed=%s" % (
                    n_steps, step["task_id"][:24], step["step_idx"], trimmed_bool))
                sys.stdout.flush()

    # --- gather U_trimmed from what we just wrote ---------------------------------------
    trim = {}   # (task_id, step_idx, probe_kind) -> (U, parse_ok, trimmed_bool)
    with open(trimmed_out) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            trim[(r.get("task_id"), r.get("step_idx"), r.get("probe_kind"))] = (
                r.get("U"), bool(r.get("parse_ok")), bool(r.get("trimmed_bool")))

    # --- pair and compute -----------------------------------------------------------------
    per_probe = {}
    n_trimmed_steps = sum(1 for v in trim_meta.values() if v)
    with open(pairs_out, "w") as fp:
        for kind in PROBE_KINDS:
            all_rows, t_rows, f_rows = [], [], []
            n_full_ok = n_trim_ok = n_both = 0
            for (task_id, step_idx), tb in trim_meta.items():
                fu = full.get((task_id, step_idx, kind))
                tr = trim.get((task_id, step_idx, kind))
                u_full, ok_full = (fu if fu else (None, False))
                u_trim, ok_trim, _tb = (tr if tr else (None, False, tb))
                if ok_full and _finite(u_full):
                    n_full_ok += 1
                if ok_trim and _finite(u_trim):
                    n_trim_ok += 1
                row = {"task_id": task_id, "step_idx": step_idx, "probe_kind": kind,
                       "trimmed_bool": tb, "U_full": u_full, "U_trim": u_trim,
                       "parse_ok_full": ok_full, "parse_ok_trim": ok_trim}
                fp.write(json.dumps(row) + "\n")
                if ok_full and ok_trim and _finite(u_full) and _finite(u_trim):
                    n_both += 1
                    all_rows.append((u_full, u_trim))
                    (t_rows if tb else f_rows).append((u_full, u_trim))
            per_probe[kind] = {
                "n_full_ok": n_full_ok, "n_trim_ok": n_trim_ok, "n_both": n_both,
                "all": summarize(all_rows), "trimmed_true": summarize(t_rows),
                "trimmed_false": summarize(f_rows),
            }

    # --- report ---------------------------------------------------------------------------
    def fmt(x, p=4):
        return "n/a" if x is None else ("%.*f" % (p, x))

    lines = []
    lines.append("# Contamination extraction — decoupled arm\n")
    lines.append("The pilot's decoupled thought completions contain the committed action, so the "
                 "post-hoc thought-stage probes were read off a thought that already reveals the "
                 "decision. This re-runs `ptrue` and `posthoc_numeric` on a TRIMMED thought (trailing "
                 "admissible-command line(s) dropped) with the pilot's exact prompt/seed/sampling, and "
                 "pairs against the recorded full-thought U.\n")
    lines.append("- Decoupled steps re-run: **%d**" % n_steps)
    lines.append("- Steps where a trailing command line was trimmed (`trimmed_bool=True`): **%d** (%.1f%%)"
                 % (n_trimmed_steps, 100.0 * n_trimmed_steps / max(1, n_steps)))
    lines.append("")
    lines.append("`U` is uncertainty (higher = less confident). If conditioning on the committed "
                 "action inflated confidence, the full-thought U is *lower* than the trimmed U, so "
                 "signed `mean(U_full - U_trim)` is **negative** and `mean|ΔU|` is its magnitude.\n")

    lines.append("## All paired steps\n")
    lines.append("| probe | N paired | mean \\|ΔU\\| | mean signed (full−trim) | corr | mean U_full | mean U_trim |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for kind in PROBE_KINDS:
        a = per_probe[kind]["all"]
        lines.append("| %s | %d | %s | %s | %s | %s | %s |" % (
            kind, a["n"], fmt(a["mean_abs"]), fmt(a["mean_signed"]), fmt(a["corr"], 3),
            fmt(a["mean_full"]), fmt(a["mean_trim"])))
    lines.append("")

    lines.append("## Split by trimmed_bool (was a command line actually removed?)\n")
    lines.append("| probe | subset | N | mean \\|ΔU\\| | mean signed | corr |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for kind in PROBE_KINDS:
        for label, key in (("trimmed=True", "trimmed_true"), ("trimmed=False", "trimmed_false")):
            s = per_probe[kind][key]
            lines.append("| %s | %s | %d | %s | %s | %s |" % (
                kind, label, s["n"], fmt(s["mean_abs"]), fmt(s["mean_signed"]), fmt(s["corr"], 3)))
    lines.append("")

    lines.append("## Parse-ok bookkeeping\n")
    lines.append("| probe | N full parse_ok | N trim parse_ok | N both (used) |")
    lines.append("|---|---:|---:|---:|")
    for kind in PROBE_KINDS:
        p = per_probe[kind]
        lines.append("| %s | %d | %d | %d |" % (kind, p["n_full_ok"], p["n_trim_ok"], p["n_both"]))
    lines.append("")

    lines.append("## Did the contamination matter?\n")
    for kind in PROBE_KINDS:
        a = per_probe[kind]["all"]
        t = per_probe[kind]["trimmed_true"]
        f = per_probe[kind]["trimmed_false"]
        bigger = ("larger" if (t["mean_abs"] or 0) > (f["mean_abs"] or 0) else "not larger")
        lines.append("- **%s**: mean|ΔU| = %s across all paired steps; on trimmed=True steps it is %s "
                     "(%s than on trimmed=False, %s). Signed shift on trimmed=True = %s (negative ⇒ full "
                     "thought read as more confident)." % (
                         kind, fmt(a["mean_abs"]), fmt(t["mean_abs"]), bigger, fmt(f["mean_abs"]),
                         fmt(t["mean_signed"])))
    lines.append("")

    with open(report_out, "w") as f:
        f.write("\n".join(lines) + "\n")

    print("\n" + "\n".join(lines))
    print("\nwrote:\n  %s\n  %s\n  %s" % (trimmed_out, pairs_out, report_out))


if __name__ == "__main__":
    main()
