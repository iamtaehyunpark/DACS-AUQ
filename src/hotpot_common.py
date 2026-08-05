"""Shared HotpotQA environment and acquisition helpers.

The two Hotpot acquisition arms intentionally share this module so task sampling,
Wikipedia behavior, action parsing, history retention, retry behavior, and outcome
records cannot drift between decoupled and entangled runs.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
from typing import Any

import requests


DOMAIN = "hotpotqa"
ACTION_SPECS = [
    "Search[entity] — search Wikipedia for an entity and load its page",
    "Lookup[keyword] — read the next sentence containing a keyword on the loaded page",
    "Finish[answer] — submit the final answer and end the episode",
]
_ACTION_RE = re.compile(r"^(search|lookup|finish)\[[^\r\n]*\]$", re.IGNORECASE)


def append_jsonl(path: str | None, record: dict[str, Any]) -> None:
    if not path:
        return
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def strip_think(text: str) -> str:
    return text.split("</think>", 1)[-1] if "</think>" in text else text


def clip_confidence(value: float | None) -> float | None:
    return value if value is not None and 0.0 <= value <= 1.0 else None


def parse_confidence(text: str, regex: re.Pattern[str]) -> float | None:
    match = regex.search(text or "")
    return clip_confidence(float(match.group(1))) if match else None


def parse_action_line(text: str, confidence_label: str) -> str:
    """Return the first non-empty pre-confidence line, without an ACTION label."""
    pre = re.split(
        r"\n?[ \t>]*%s:" % re.escape(confidence_label),
        text or "",
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    action = next((line.strip() for line in pre.splitlines() if line.strip()), "")
    return re.sub(r"^ACTION:\s*", "", action, flags=re.IGNORECASE).strip().strip("`").strip()


def valid_action(action: str) -> bool:
    return bool(_ACTION_RE.fullmatch((action or "").strip()))


def env_action(action: str) -> str:
    """WikiEnv's grammar is lower-case; preserve the logged model text separately."""
    action = (action or "").strip()
    return action[:1].lower() + action[1:] if action else ""


def state_hash(observation: str) -> str:
    return hashlib.sha1((observation or "").encode()).hexdigest()[:16]


def is_overflow(exc: BaseException) -> bool:
    text = str(exc).lower()
    return (
        "context length" in text
        or "context_length" in text
        or "maximum context" in text
    )


def make_env(split: str):
    """Construct the vendored ReAct Hotpot environment with a modern User-Agent."""
    import wikienv
    import wrappers

    user_agent = os.environ.get(
        "REACT_WIKI_UA",
        "ReAct-UQ-acquisition/1.0 (research; https://github.com/ysymyth/ReAct)",
    )
    if not hasattr(wikienv.requests, "_react_uq_original_get"):
        original_get = wikienv.requests.get

        def get_with_ua(url, **kwargs):
            headers = dict(kwargs.pop("headers", None) or {})
            headers.setdefault("User-Agent", user_agent)
            return original_get(url, headers=headers, **kwargs)

        wikienv.requests._react_uq_original_get = original_get
        wikienv.requests.get = get_with_ua

    env = wikienv.WikiEnv()
    env = wrappers.HotPotQAWrapper(env, split=split)
    return wrappers.LoggingWrapper(env)


def step_with_retry(env, action: str, attempts: int = 10):
    last_error = None
    for _ in range(attempts):
        try:
            return env.step(env_action(action))
        except requests.exceptions.Timeout as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError("HotpotQA environment step failed without an exception")


def sample_indices(
    dataset_size: int,
    n_episodes: int,
    seed: int,
    num_workers: int,
    worker_id: int,
) -> list[int]:
    if n_episodes < 0 or n_episodes > dataset_size:
        raise ValueError("REACT_N_EPISODES must be between 0 and %d" % dataset_size)
    if num_workers < 1 or not 0 <= worker_id < num_workers:
        raise ValueError("worker configuration must satisfy 0 <= WORKER_ID < NUM_WORKERS")
    indices = list(range(dataset_size))
    random.Random(seed).shuffle(indices)
    return indices[:n_episodes][worker_id::num_workers]


def task_metadata(env, task_id: int) -> tuple[str, str | None]:
    """Read question/gold for logging; callers must never place gold in model context."""
    node = env
    while hasattr(node, "env") and not hasattr(node, "data"):
        node = node.env
    data = getattr(node, "data", None)
    if data is None:
        return str(task_id), None
    question, gold = data[task_id]
    return str(question), str(gold)


def dataset_size(env) -> int:
    node = env
    while hasattr(node, "env") and not hasattr(node, "data"):
        node = node.env
    data = getattr(node, "data", None)
    if data is None:
        raise TypeError("could not locate HotpotQA dataset through wrapper chain")
    return len(data)


def episode_record(
    *,
    run_id: str,
    task_id: int,
    question: str,
    info: dict[str, Any] | None,
    terminal_reason: str,
    n_steps: int,
    loops: int,
    gold_answer: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    info = info or {}
    em = bool(info.get("em", 0))
    return {
        "kind": "episode",
        "domain": DOMAIN,
        "run_id": run_id,
        "task_id": task_id,
        "question": question,
        "gold_answer": info.get("gt_answer", gold_answer),
        "predicted_answer": info.get("answer"),
        "success": em,
        "em": em,
        "f1": float(info.get("f1", 0) or 0),
        "terminal_reason": terminal_reason,
        "n_steps": n_steps,
        "loop_collapse_fraction": round(loops / max(1, n_steps), 3),
        "error": error,
    }
