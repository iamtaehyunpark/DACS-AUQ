"""Single entrypoint (spec §0.2): python -m src.run --config configs/<x>.yaml --stage <stage>

Stages:
  generate       roll out one condition over the configured task range -> JSONL + .traj.jsonl
  judge          label a records file (backend: local vLLM judge or frontier API)
  e0-sample      stratified 150-step sample for E0
  e0-html        build the E0 annotation page
  e0-agreement   kappa report from judge-labeled sample + human CSVs

Generation is resume-safe: task_indexes already present in the output's .traj.jsonl sidecar
are skipped, and the env is reset-cycled past non-target games without paying generation cost.
"""
from __future__ import annotations

import argparse
import json
import os

import yaml

from src.agent.llm import VLLMClient
from src.agent.loops import LoopConfig, Prompts, run_episode, task_index_of
from src.agent.prompts import load_prompt
from src.schema import write_jsonl


def _load_cfg(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _append_json(path: str, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def stage_generate(cfg: dict, condition_name: str) -> None:
    from src.env.alfworld_env import AlfworldEnv

    cond = cfg["conditions"][condition_name]
    run_id = f"{cfg['run_id_prefix']}_{condition_name}"
    out_dir = cfg.get("out_dir", "data/trajectories")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{run_id}.jsonl")
    traj_path = os.path.join(out_dir, f"{run_id}.traj.jsonl")

    done: set[int] = set()
    if os.path.exists(traj_path):
        with open(traj_path, encoding="utf-8") as f:
            done = {json.loads(line)["task_index"] for line in f if line.strip()}

    lo, hi = cfg["tasks"]["start"], cfg["tasks"]["end"]
    loop_cfg = LoopConfig(**{**cfg.get("loop", {}),
                             "auq_suffix": cond.get("auq_suffix", False),
                             "verbalized": cond.get("verbalized", True)})
    client = VLLMClient(cfg["agent"]["base_url"], cfg["agent"]["model"],
                        top_logprobs=cfg["agent"].get("top_logprobs", 20))
    # <think> ban is DECOUPLED-ONLY: the entangled AUQ prompt REQUIRES <think> tags (its
    # reasoning channel); the ban guards the ReDAct calls against native-thinking leaks.
    if cfg["agent"].get("ban_think", True) and cond["arch"] == "decoupled":
        client.ban_token("<think>")
    prompts = Prompts.load()
    env = AlfworldEnv(cfg["env"]["alfworld_config"], split=cfg["env"]["split"])

    targets = {i for i in range(lo, hi)} - done
    print(f"[generate] {run_id}: {len(targets)} episodes to run (of {hi - lo} in range)")
    resets = 0
    max_resets = 3 * max(1, len(env.game_files))
    while targets and resets < max_resets:
        res = env.reset()
        resets += 1
        idx = task_index_of(env)
        if idx not in targets:
            continue
        ep = run_episode(cond["arch"], client, env, res, run_id=run_id,
                         condition=condition_name, prompts=prompts,
                         sampling=cfg["sampling"], cfg=loop_cfg)
        write_jsonl(out_path, ep.records)
        _append_json(traj_path, ep.summary)
        targets.discard(idx)
        print(f"[generate] task {idx} ({ep.summary['task_id']}): "
              f"{ep.summary['n_steps']} steps, success={ep.summary['success']} "
              f"({len(targets)} left)")
    if targets:
        print(f"[generate] WARNING: reset budget exhausted, missing task_indexes: {sorted(targets)}")


def stage_judge(cfg: dict, in_path: str, backend: str) -> None:
    from src.judge.pipeline import judge_file

    j = cfg["judge"][backend]
    api_key = os.environ.get(j["api_key_env"], "EMPTY") if "api_key_env" in j else "EMPTY"
    client = VLLMClient(j["base_url"], j["model"], api_key=api_key,
                        chat_max_tokens=j.get("chat_max_tokens"))
    template = load_prompt(cfg["judge"]["prompt"])
    os.makedirs("data/labels", exist_ok=True)
    out_path = os.path.join("data/labels",
                            os.path.basename(in_path).replace(".jsonl", f".{backend}.labeled.jsonl"))
    stats = judge_file(in_path, out_path, client, template,
                       include_thought=cfg["judge"].get("include_thought", False),
                       judge_name=backend)
    _append_json(out_path.replace(".jsonl", ".stats.json"), stats)
    print(f"[judge:{backend}] {stats}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--stage", required=True,
                    choices=["generate", "judge", "e0-sample", "e0-html", "e0-agreement"])
    ap.add_argument("--condition", help="generate: which conditions block to run")
    ap.add_argument("--in", dest="in_path", help="judge/e0-*: input records file")
    ap.add_argument("--backend", default="local", choices=["local", "frontier", "frontier56"])
    ap.add_argument("--human-csv", nargs="*", default=[], help="e0-agreement: annotator CSVs")
    args = ap.parse_args()
    cfg = _load_cfg(args.config)

    if args.stage == "generate":
        stage_generate(cfg, args.condition or next(iter(cfg["conditions"])))
    elif args.stage == "judge":
        stage_judge(cfg, args.in_path, args.backend)
    elif args.stage == "e0-sample":
        from src.e0.sample_steps import sample_file
        os.makedirs("data/labels", exist_ok=True)
        out = "data/labels/e0_sample.jsonl"
        print(sample_file(args.in_path, out, **cfg.get("e0", {}).get("sample", {})))
    elif args.stage == "e0-html":
        from src.e0.annotation_html import build_page
        os.makedirs("results/e0", exist_ok=True)
        print(build_page("data/labels/e0_sample.jsonl", args.in_path,
                         cfg["judge"]["prompt"], "results/e0/annotation.html"))
    elif args.stage == "e0-agreement":
        from src.e0.agreement import agreement_report
        report = agreement_report(args.in_path, args.human_csv)
        os.makedirs("results/e0", exist_ok=True)
        with open("results/e0/agreement.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
