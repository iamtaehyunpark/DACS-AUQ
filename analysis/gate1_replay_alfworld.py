#!/usr/bin/env python3
"""Gate-1 Phase 3 — ALFWorld Tier-B labels by deterministic environment replay.

CPU only. No model is called and no trajectory is regenerated: the logged
`action_parsed` sequence is replayed into the exact trial named by `task_id`, and the
built-in TextWorld PDDL planner is queried at every state for the REMAINING expert
plan.

  B1  a step is CORRECT if it reduces the remaining expert-plan length,
      INCORRECT if it increases or leaves it unchanged.

Determinism check: at every step the replayed observation is compared to the logged
`obs`. On any divergence the episode is marked `replay_diverged`, its Tier-B labels are
dropped, it is counted, and the replay continues. Divergence above 2% of episodes is a
STOP condition and is reported as such.

Two implementation notes that are easy to get wrong:

  * `AlfredExpert.__init__(self, env=None, expert_type=HANDCODED)` takes the expert
    type as its SECOND argument. alfworld's own `init_env` passes it positionally, so
    it binds to `env` and the expert silently stays HANDCODED — which returns only a
    single next action and no remaining length. This script does not use the wrapper
    at all; it requests TextWorld's `policy_commands` directly, which is the same
    quantity `AlfredExpertType.PLANNER` would have copied.
  * The generation runs used no expert wrapper (dagger + non-train split), so
    requesting `policy_commands` is the only difference from the generating env. It
    adds information, it does not change the game text — which the per-step
    observation comparison then verifies empirically.

  gate1_replay_alfworld.py [--pivot DIR] [--out-csv ...] [--jobs N] [--arms a,b]
"""
import argparse
import collections
import csv
import hashlib
import json
import multiprocessing
import os
import sys
import time

import gate1_manifest
from gate1_inventory import MATRIX_TARGETS, iter_records

ALFWORLD_DATA = os.environ.setdefault("ALFWORLD_DATA", "/home/user/.cache/alfworld")
SPLIT = "valid_seen"          # REACT_SPLIT=eval_in_distribution in every ALFWorld run script
MAX_EPISODE_STEPS = 50        # base_config.yaml dagger.training.max_nb_steps_per_episode

COLUMNS = [
    "dataset", "model", "task_id", "step_idx", "action_parsed",
    "plan_len_before", "plan_len_after", "y_tier_b", "b_reason",
    "replay_diverged", "obs_match",
]


def gamefile(task_id):
    return os.path.join(ALFWORLD_DATA, "json_2.1.1", SPLIT, task_id, "game.tw-pddl")


def make_env(task_id):
    import textworld
    import textworld.gym
    from alfworld.agents.environment.alfred_tw_env import AlfredDemangler, AlfredInfos

    infos = textworld.EnvInfos(won=True, admissible_commands=True, policy_commands=True,
                               extras=["gamefile"])
    env_id = textworld.gym.register_games(
        [gamefile(task_id)], infos, batch_size=1, asynchronous=True,
        max_episode_steps=MAX_EPISODE_STEPS,
        wrappers=[AlfredDemangler(shuffle=False), AlfredInfos])
    return textworld.gym.make(env_id)


def plan_len(info):
    """Remaining expert-plan length, or None when the planner returns nothing.

    None means the planner could not produce a plan from this state — typically an
    irreversible action left the goal unreachable. That is NOT folded into "increased"
    here; it is recorded separately so the call stays visible.
    """
    pc = info.get("policy_commands")
    if not pc:
        return None
    pc = pc[0]
    return None if pc is None else len(pc)


def replay_episode_iter(task_id, steps):
    """Yield (row, diverged_so_far), one step at a time.

    Streaming rather than returning a list so the caller can checkpoint after every
    step. A handful of ALFWorld kitchen states send the PDDL planner into a search
    that does not return within any usable budget; without checkpointing, killing
    such an episode would also discard the 30 steps already replayed correctly
    before it.
    """
    rows = []
    if not os.path.isfile(gamefile(task_id)):
        for idx, action, _obs in steps:
            yield {"task_id": task_id, "step_idx": idx, "action_parsed": action,
                   "plan_len_before": "", "plan_len_after": "", "y_tier_b": "",
                   "b_reason": "no_game_file", "replay_diverged": 0,
                   "obs_match": ""}, False
        return

    env = make_env(task_id)
    _ob, info = env.reset()
    before = plan_len(info)
    diverged = False

    for idx, action, logged_obs in steps:
        if diverged:
            yield {"task_id": task_id, "step_idx": idx, "action_parsed": action,
                   "plan_len_before": "", "plan_len_after": "", "y_tier_b": "",
                   "b_reason": "replay_diverged", "replay_diverged": 1,
                   "obs_match": ""}, True
            continue
        ob, _r, _d, info = env.step([action])
        obs = ob[0]
        after = plan_len(info)
        match = int(obs == logged_obs)
        if not match:
            # First divergence: this step and every later one in the episode are
            # unusable. The episode is counted once and the replay stops labelling.
            diverged = True
            yield {"task_id": task_id, "step_idx": idx, "action_parsed": action,
                   "plan_len_before": before if before is not None else "",
                   "plan_len_after": after if after is not None else "",
                   "y_tier_b": "", "b_reason": "replay_diverged",
                   "replay_diverged": 1, "obs_match": 0}, True
            continue

        if before is None or after is None:
            y, reason = "", ("plan_unavailable_before" if before is None
                             else "plan_unavailable_after")
        elif after < before:
            y, reason = 0, "B1_plan_shortened"          # 0 = correct
        else:
            y, reason = 1, "B1_plan_not_shortened"      # 1 = incorrect
        yield {"task_id": task_id, "step_idx": idx, "action_parsed": action,
               "plan_len_before": before if before is not None else "",
               "plan_len_after": after if after is not None else "",
               "y_tier_b": y, "b_reason": reason, "replay_diverged": 0,
               "obs_match": 1}, False
        before = after


def load_arm_steps(pivot, dataset, model, limit_bytes):
    """task_id -> [(step_idx, action, obs)] in logged order."""
    by_ep = collections.OrderedDict()
    path = os.path.join(pivot, dataset, model, "uq.jsonl")
    for kind, rec in iter_records(path, limit_bytes):
        if kind != "step":
            continue
        by_ep.setdefault(rec["task_id"], []).append(
            (rec["step_idx"], rec.get("action_parsed") or "", rec.get("obs")))
    for tid in by_ep:
        by_ep[tid].sort(key=lambda t: t[0])
    return by_ep


def _job_key(dataset, model, task_id):
    h = hashlib.sha1(("%s|%s|%s" % (dataset, model, task_id)).encode()).hexdigest()[:16]
    return "%s__%s__%s" % (dataset, model, h)


def _child(shard_path, dataset, model, task_id, steps):
    """Runs in its own process so the parent can kill it on timeout.

    A Pool is not usable here: its workers are daemonic and cannot be terminated
    mid-task, and the TextWorld PDDL planner spends minutes inside C code on some
    ALFWorld kitchen states, where a Python-level signal handler would never run.

    Every step is checkpointed to `<shard>.partial`, so an episode killed at the
    timeout still contributes the steps it did finish.
    """
    t0 = time.time()
    rows, diverged = [], False
    partial = shard_path + ".partial"
    try:
        for row, div in replay_episode_iter(task_id, steps):
            row["dataset"] = dataset
            row["model"] = model
            rows.append(row)
            diverged = diverged or div
            with open(partial + ".tmp", "w") as f:
                json.dump({"rows": rows, "diverged": diverged,
                           "seconds": time.time() - t0, "timed_out": False}, f)
            os.replace(partial + ".tmp", partial)
    except Exception as e:
        done = {r["step_idx"] for r in rows}
        for idx, a, _o in steps:
            if idx not in done:
                rows.append({"dataset": dataset, "model": model, "task_id": task_id,
                             "step_idx": idx, "action_parsed": a,
                             "plan_len_before": "", "plan_len_after": "", "y_tier_b": "",
                             "b_reason": "replay_error:%s" % type(e).__name__,
                             "replay_diverged": 0, "obs_match": ""})
    tmp = shard_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"rows": rows, "diverged": diverged, "seconds": time.time() - t0,
                   "timed_out": False}, f)
    os.replace(tmp, shard_path)      # atomic: a shard is either absent or complete
    if os.path.exists(partial):
        os.remove(partial)


def _abort_shard(shard_path, dataset, model, task_id, steps, limit, reason):
    """Finalise an episode the replay could not complete.

    Whatever the child checkpointed is kept; only the steps it never reached carry
    `reason`. Nothing is dropped silently — every unlabelable step takes its reason
    into the coverage report.
    """
    partial = shard_path + ".partial"
    rows, diverged = [], False
    if os.path.exists(partial):
        try:
            with open(partial) as f:
                d = json.load(f)
            rows, diverged = d["rows"], d["diverged"]
        except (ValueError, KeyError):
            rows, diverged = [], False
    done = {r["step_idx"] for r in rows}
    for idx, a, _o in steps:
        if idx in done:
            continue
        rows.append({"dataset": dataset, "model": model, "task_id": task_id,
                     "step_idx": idx, "action_parsed": a, "plan_len_before": "",
                     "plan_len_after": "", "y_tier_b": "", "b_reason": reason,
                     "replay_diverged": 0, "obs_match": ""})
    rows.sort(key=lambda r: r["step_idx"])
    with open(shard_path, "w") as f:
        json.dump({"rows": rows, "diverged": diverged, "seconds": limit,
                   "timed_out": True, "steps_recovered": len(done)}, f)
    if os.path.exists(partial):
        os.remove(partial)


def run_jobs(jobs, shard_dir, jobs_n, timeout, progress_path):
    os.makedirs(shard_dir, exist_ok=True)
    os.makedirs(os.path.dirname(progress_path) or ".", exist_ok=True)
    prog = open(progress_path, "a", buffering=1)
    pending = []
    for dataset, model, task_id, steps in jobs:
        shard = os.path.join(shard_dir, _job_key(dataset, model, task_id) + ".json")
        if os.path.exists(shard):
            continue                 # already done on an earlier run — resume
        pending.append((shard, dataset, model, task_id, steps))
    done_already = len(jobs) - len(pending)
    prog.write("start: %d jobs, %d already done, %d to run\n"
               % (len(jobs), done_already, len(pending)))

    live = []                        # [(proc, deadline, args)]
    t0 = time.time()
    finished = 0
    while pending or live:
        while pending and len(live) < jobs_n:
            shard, dataset, model, task_id, steps = pending.pop(0)
            p = multiprocessing.Process(
                target=_child, args=(shard, dataset, model, task_id, steps))
            p.start()
            live.append((p, time.time() + timeout,
                         (shard, dataset, model, task_id, steps)))
        time.sleep(0.5)
        still = []
        for p, deadline, argv in live:
            if not p.is_alive():
                p.join()
                finished += 1
                shard = argv[0]
                if not os.path.exists(shard):
                    # died without writing (OOM-killed, segfault): record it rather
                    # than silently dropping the episode
                    _abort_shard(*argv, limit=-1, reason="replay_process_died")
                    prog.write("%d/%d died_without_shard %s\n"
                               % (finished + done_already, len(jobs), argv[3]))
                else:
                    with open(shard) as f:
                        d = json.load(f)
                    prog.write("%d/%d %.1fs elapsed=%.0fs %s/%s %s diverged=%d steps=%d%s\n"
                               % (finished + done_already, len(jobs), d["seconds"],
                                  time.time() - t0, argv[1], argv[2], argv[3],
                                  int(d["diverged"]), len(d["rows"]),
                                  " TIMEOUT" if d["timed_out"] else ""))
                continue
            if time.time() > deadline:
                p.terminate()
                p.join(10)
                if p.is_alive():
                    p.kill()
                    p.join()
                _abort_shard(*argv, limit=timeout, reason="plan_timeout")
                finished += 1
                prog.write("%d/%d TIMEOUT(%ds) elapsed=%.0fs %s/%s %s\n"
                           % (finished + done_already, len(jobs), timeout,
                              time.time() - t0, argv[1], argv[2], argv[3]))
                continue
            still.append((p, deadline, argv))
        live = still
    prog.close()


def collect(shard_dir):
    rows, meta = [], {}
    for fn in sorted(os.listdir(shard_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(shard_dir, fn)) as f:
            d = json.load(f)
        rows.extend(d["rows"])
        if d["rows"]:
            key = (d["rows"][0]["dataset"], d["rows"][0]["model"],
                   str(d["rows"][0]["task_id"]))
            meta[key] = {"diverged": d["diverged"], "timed_out": d["timed_out"]}
    return rows, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pivot", default="result/pivot")
    ap.add_argument("--manifest", default="reports/gate1/input_manifest.json")
    ap.add_argument("--out-csv", default="reports/gate1/tier_b_alfworld.csv")
    ap.add_argument("--out-json", default="reports/gate1/tier_b_alfworld_summary.json")
    ap.add_argument("--shard-dir", default="reports/gate1/replay_shards")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=600,
                    help="hard per-episode wall-clock cap. ~97%% of episodes finish in "
                         "under a minute; a handful of ALFWorld kitchen states send the "
                         "PDDL planner into a search that does not come back, and those "
                         "steps are recorded as plan_timeout rather than waited on")
    ap.add_argument("--arms", default=None, help="comma-separated model names; default all")
    ap.add_argument("--progress", default="reports/gate1/replay_progress.log")
    ap.add_argument("--collect-only", action="store_true")
    args = ap.parse_args()

    pins = gate1_manifest.load(args.manifest, args.pivot)
    d = os.path.join(args.pivot, "alfworld")
    models = sorted(m for m in os.listdir(d)
                    if os.path.isfile(os.path.join(d, m, "uq.jsonl")))
    if args.arms:
        models = [m for m in models if m in args.arms.split(",")]

    jobs = []
    for model in models:
        by_ep = load_arm_steps(args.pivot, "alfworld", model,
                               pins["alfworld/%s/uq.jsonl" % model])
        sys.stderr.write("queued alfworld/%s: %d episodes\n" % (model, len(by_ep)))
        sys.stderr.flush()
        for tid, steps in by_ep.items():
            jobs.append(("alfworld", model, tid, steps))

    if not args.collect_only:
        run_jobs(jobs, args.shard_dir, args.jobs, args.timeout, args.progress)

    rows, meta = collect(args.shard_dir)
    rows.sort(key=lambda r: (r["dataset"], r["model"], str(r["task_id"]), r["step_idx"]))
    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    by_arm = collections.defaultdict(list)
    for r in rows:
        by_arm[(r["dataset"], r["model"])].append(r)
    summary = {}
    for key, rs in sorted(by_arm.items()):
        ds, m = key
        eps = {(ds, m, str(r["task_id"])) for r in rs}
        div = sum(1 for e in eps if meta.get(e, {}).get("diverged"))
        tmo = sum(1 for e in eps if meta.get(e, {}).get("timed_out"))
        summary["%s/%s" % key] = {
            "episodes": len(eps), "episodes_diverged": div, "episodes_timed_out": tmo,
            "divergence_rate": div / len(eps) if eps else None,
            "steps": len(rs),
            "labelled_correct": sum(1 for r in rs if r["y_tier_b"] == 0),
            "labelled_incorrect": sum(1 for r in rs if r["y_tier_b"] == 1),
            "reasons": dict(collections.Counter(r["b_reason"] for r in rs)),
            "in_matrix": m in MATRIX_TARGETS["alfworld"],
        }
    with open(args.out_json, "w") as f:
        json.dump(summary, f, indent=2)

    for k, v in summary.items():
        flag = "  <-- STOP (>2%)" if (v["divergence_rate"] or 0) > 0.02 else ""
        print("%-42s eps=%3d diverged=%3d (%.1f%%) timeout=%3d%s" % (
            k, v["episodes"], v["episodes_diverged"],
            100 * (v["divergence_rate"] or 0), v["episodes_timed_out"], flag))
    print("wrote %s (%d step rows) and %s" % (args.out_csv, len(rows), args.out_json))


if __name__ == "__main__":
    main()
