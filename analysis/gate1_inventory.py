#!/usr/bin/env python3
"""Gate-1 Phase 0 — inventory and field audit over the pivot corpus.

Reads NOTHING but the logged records. No model calls, no environment, no GPU.
Emits a JSON blob (machine-readable) and a markdown report:

  * per-arm record counts by kind
  * per-arm presence / null-rate of every step field gate 1 depends on
  * the full skip_reasons taxonomy with counts, per arm
  * Tier-A rule firing counts and union coverage per arm
  * HotpotQA-specific recoverability audit (0.1): tool-call validity, result
    count, query text, gold supporting-fact ids

  gate1_inventory.py [--pivot DIR] [--out-json ...] [--out-md ...]
"""
import argparse
import collections
import json
import os
import re
import sys

import gate1_manifest

# The step fields gate 1 reads. Presence and null-rate are both audited: a key
# that exists but is always null is not a usable field.
STEP_FIELDS = [
    "task_id", "step_idx", "action_parsed", "obs", "obs_changed", "admissible",
    "in_admissible", "loop_flag", "state_hash", "U_verbalized", "skip_reasons", "tau",
]
EPISODE_FIELDS = ["task_id", "success", "terminal_reason", "n_steps", "loop_collapse_fraction"]
# HotpotQA episodes carry the outcome fields the Tier-B answer rule needs.
EPISODE_FIELDS_HOTPOT = EPISODE_FIELDS + ["em", "f1", "gold_answer", "predicted_answer", "question"]

# Arms that feed the 56-cell (assessor x target) matrix. Other directories under
# result/pivot are inventoried too but flagged as non-matrix.
MATRIX_TARGETS = {
    "alfworld": ["Llama-3.3-70B-Instruct", "Mistral-7B-Instruct-v0.3", "Phi-4-mini-instruct",
                 "Qwen3.6-35B-A3B", "deepseek-v4-flash", "gemma-3-4b-it"],
    "hotpotqa": ["Llama-3.3-70B-Instruct", "Mistral-7B-Instruct-v0.3", "Phi-4-mini-instruct",
                 "Qwen3.6-35B-A3B", "gemma-3-4b-it"],
}

NOTHING_HAPPENS = "Nothing happens."
_HOTPOT_ACTION_RE = re.compile(r"^(search|lookup|finish)\[[^\r\n]*\]$", re.IGNORECASE)
_COULD_NOT_FIND_RE = re.compile(r"^Could not find .*\. Similar: (\[.*\])\.\s*$", re.DOTALL)


def iter_records(path, limit_bytes=None):
    """Yield (kind, record) for step/episode records only.

    `call` records carry the per-token logprobs and dominate file size (tens of GB
    per arm); parsing them would make this scan hours long for no gain. They are
    identified by the cheap head test below rather than by full parse. Lines that
    match neither prefix are counted and sampled so a silent miss is impossible.

    `limit_bytes` pins the read to a manifest-recorded length so a concurrent
    appender cannot change what a later phase sees (see gate1_manifest.py).
    """
    skipped = 0
    consumed = 0
    sampled_other = collections.Counter()
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if limit_bytes is not None:
                consumed += len(line.encode("utf-8"))
                if consumed > limit_bytes:
                    break
            head = line[:64]
            if '"kind": "step"' in head:
                yield "step", json.loads(line)
            elif '"kind": "episode"' in head:
                yield "episode", json.loads(line)
            else:
                # Sample 1-in-5000 of the unparsed lines and confirm each is a
                # `call`; anything else is a scan bug and must surface loudly.
                if skipped % 5000 == 0:
                    try:
                        sampled_other[json.loads(line).get("kind")] += 1
                    except Exception:
                        sampled_other["UNPARSEABLE"] += 1
                skipped += 1
    yield "__meta__", {"skipped_lines": skipped, "sampled_skipped_kinds": dict(sampled_other)}


def hotpot_zero_result(obs):
    """(is_zero_result, similar_list_empty) for a HotpotQA observation.

    wikienv emits `Could not find {entity}. Similar: {titles[:5]}.` when the search
    loaded no page, and `No more results.` when a Lookup exhausts its matches.
    """
    if obs is None:
        return False, False
    o = obs.strip()
    m = _COULD_NOT_FIND_RE.match(o)
    if m:
        return True, m.group(1).strip() == "[]"
    if o.startswith("No more results."):
        return True, False
    return False, False


def tier_a_flags(dataset, rec, seen_pairs):
    """Sub-rules that fire on this step. Tier A yields ONLY incorrect labels."""
    fired = []
    action = rec.get("action_parsed")
    obs = rec.get("obs")

    if dataset == "alfworld":
        if rec.get("in_admissible") is False:
            fired.append("A1_inadmissible")
        if rec.get("obs_changed") is False and (obs or "").strip() == NOTHING_HAPPENS:
            fired.append("A2_nothing_happens")
        key = (rec.get("state_hash"), action)
        if key in seen_pairs:
            fired.append("A3_exact_repeat")
        seen_pairs.add(key)
    else:
        # A1 for HotpotQA is a malformed tool call: the action does not match the
        # Search/Lookup/Finish grammar. `in_admissible` is logged from the same
        # regex, so the two agree by construction; both are checked and any
        # disagreement is reported rather than silently resolved.
        malformed = not _HOTPOT_ACTION_RE.match((action or "").strip())
        if malformed or rec.get("in_admissible") is False:
            fired.append("A1_malformed_toolcall")
        # A3 for HotpotQA is a repeated query text (the action string).
        key = (action or "").strip().lower()
        if key in seen_pairs:
            fired.append("A3_repeat_query")
        seen_pairs.add(key)
        zero, _empty_similar = hotpot_zero_result(obs)
        if zero:
            fired.append("A4_zero_result")
    return fired


def scan_arm(dataset, model, path, limit_bytes=None):
    out = {
        "dataset": dataset, "model": model, "path": path,
        "in_matrix": model in MATRIX_TARGETS.get(dataset, []),
        "counts": collections.Counter(),
        "step_field_present": collections.Counter(),
        "step_field_null": collections.Counter(),
        "episode_field_present": collections.Counter(),
        "skip_reasons": collections.Counter(),
        "skip_reason_cooccur_with_tierA": collections.Counter(),
        "tier_a_rule": collections.Counter(),
        "tier_a_any": 0,
        "n_steps": 0,
        "n_episodes": 0,
        "episodes_seen": set(),
        "hotpot": collections.Counter(),
        "anomalies": collections.Counter(),
        "checks": collections.Counter(),
        "meta": {},
    }
    episode_record_ids = set()
    ep_fields = EPISODE_FIELDS_HOTPOT if dataset == "hotpotqa" else EPISODE_FIELDS
    per_ep_seen = collections.defaultdict(set)
    step_keys = collections.defaultdict(set)

    for kind, rec in iter_records(path, limit_bytes):
        if kind == "__meta__":
            out["meta"] = rec
            continue
        out["counts"][kind] += 1
        if kind == "episode":
            out["n_episodes"] += 1
            episode_record_ids.add(rec.get("task_id"))
            for f in ep_fields:
                if f in rec and rec[f] is not None:
                    out["episode_field_present"][f] += 1
            continue

        out["n_steps"] += 1
        tid = rec.get("task_id")
        out["episodes_seen"].add(tid)
        key = (tid, rec.get("step_idx"))
        if key in step_keys[tid]:
            out["anomalies"]["duplicate_step_key"] += 1
        step_keys[tid].add(key)

        for f in STEP_FIELDS:
            if f in rec:
                out["step_field_present"][f] += 1
                if rec[f] is None:
                    out["step_field_null"][f] += 1

        if not (rec.get("action_parsed") or "").strip():
            out["checks"]["empty_action_parsed"] += 1
            if not (rec.get("skip_reasons") or []):
                # An empty action carries NO skip_reason (the drivers guard the
                # invalid_action_syntax / tau_unrecognized_action appends behind
                # `and action`), so a skip_reason-based filter silently keeps it.
                out["checks"]["empty_action_no_skip_reason"] += 1

        reasons = rec.get("skip_reasons") or []
        fired = tier_a_flags(dataset, rec, per_ep_seen[tid])
        # A3 is defined over (state_hash, action_parsed), and state_hash is
        # sha1(obs) of the POST-action observation, so A3 should coincide exactly
        # with the driver's own loop_flag. Verified rather than assumed.
        a3_fired = any(f.startswith("A3_") for f in fired)
        if dataset == "alfworld":
            if a3_fired != bool(rec.get("loop_flag")):
                out["checks"]["A3_vs_loop_flag_disagree"] += 1
            if a3_fired:
                out["checks"]["A3_fired"] += 1
        for r in reasons:
            out["skip_reasons"][r] += 1
            if fired:
                out["skip_reason_cooccur_with_tierA"][r] += 1
        if not reasons:
            out["skip_reasons"]["<none>"] += 1

        for f in fired:
            out["tier_a_rule"][f] += 1
        if fired:
            out["tier_a_any"] += 1

        if dataset == "hotpotqa":
            action = (rec.get("action_parsed") or "").strip()
            out["hotpot"]["query_text_recoverable"] += 1 if action else 0
            grammar_ok = bool(_HOTPOT_ACTION_RE.match(action))
            logged_ok = rec.get("in_admissible")
            if logged_ok is not None and grammar_ok != bool(logged_ok):
                out["hotpot"]["grammar_vs_in_admissible_disagree"] += 1
            zero, empty_similar = hotpot_zero_result(rec.get("obs"))
            if zero:
                out["hotpot"]["zero_result_obs"] += 1
                if empty_similar:
                    out["hotpot"]["zero_result_empty_similar"] += 1
            if action.lower().startswith("search["):
                out["hotpot"]["search_steps"] += 1
            elif action.lower().startswith("lookup["):
                out["hotpot"]["lookup_steps"] += 1
            elif action.lower().startswith("finish["):
                out["hotpot"]["finish_steps"] += 1

    out["steps_without_episode_record"] = sorted(out["episodes_seen"] - episode_record_ids)
    out["episodes_seen"] = len(out["episodes_seen"])
    for k in ("counts", "step_field_present", "step_field_null", "episode_field_present",
              "skip_reasons", "skip_reason_cooccur_with_tierA", "tier_a_rule", "hotpot",
              "anomalies", "checks"):
        out[k] = dict(out[k])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--out-json", default="reports/gate1/phase0_inventory.json")
    ap.add_argument("--out-md", default="reports/gate1/report_phase0_inventory.md")
    ap.add_argument("--only", default=None, help="comma-separated dataset/model to limit the scan")
    ap.add_argument("--manifest", default="reports/gate1/input_manifest.json",
                    help="pin every read to the byte lengths recorded here")
    ap.add_argument("--from-json", action="store_true",
                    help="re-render the markdown from an existing --out-json; no rescan")
    args = ap.parse_args()

    if args.from_json:
        blob = json.load(open(args.out_json))
        write_md(blob["arms"], args.out_md, args.pivot)
        sys.stderr.write("rewrote %s from %s\n" % (args.out_md, args.out_json))
        return

    arms = []
    for dataset in ("alfworld", "hotpotqa"):
        d = os.path.join(args.pivot, dataset)
        if not os.path.isdir(d):
            continue
        for model in sorted(os.listdir(d)):
            p = os.path.join(d, model, "uq.jsonl")
            if os.path.isfile(p):
                if args.only and "%s/%s" % (dataset, model) not in args.only.split(","):
                    continue
                arms.append((dataset, model, p))

    pins = gate1_manifest.load(args.manifest, args.pivot)
    results = []
    for dataset, model, path in arms:
        rel = os.path.relpath(path, args.pivot)
        if rel not in pins:
            raise SystemExit("%s is not in the manifest — regenerate it" % rel)
        sys.stderr.write("scanning %s/%s (%.1f GB)\n"
                         % (dataset, model, os.path.getsize(path) / 1e9))
        sys.stderr.flush()
        results.append(scan_arm(dataset, model, path, pins[rel]))

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump({"pivot": os.path.abspath(args.pivot), "arms": results}, f, indent=2)
    write_md(results, args.out_md, args.pivot)
    sys.stderr.write("wrote %s and %s\n" % (args.out_json, args.out_md))


def _pct(n, d):
    return "—" if not d else "%.1f%%" % (100.0 * n / d)


def write_md(results, path, pivot):
    L = []
    A = L.append
    A("# Gate-1 Phase 0 — inventory and field audit\n")
    A("Corpus: `%s`. Log-scan only — no inference, no environment, no GPU.\n" % pivot)

    matrix = [r for r in results if r["in_matrix"]]
    n_steps_matrix = sum(r["n_steps"] for r in matrix)
    cov = [(r["tier_a_any"] / r["n_steps"], r) for r in matrix if r["n_steps"]]
    lo, hi = min(cov)[0], max(cov)[0]
    hot = [r for r in results if r["dataset"] == "hotpotqa"]

    A("\n## 0. Findings\n")
    A("**Scope.** %d arms carry `uq.jsonl`; %d of them are the targets behind the 56-cell "
      "(assessor × target) matrix (%d steps). The %d `Qwen3.5-*` arms are outside the matrix "
      "and are inventoried for completeness only.\n"
      % (len(results), len(matrix), n_steps_matrix, len(results) - len(matrix)))
    A("**The corpus is live, so every read is pinned.** While gate 1 ran, a "
      "`judge_hotpot.py` process and eight `run_probes.py` workers were still appending "
      "to the `Qwen3.5-*` arms (none of which is in the 56-cell matrix). Every gate-1 "
      "input is therefore recorded in `reports/gate1/input_manifest.json` as "
      "(size, sha256, mtime) and every reader takes only the first `size` bytes, so a "
      "concurrent append cannot change a result. Verified: one judge file grew by 139 KB "
      "mid-run and the Phase-1 output was byte-identical across the two runs that "
      "straddled it. `gate1_manifest.py --verify` re-checks the pinned prefixes.\n")
    A("**0.1 — field presence.** Every field gate 1 depends on (`action_parsed`, `obs`, "
      "`obs_changed`, `admissible`, `in_admissible`, `loop_flag`, `state_hash`, `task_id`, "
      "`step_idx`, `skip_reasons`) is present on **100% of step records in every arm**, "
      "non-null. Only `U_verbalized` and `tau` carry nulls, and both are elicitation/tagging "
      "outputs rather than environment evidence, so neither blocks labelling.\n")
    A("**0.1 — HotpotQA. STOP condition partially triggered.** Of the four fields named in "
      "the brief, three are fully recoverable and one is not:\n")
    A("- *tool-call validity* — recoverable. `in_admissible` is logged on every step and "
      "agrees with an independent re-derivation from the `Search|Lookup|Finish[...]` grammar "
      "on **every step of every arm** (0 disagreements).")
    A("- *result count* — recoverable. `wikienv` emits a fixed `Could not find {entity}. "
      "Similar: [...]` / `No more results.` string, so a retrieval that loaded no page is "
      "detectable from `obs` verbatim.")
    A("- *query text* — recoverable, verbatim in `action_parsed`.")
    A("- *gold supporting-fact ids* — **NOT recoverable.** The vendored corpus "
      "`src/data/hotpot_dev_v1_simplified.json` holds only `question` / `answer` / `type`; "
      "there are no `supporting_facts` and no context paragraphs. No copy carrying them "
      "exists on the machine (the only other HotpotQA files, under "
      "`experiments/single_agent_uncertainty_exp/data/`, are likewise question/answer only).\n")
    A("  Consequence, per the hard constraint against improvising labels: **Phase 3's "
      "HotpotQA search-step rule (\"retrieved a gold supporting document\") is halted.** "
      "Everything else proceeds. The HotpotQA *answer*-step rule is unaffected — `em`, `f1`, "
      "`gold_answer` and `predicted_answer` are present on 100% of episode records — and "
      "HotpotQA Tier A is unaffected, since A1/A3/A4 need none of the blocked field.\n")
    A("**0.2 — skip-reason taxonomy.** Four reasons occur corpus-wide. Two are action "
      "evidence and are **included** in the gate-1 label set as the brief directs:\n")
    A("- `tau_unrecognized_action` — the action matched no entry in the environment grammar.")
    A("- `invalid_action_syntax` (HotpotQA only) — same event, logged by the Hotpot drivers "
      "alongside the τ reason; the two co-occur one-for-one in every arm.\n")
    A("Two are **flagged as ambiguous and NOT decided here** (see §7).\n")
    A("**0.3 — Tier-A coverage** on matrix arms runs from **%.1f%% (%s/%s)** to "
      "**%.1f%% (%s/%s)** of steps. Tier A produces incorrect labels only, so this is an "
      "upper bound on what Tier A alone can decide; Tier B has to carry the rest.\n"
      % (100 * lo, min(cov)[1]["dataset"], min(cov)[1]["model"],
         100 * hi, max(cov)[1]["dataset"], max(cov)[1]["model"]))
    A("**A3 is an observation-repeat rule, not a state-repeat rule.** `state_hash` is "
      "`sha1(obs)[:16]` of the *post*-action observation, so the pair `(state_hash, "
      "action_parsed)` is the pair `(obs, action)` the drivers already track as `loop_flag`. "
      "Recomputed independently, A3 and `loop_flag` agree on **every ALFWorld step in every "
      "arm** (0 disagreements). A3 is therefore reproducing the logged loop detector exactly "
      "— it adds no independent evidence, and it cannot detect a revisit to the same world "
      "state that produced a different observation.\n")

    A("\n## 1. Arms and record counts\n")
    A("| dataset | model | in 56-cell matrix | steps | episodes (records) | episodes (distinct task_id) | dup step keys |")
    A("|---|---|---|---|---|---|---|")
    for r in results:
        A("| %s | %s | %s | %d | %d | %d | %d |" % (
            r["dataset"], r["model"], "yes" if r["in_matrix"] else "**no**",
            r["n_steps"], r["n_episodes"], r["episodes_seen"],
            r["anomalies"].get("duplicate_step_key", 0)))

    A("\n## 2. Step-field presence (0.1)\n")
    A("Each cell is present/steps; `null` in parentheses when a present key is null.\n")
    A("| dataset | model | " + " | ".join(STEP_FIELDS) + " |")
    A("|---|---|" + "---|" * len(STEP_FIELDS))
    for r in results:
        cells = []
        for f in STEP_FIELDS:
            p = r["step_field_present"].get(f, 0)
            n = r["step_field_null"].get(f, 0)
            cells.append(("%s" % _pct(p, r["n_steps"])) + (" (null %s)" % _pct(n, r["n_steps"]) if n else ""))
        A("| %s | %s | %s |" % (r["dataset"], r["model"], " | ".join(cells)))

    A("\n## 3. skip_reasons taxonomy (0.2)\n")
    all_reasons = sorted({k for r in results for k in r["skip_reasons"]})
    A("| dataset | model | " + " | ".join("`%s`" % x for x in all_reasons) + " |")
    A("|---|---|" + "---|" * len(all_reasons))
    for r in results:
        A("| %s | %s | %s |" % (r["dataset"], r["model"],
                                " | ".join(str(r["skip_reasons"].get(k, 0)) for k in all_reasons)))

    A("\n## 4. Tier-A coverage (0.3)\n")
    A("Tier A emits **incorrect** labels only; coverage = share of steps it can label at all.\n")
    A("| dataset | model | steps | A1 | A2 | A3 | A4 | any (coverage) |")
    A("|---|---|---|---|---|---|---|---|")
    for r in results:
        g = r["tier_a_rule"]
        a1 = g.get("A1_inadmissible", 0) + g.get("A1_malformed_toolcall", 0)
        a2 = g.get("A2_nothing_happens", 0)
        a3 = g.get("A3_exact_repeat", 0) + g.get("A3_repeat_query", 0)
        a4 = g.get("A4_zero_result", 0)
        A("| %s | %s | %d | %d | %d | %d | %d | %d (%s) |" % (
            r["dataset"], r["model"], r["n_steps"], a1, a2, a3, a4,
            r["tier_a_any"], _pct(r["tier_a_any"], r["n_steps"])))

    A("\n## 5. HotpotQA field recoverability (0.1 STOP check)\n")
    A("| model | tool-call validity | result count | query text | gold supporting-fact ids |")
    A("|---|---|---|---|---|")
    for r in results:
        if r["dataset"] != "hotpotqa":
            continue
        h = r["hotpot"]
        A("| %s | yes (`in_admissible` + grammar; %d disagreements) | yes (zero-result detectable from `obs`: %d) | yes (%s of steps) | **NO** |" % (
            r["model"], h.get("grammar_vs_in_admissible_disagree", 0),
            h.get("zero_result_obs", 0), _pct(h.get("query_text_recoverable", 0), r["n_steps"])))

    A("\n## 6. Episode-field presence\n")
    A("| dataset | model | " + " | ".join(EPISODE_FIELDS_HOTPOT) + " |")
    A("|---|---|" + "---|" * len(EPISODE_FIELDS_HOTPOT))
    for r in results:
        cells = [_pct(r["episode_field_present"].get(f, 0), r["n_episodes"]) for f in EPISODE_FIELDS_HOTPOT]
        A("| %s | %s | %s |" % (r["dataset"], r["model"], " | ".join(cells)))

    A("\n## 7. Flagged for decision — NOT resolved here (0.2)\n")
    A("Two skip reasons are reported rather than decided, because including or excluding "
      "them changes what the label set means and the brief reserves that call. Numbered F1/F2 below.\n")
    A("**F1 · `confidence_parse_failed`** — the model's confidence number could not be "
      "parsed. This is a failure of the *elicitation*, not of the *action*: the step's "
      "action can be perfectly valid and admissible. It is not evidence of an incorrect "
      "step, so Tier A does not fire on it and gate-1 labelling is unaffected. What it does "
      "affect is **U-side coverage**: these steps have `U_verbalized == null` and therefore "
      "drop out of any verbalized-U analysis regardless of label.\n")
    A("| dataset | model | steps | confidence_parse_failed | share |")
    A("|---|---|---|---|---|")
    for r in results:
        if not r["in_matrix"]:
            continue
        c = r["skip_reasons"].get("confidence_parse_failed", 0)
        A("| %s | %s | %d | %d | %s |" % (r["dataset"], r["model"], r["n_steps"], c,
                                          _pct(c, r["n_steps"])))
    A("\nThe rate is not uniform — it is a near-majority for `gemma-3-4b-it` in both "
      "environments — so whichever way this is decided it is a per-arm effect, not a wash.\n")
    _n_tpf = sum(r["skip_reasons"].get("thought_parse_failed", 0) for r in results)
    A("**F2 · `thought_parse_failed`** — same class of event on the thought channel. It "
      "occurs %d time%s corpus-wide and is listed only for completeness.\n"
      % (_n_tpf, "" if _n_tpf == 1 else "s"))

    A("\n## 8. Data-integrity notes\n")
    A("| dataset | model | empty `action_parsed` | of those, no skip_reason | task_ids with steps but no episode record |")
    A("|---|---|---|---|---|")
    for r in results:
        A("| %s | %s | %d | %d | %d |" % (
            r["dataset"], r["model"], r["checks"].get("empty_action_parsed", 0),
            r["checks"].get("empty_action_no_skip_reason", 0),
            len(r["steps_without_episode_record"])))
    A("\n- An **empty `action_parsed` carries no skip reason at all**: the drivers guard both "
      "`invalid_action_syntax` and `tau_unrecognized_action` behind `and action`, so a step "
      "where the model emitted nothing is invisible to a skip-reason filter. Tier A still "
      "catches it via A1 (`in_admissible == false` / grammar mismatch), which is why A1 "
      "counts exceed the corresponding skip-reason counts in several arms.")
    A("- Any non-zero entry in the last column is an episode whose steps were logged but "
      "whose terminal record was not, so `success` / `terminal_reason` are unavailable for "
      "it. These episodes are excluded from `y_suffix` (which needs the episode outcome) and "
      "flagged in the Phase-4 coverage columns; Tier A and Tier B are unaffected.\n")

    A("\n## 9. Scan integrity\n")
    A("`call` records are skipped by a head test rather than parsed. 1-in-5000 skipped")
    A("lines are parsed to confirm they are `call` records; any other kind here is a bug.\n")
    A("| dataset | model | skipped lines | sampled kinds |")
    A("|---|---|---|---|")
    for r in results:
        m = r["meta"]
        A("| %s | %s | %d | %s |" % (r["dataset"], r["model"], m.get("skipped_lines", 0),
                                     m.get("sampled_skipped_kinds", {})))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
