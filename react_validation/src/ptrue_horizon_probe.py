"""P(True) HINDSIGHT-HORIZON sweep — how does a step's uncertainty move as future steps accumulate?

Generalizes the C5/C6 pre-hindsight cells of ptrue_context_rule_probe.py into a curve. For one
frozen step t, re-ask P(True) about THAT step with k = 0, 1, 2, ... K subsequent steps of the
trajectory appended as context:

    k=0   the production prompt (nothing after the action)          <- U_0, the online signal
    k=1   + the observation the action produced                     <- the old C5
    k=2   + the next action and its observation
    ...
    k=K   + K steps of what actually followed

The question is not "does hindsight help" (it does — see PTRUE_CTXRULE_REPORT) but whether the
SHAPE of the curve carries information the instantaneous reading does not:

  * delta_k = U_k - U_0. Does it flow UP for steps that were genuinely off-track, and DOWN (or
    flat) for steps that looked doubtful but were on-path?
  * The 2x2 that motivates this: step-level judge label x TRAJECTORY outcome.
      - uncertain now / episode SUCCEEDED  -> a step that looked bad but was on-path; the curve
        should come back down as the trajectory vindicates it
      - certain now / episode FAILED       -> a confidently-wrong step; the curve should rise
    If those two cases separate by delta but not by U_0, then delta is a cue U_0 cannot give.
  * Online feasibility: U_0 is causal (available at decision time). U_k for k>=1 is NOT — it
    needs the future. It is available online only where actions are reversible (act, observe,
    assess, undo, up to k steps of lookahead), or offline as an analysis instrument. Everything
    here measures whether the cue would be worth that cost; it does not assume it is free.

Nothing is re-run: step t+k's logged history IS step t's history plus the intervening actions and
observations, so the whole curve is a set of slices of the frozen trajectory.

Usage
  python ptrue_horizon_probe.py select --uq ... --judge ... --out sel_h.json --horizon 6
  python ptrue_horizon_probe.py run    --selection sel_h.json --out horizon.jsonl --model qwen ...
  python ptrue_horizon_probe.py report --records horizon.jsonl --out horizon.md --csv horizon.csv
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ptrue_context_rule_probe as P          # prompt blocks, judge labels, AUROC, bootstrap

SCHEMA_VERSION = "horizon_1.0.0"
DEFAULT_HORIZON = 6


# --------------------------------------------------------------------------- prompt

def future_slice(hist_t: str, hist_future: str) -> str | None:
    """The trajectory between step t and a later step, taken verbatim from the logged history.

    hist_{t+k} always begins with hist_t (the harness only ever APPENDS "\\n> action\\nobs"), so the
    suffix is exactly steps t..t+k-1. The leading "> action_t" line is dropped because that action
    is already shown to the probe as PROPOSED ACTION; what remains starts with the observation it
    produced. Returns None if the prefix relation does not hold (never fabricate the slice)."""
    if not hist_future.startswith(hist_t):
        return None
    suf = hist_future[len(hist_t):].lstrip("\n")
    lines = suf.split("\n")
    if lines and lines[0].lstrip().startswith(">"):
        lines = lines[1:]                       # drop the echo of the proposed action
    return "\n".join(lines).strip()


# How each future action is annotated with ITS OWN uncertainty, so the probe can tell whether a
# later step is itself trustworthy before reading it as evidence about step t.
#   none   plain trajectory (the k-curve arm)
#   agent  the agent's own in-generation confidence, c-hat = 1 - U_verbalized. Causally available
#          online: the agent emitted it at the time.
#   ptrue  the post-hoc whole-response P(True) for that step (U_R_ptrue), from the frozen probe
#          corpus. An INDEPENDENT estimate, but note it is the same probe family being asked
#          about the target step — the annotated arm is partly reading its own earlier answers.
ANNOTATIONS = ("none", "agent", "ptrue")
_ANN_LABEL = {"agent": "the agent's own stated confidence in this action",
              "ptrue": "an independent confidence estimate for this action"}


def _future_block(ctx, k, annotate):
    """Rebuild the future block from the logged step records (action / observation / UQ), rather
    than slicing the history text, so the plain and annotated arms differ ONLY by the bracketed
    confidence — a length-matched comparison."""
    fs = ctx.get("future_steps") or []
    if not fs:
        return (ctx.get("future_slices") or {}).get(str(k), "")     # pre-annotation selections
    lines = []
    for j in range(min(k, len(fs))):
        e = fs[j]
        if j == 0:
            lines.append(e.get("obs", ""))                          # outcome of the proposed action
            continue
        u = e.get("u_verb") if annotate == "agent" else e.get("u_ptrue")
        ann = ""
        if annotate != "none" and u is not None:
            ann = "   [%s: %.2f]" % (_ANN_LABEL[annotate], 1.0 - float(u))
        lines.append("> %s%s" % (e.get("action", ""), ann))
        lines.append(e.get("obs", ""))
    return "\n".join(x for x in lines if x is not None).strip()


def build_prompt(ctx, k, *, with_commands=True, annotate="none"):
    """k=0 is byte-identical to the production P(True) prompt; k>=1 appends the future block.
    The Yes/No question is unchanged at every k and every annotation arm, and the future block is
    labeled distinctly from PROPOSED ACTION, so 'the proposed action above' always refers to
    step t."""
    parts = [P._PREAMBLE, "TASK DESCRIPTION:\n%s\n" % ctx["task"],
             "ENVIRONMENT HISTORY:\n%s\n" % ctx["history"]]
    if with_commands:
        parts.append("AVAILABLE COMMANDS:\n%s\n" % ctx["commands"])
    parts.append("AGENT REASONING:\n%s\n" % ctx["thought"])
    parts.append("PROPOSED ACTION:\n%s\n" % ctx["action"])
    if k >= 1:
        blk = _future_block(ctx, k, annotate)
        head = "WHAT HAPPENED NEXT (the following %d step%s of the trajectory" % (
            k, "" if k == 1 else "s")
        if annotate != "none":
            head += "; each later action is tagged with %s" % _ANN_LABEL[annotate]
        parts.append("%s):\n%s\n" % (head, blk))
    parts.append("\n")
    parts.append(P._Q_ACTION)
    return "".join(parts)


# --------------------------------------------------------------------------- selection

def cmd_select(a):
    import run_probes

    judge, episode, steprec = {}, {}, {}
    for line in open(a.judge):
        if line.strip():
            r = json.loads(line)
            if r.get("kind") == "judge":
                judge[(r.get("run_id"), r.get("task_id"), r.get("step_idx"))] = r
    records = [json.loads(l) for l in open(a.uq) if l.strip()]
    for r in records:
        if r.get("kind") == "episode":
            episode[(r.get("run_id"), r.get("task_id"))] = r
        elif r.get("kind") == "step":
            steprec[(r.get("task_id"), r.get("step_idx"))] = r

    # Post-hoc whole-response P(True) per step, from the frozen probe corpus — the second
    # annotation source. Optional: without it the `ptrue` arm simply has no annotations.
    ptrue_u = {}
    if a.ptrue_probes and os.path.exists(a.ptrue_probes):
        for line in open(a.ptrue_probes):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("probe_kind") == "ptrue" and r.get("parse_ok") and r.get("U") is not None:
                ptrue_u[(r.get("task_id"), r.get("step_idx"))] = float(r["U"])
    print("annotation sources: %d step records, %d post-hoc P(True) values"
          % (len(steprec), len(ptrue_u)))

    grouped = list(run_probes.group_steps(records))
    by_key = {(s["run_id"], s["task_id"], s["step_idx"]): s for s in grouped}

    pool = []
    for s in grouped:
        key = (s["run_id"], s["task_id"], s["step_idx"])
        jr, ep = judge.get(key), episode.get((key[0], key[1]))
        if jr is None or ep is None:
            continue
        label, n_inc, n_valid = P._judge_label(jr)
        if label is None:
            continue
        ctx = dict(s["ctx"])
        if not ctx.get("action") or not ctx.get("thought") or not ctx.get("history"):
            continue

        # every horizon 1..K must exist, so the curve is complete and fully paired across k
        slices, ok = {}, True
        for k in range(1, a.horizon + 1):
            nxt = by_key.get((key[0], key[1], (key[2] or 0) + k))
            if nxt is None:
                ok = False
                break
            sl = future_slice(ctx["history"], nxt["ctx"]["history"])
            if sl is None:
                ok = False
                break
            slices[str(k)] = sl
        if not ok:
            continue
        ctx["future_slices"] = slices

        # Per-future-step records for the annotated arms. Entry j=0 is the OUTCOME of the step
        # under evaluation (no annotation — annotating the target with another probe's verdict
        # about it would leak the answer); j>=1 are the later actions, each with its own UQ.
        fsteps, ok = [], True
        for j in range(a.horizon):
            sr = steprec.get((key[1], (key[2] or 0) + j))
            if sr is None:
                ok = False
                break
            e = {"obs": sr.get("obs") or ""}
            if j >= 1:
                e["action"] = sr.get("action_parsed") or ""
                e["u_verb"] = sr.get("U_verbalized")
                e["u_ptrue"] = ptrue_u.get((key[1], (key[2] or 0) + j))
            fsteps.append(e)
        if not ok:
            continue
        ctx["future_steps"] = fsteps

        pool.append({
            "run_id": key[0], "task_id": key[1], "step_idx": key[2],
            "label": label, "n_incorrect_votes": n_inc, "n_valid_votes": n_valid,
            "episode_success": bool(ep.get("success")),
            "episode_terminal_reason": ep.get("terminal_reason"),
            "episode_n_steps": ep.get("n_steps"),
            "loop_collapse_fraction": ep.get("loop_collapse_fraction"),
            "steps_remaining": (ep.get("n_steps") or 0) - (key[2] or 0),
            "judge_reasons": {m: (v.get("reason") or "")[:200]
                              for m, v in (jr.get("votes") or {}).items()},
            "ctx": ctx,
        })

    # 2x2: step judge label x TRAJECTORY outcome. The off-diagonal cells are the interesting
    # ones (bad-looking step in a successful run; clean-looking step in a failed run), so they
    # get the same quota as the diagonal even though they are rarer.
    cells = {(l, e): [p for p in pool if p["label"] == l and p["episode_success"] == e]
             for l in (0, 1) for e in (True, False)}
    rng = random.Random(a.seed)
    per_task, picked = {}, []
    for keyc in [(1, False), (1, True), (0, False), (0, True)]:
        cands = cells[keyc][:]
        rng.shuffle(cands)
        taken = 0
        for c in cands:
            if taken >= a.per_cell:
                break
            if per_task.get(c["task_id"], 0) >= a.max_per_task:
                continue
            per_task[c["task_id"]] = per_task.get(c["task_id"], 0) + 1
            picked.append(c)
            taken += 1

    sel = {"schema": SCHEMA_VERSION, "horizon": a.horizon, "uq": a.uq, "judge": a.judge,
           "seed": a.seed, "steps": picked}
    json.dump(sel, open(a.out, "w"), indent=1)

    print("pool with a full %d-step future: %d" % (a.horizon, len(pool)))
    for keyc, v in sorted(cells.items()):
        got = sum(1 for p in picked if (p["label"], p["episode_success"]) == keyc)
        print("  step=%-9s episode=%-7s available %4d   picked %3d"
              % ("INCORRECT" if keyc[0] else "correct", "SUCCESS" if keyc[1] else "FAIL",
                 len(v), got))
    print("selected %d steps x %d horizons = %d calls -> %s"
          % (len(picked), a.horizon + 1, len(picked) * (a.horizon + 1), a.out))
    return 0


# --------------------------------------------------------------------------- sweep

def cmd_run(a):
    import probes
    from openai import OpenAI

    sel = json.load(open(a.selection))
    K = sel["horizon"]
    steps = sel["steps"][:a.max_steps] if a.max_steps else sel["steps"]
    cfg = probes.ProbeConfig(model=a.model, tokenizer_path=a.tokenizer, base_url=a.base_url,
                             temperature=0.0, top_p=1.0, top_k=20, min_p=0.0,
                             presence_penalty=0.0, repetition_penalty=1.0, seed_base=a.seed_base)
    client = OpenAI(api_key="EMPTY", base_url=a.base_url)

    arms = [x.strip() for x in a.annotate.split(",") if x.strip()]
    for arm in arms:
        if arm not in ANNOTATIONS:
            sys.exit("unknown --annotate arm %r (choose from %s)" % (arm, ",".join(ANNOTATIONS)))

    def one(s, k, arm):
        prompt = build_prompt(s["ctx"], k, annotate=arm)
        seed = (a.seed_base + (hash(s["task_id"]) % 100000) * 100 + int(s["step_idx"]) * 10 + k
                + 1000000 * ANNOTATIONS.index(arm))
        try:
            _c, rec = probes._call(client, cfg, prompt, max_tokens=4, seed=seed)
        except Exception as e:
            sys.stderr.write("ERROR %s/%s k=%d: %r\n" % (s["task_id"], s["step_idx"], k, e))
            return None
        top = probes._first_nonws_top(rec["gen_logprobs"])
        p_yes, p_no, conf, U, ok = probes.yesno_mass(top)
        return {
            "kind": "probe", "horizon_schema_version": SCHEMA_VERSION, "probe_kind": "ptrue",
            "k": k, "annotate": arm,
            "run_id": s["run_id"], "task_id": s["task_id"], "step_idx": s["step_idx"],
            "label": s["label"], "episode_success": s["episode_success"],
            "episode_terminal_reason": s.get("episode_terminal_reason"),
            "episode_n_steps": s.get("episode_n_steps"),
            "loop_collapse_fraction": s.get("loop_collapse_fraction"),
            "steps_remaining": s.get("steps_remaining"),
            "step_meta": {"task": s["ctx"]["task"], "thought": s["ctx"]["thought"],
                          "action": s["ctx"]["action"], "judge_reasons": s.get("judge_reasons")},
            "probe_seed": seed, "probe_prompt": prompt,
            "parsed_value": conf, "U": U, "parse_ok": ok, "p_yes": p_yes, "p_no": p_no,
            "record": rec,
        }

    n_ok = n_tot = 0
    with open(a.out, "a") as fo:
        for si, s in enumerate(steps):
            jobs = [(k, arm) for arm in arms for k in range(K + 1)]
            with cf.ThreadPoolExecutor(max_workers=a.concurrency) as ex:
                out = list(ex.map(lambda j: one(s, j[0], j[1]), jobs))
            for r in out:
                if r is None:
                    continue
                n_tot += 1
                n_ok += 1 if r["parse_ok"] else 0
                fo.write(json.dumps(r) + "\n")
            fo.flush()
            print("[%d/%d] %s step %s: %d cells (parse_ok %d/%d)"
                  % (si + 1, len(steps), s["task_id"][:38], s["step_idx"], len(jobs), n_ok, n_tot))
            sys.stdout.flush()
    print("\nDONE: %d steps x %d horizons x %d arms -> %s | parse_ok %d/%d"
          % (len(steps), K + 1, len(arms), a.out, n_ok, n_tot))
    return 0


# --------------------------------------------------------------------------- report

GROUPS = [(1, False, "INCORRECT step / episode FAILED"),
          (1, True, "INCORRECT step / episode SUCCEEDED"),
          (0, False, "correct step / episode FAILED"),
          (0, True, "correct step / episode SUCCEEDED")]


def _fmt(x, nd=3):
    return "n/a" if x is None else "%.*f" % (nd, x)


def load(path, arm_filter=None):
    U, meta, ks = {}, {}, set()
    for line in open(path):
        if not line.strip():
            continue
        r = json.loads(line)
        key = (r["task_id"], r["step_idx"])
        if arm_filter is not None and r.get("annotate", "none") != arm_filter:
            continue
        meta[key] = {"label": r["label"], "success": r["episode_success"],
                     "terminal": r.get("episode_terminal_reason"),
                     "remaining": r.get("steps_remaining"),
                     "step_meta": r.get("step_meta") or {}}
        ks.add(r["k"])
        if r.get("parse_ok") and r.get("U") is not None:
            U[(key, r["k"])] = float(r["U"])
    return U, meta, sorted(ks)


def cmd_report(a):
    U, meta, ks = load(a.records, arm_filter=a.arm)
    keys = sorted(meta)
    K = max(ks)

    def grp(k_label, succ):
        return [x for x in keys if meta[x]["label"] == k_label and meta[x]["success"] == succ]

    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["task_id", "step_idx", "step_label", "episode_success", "terminal_reason"]
                       + ["U_k%d" % k for k in ks] + ["delta_K", "slope"])
            for x in keys:
                us = [U.get((x, k)) for k in ks]
                d = (us[-1] - us[0]) if (us[-1] is not None and us[0] is not None) else None
                w.writerow([x[0], x[1], meta[x]["label"], meta[x]["success"], meta[x]["terminal"]]
                           + [_fmt(u, 4) for u in us] + [_fmt(d, 4), _fmt(_slope(us, ks), 4)])

    L = ["# P(True) hindsight-horizon sweep — does the SHAPE of U(k) carry extra information?", ""]
    L.append("%d steps x %d horizons (k=0..%d). k=0 is the production prompt (causal, available "
             "online); k>=1 appends what actually followed and is available only where actions "
             "are reversible." % (len(keys), len(ks), K))
    L.append("")
    L.append("## Mean U by horizon, split by step label x trajectory outcome")
    L.append("")
    L.append("| group | n | " + " | ".join("k=%d" % k for k in ks) + " | ΔK = U_K − U_0 |")
    L.append("|" + "---|" * (len(ks) + 3))
    for lab, succ, name in GROUPS:
        g = grp(lab, succ)
        if not g:
            continue
        row = []
        for k in ks:
            vals = [U[(x, k)] for x in g if (x, k) in U]
            row.append(_fmt(statistics.fmean(vals) if vals else None))
        ds = [U[(x, K)] - U[(x, 0)] for x in g if (x, K) in U and (x, 0) in U]
        L.append("| %s | %d | %s | **%s** |" % (name, len(g), " | ".join(row),
                                                _fmt(statistics.fmean(ds) if ds else None)))
    L.append("")

    # ---- does hindsight sharpen STEP-level discrimination, and where does it saturate?
    L.append("## Step-level discrimination at each horizon")
    L.append("")
    L.append("AUROC for the judge's step label, using U_k alone. If this rises with k and then "
             "flattens, that flattening point is how much lookahead is worth buying.")
    L.append("")
    L.append("| k | AUROC (step incorrect) [95% CI] | n |")
    L.append("|---|---|---|")
    for k in ks:
        pairs, by_task = [], {}
        for x in keys:
            if (x, k) in U:
                pairs.append((U[(x, k)], meta[x]["label"]))
                by_task.setdefault(x[0], []).append((U[(x, k)], meta[x]["label"]))
        au = P._auroc(pairs)
        lo, hi = P._auroc_ci(by_task)
        L.append("| %d | %s | %d |" % (k, "n/a" if au is None else
                                       ("%.3f [%.3f, %.3f]" % (au, lo, hi) if lo is not None
                                        else "%.3f" % au), len(pairs)))
    L.append("")

    # ---- THE question: does the SHAPE beat the instantaneous value for TRAJECTORY outcome?
    L.append("## Trajectory outcome: does Δ beat U_0?")
    L.append("")
    L.append("AUROC for *episode FAILED*, positive class = failed, computed over steps "
             "(clustered by episode). `U_0` is what an online probe sees; `ΔK` and `slope` are "
             "what the hindsight curve adds.")
    L.append("")
    L.append("| predictor | AUROC (episode failed) [95% CI] |")
    L.append("|---|---|")
    feats = {
        "U_0 (online, instantaneous)": lambda x: U.get((x, 0)),
        "U_K (full hindsight)": lambda x: U.get((x, K)),
        "ΔK = U_K − U_0": lambda x: (None if (x, K) not in U or (x, 0) not in U
                                     else U[(x, K)] - U[(x, 0)]),
        "slope of U over k": lambda x: _slope([U.get((x, k)) for k in ks], ks),
    }
    for name, fn in feats.items():
        pairs, by_task = [], {}
        for x in keys:
            v = fn(x)
            if v is None:
                continue
            y = 0 if meta[x]["success"] else 1
            pairs.append((v, y))
            by_task.setdefault(x[0], []).append((v, y))
        au = P._auroc(pairs)
        lo, hi = P._auroc_ci(by_task)
        L.append("| %s | %s |" % (name, "n/a" if au is None else
                                  ("%.3f [%.3f, %.3f]" % (au, lo, hi) if lo is not None
                                   else "%.3f" % au)))
    L.append("")

    # ---- the motivating 2x2, conditioned on how the step LOOKED at the time
    L.append("## Conditioned on how the step looked at the time")
    L.append("")
    L.append("Split the steps at the median U_0 — 'looked fine' vs 'looked doubtful' to an online "
             "probe — and ask whether Δ separates trajectory outcome WITHIN each half. That is "
             "the case for Δ as a cue: it would have to add something where U_0 alone is "
             "ambiguous.")
    L.append("")
    u0 = sorted(U[(x, 0)] for x in keys if (x, 0) in U)
    med = statistics.median(u0) if u0 else 0.5
    L.append("| U_0 half | n | mean ΔK, episode SUCCEEDED | mean ΔK, episode FAILED | AUROC of ΔK for failure |")
    L.append("|---|---|---|---|---|")
    for name, pred in [("looked fine (U_0 <= %.2f)" % med, lambda v: v <= med),
                       ("looked doubtful (U_0 > %.2f)" % med, lambda v: v > med)]:
        sub = [x for x in keys if (x, 0) in U and pred(U[(x, 0)])]
        ds = {True: [], False: []}
        pairs, by_task = [], {}
        for x in sub:
            if (x, K) not in U:
                continue
            d = U[(x, K)] - U[(x, 0)]
            ds[meta[x]["success"]].append(d)
            y = 0 if meta[x]["success"] else 1
            pairs.append((d, y))
            by_task.setdefault(x[0], []).append((d, y))
        au = P._auroc(pairs)
        lo, hi = P._auroc_ci(by_task)
        L.append("| %s | %d | %s | %s | %s |"
                 % (name, len(sub),
                    _fmt(statistics.fmean(ds[True]) if ds[True] else None),
                    _fmt(statistics.fmean(ds[False]) if ds[False] else None),
                    "n/a" if au is None else ("%.3f [%.3f, %.3f]" % (au, lo, hi) if lo is not None
                                              else "%.3f" % au)))
    L.append("")
    L.append("_Caveat that applies to every number above: U_k for k>=1 is not causally available "
             "at step t. These measure whether the cue is worth paying for (reversible-action "
             "lookahead, or offline analysis), not a deployable online detector._")

    out = "\n".join(L) + "\n"
    if a.out:
        open(a.out, "w").write(out)
        print("wrote %s%s" % (a.out, " and %s" % a.csv if a.csv else ""))
    else:
        print(out)
    return 0


def _slope(us, ks):
    """OLS slope of U on k over the non-missing points (the curve's overall drift)."""
    pts = [(k, u) for k, u in zip(ks, us) if u is not None]
    if len(pts) < 2:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return None if den == 0 else sum((x - mx) * (y - my) for x, y in pts) / den


# --------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("select")
    s.add_argument("--uq", required=True)
    s.add_argument("--judge", required=True)
    s.add_argument("--out", default="sel_horizon.json")
    s.add_argument("--horizon", type=int, default=DEFAULT_HORIZON)
    s.add_argument("--per-cell", type=int, default=30, help="steps per 2x2 cell")
    s.add_argument("--max-per-task", type=int, default=2)
    s.add_argument("--seed", type=int, default=20260731)
    s.add_argument("--ptrue-probes", default="result/e1/e1b/probes_entangled_e1.aggtrue_ptrue.jsonl",
                   help="frozen whole-response P(True) corpus used to annotate future steps")
    s.set_defaults(fn=cmd_select)

    env = os.environ
    r = sub.add_parser("run")
    r.add_argument("--selection", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--model", default=env.get("PROBE_MODEL", "qwen"))
    r.add_argument("--tokenizer", default=env.get("PROBE_TOKENIZER", "Qwen/Qwen3.6-35B-A3B"))
    r.add_argument("--base-url", default=env.get("PROBE_BASE_URL", "http://localhost:8000/v1"))
    r.add_argument("--seed-base", type=int, default=11000)
    r.add_argument("--max-steps", type=int, default=None)
    r.add_argument("--concurrency", type=int, default=7)
    r.add_argument("--annotate", default="none",
                   help="comma-separated arms from %s; annotated arms tag each FUTURE action "
                        "with its own uncertainty so the probe can weigh it" % (",".join(ANNOTATIONS),))
    r.set_defaults(fn=cmd_run)

    p = sub.add_parser("report")
    p.add_argument("--records", required=True)
    p.add_argument("--csv", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--arm", default=None, help="restrict to one --annotate arm")
    p.set_defaults(fn=cmd_report)

    d = sub.add_parser("dump")
    d.add_argument("--selection", required=True)
    d.add_argument("--step", type=int, default=0)
    d.add_argument("--head", type=int, default=0)
    d.add_argument("--annotate", default="none")
    d.set_defaults(fn=cmd_dump)

    a = ap.parse_args()
    sys.exit(a.fn(a))


def cmd_dump(a):
    sel = json.load(open(a.selection))
    s = sel["steps"][a.step]
    print("### %s step %s | label=%d | episode_success=%s | remaining=%s\n"
          % (s["task_id"], s["step_idx"], s["label"], s["episode_success"],
             s.get("steps_remaining")))
    for k in range(sel["horizon"] + 1):
        p = build_prompt(s["ctx"], k, annotate=a.annotate)
        print("=" * 78)
        print("### k=%d   [%d chars]" % (k, len(p)))
        print("=" * 78)
        tail = p.split("PROPOSED ACTION:", 1)[1]
        print("PROPOSED ACTION:" + (tail if not a.head else
                                    "\n".join(tail.splitlines()[:a.head])))
        print()
    return 0


if __name__ == "__main__":
    main()
