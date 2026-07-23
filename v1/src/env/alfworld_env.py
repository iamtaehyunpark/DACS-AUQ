"""ALFWorld (TextWorld backend) wrapper for DACS — written from scratch against the alfworld API.

Seen split: AlfredTWEnv with train_eval="eval_in_distribution" (spec E1★.3, matches ReDAct's
'valid seen' and AUQ's 'Seen Evaluation Set'). Exposes the environment-provided admissible
commands to the prompt (spec: the ReDAct/AUQ prompts need the AVAILABLE COMMANDS list) and tags
every command with tau via the pure src/env/tau_map.py function.

Requires: the `alfworld` package importable and ALFWORLD_DATA set to the data cache. On this server
run under the `Jagent` interpreter with ALFWORLD_DATA=/home/user/.cache/alfworld (see server-env memory).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import yaml

from src.env.tau_map import tau_of

_TASK_RE = re.compile(r"your task is to:\s*(.*)", re.IGNORECASE)


@dataclass
class StepResult:
    observation: str
    admissible_commands: list[str]
    done: bool
    success: bool
    # tau tags aligned to admissible_commands (None => command in no known family; logged upstream)
    admissible_tau: list = field(default_factory=list)


class AlfworldEnv:
    """One-episode-at-a-time text ALFWorld env (batch_size=1)."""

    def __init__(self, config_path: str, split: str = "eval_in_distribution"):
        from alfworld.agents.environment import get_environment
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.split = split
        env_type = self.config["env"]["type"]  # 'AlfredTWEnv'
        self._alf = get_environment(env_type)(self.config, train_eval=split)
        self._batch = self._alf.init_env(batch_size=1)
        self._last_info: dict | None = None

    @property
    def game_files(self) -> list[str]:
        """Deterministic list of solvable game files for this split (populated at init)."""
        return list(getattr(self._alf, "game_files", []))

    # -- rollout ----------------------------------------------------------
    def reset(self) -> StepResult:
        obs, info = self._batch.reset()
        self._last_info = info
        return self._result(obs[0], info, done=False, success=False)

    def step(self, command: str) -> StepResult:
        obs, _scores, dones, info = self._batch.step([command])
        self._last_info = info
        success = bool(info.get("won", [False])[0])
        done = bool(dones[0]) or success
        return self._result(obs[0], info, done=done, success=success)

    # -- helpers ----------------------------------------------------------
    def _result(self, obs: str, info: dict, *, done: bool, success: bool) -> StepResult:
        cmds = self._admissible(info)
        return StepResult(
            observation=obs,
            admissible_commands=cmds,
            done=done,
            success=success,
            admissible_tau=[tau_of(c) for c in cmds],
        )

    @staticmethod
    def _admissible(info: dict) -> list[str]:
        ac = info.get("admissible_commands")
        if not ac:
            return []
        first = ac[0] if isinstance(ac[0], (list, tuple)) else ac
        return [str(c) for c in first]

    @staticmethod
    def task_description(observation: str) -> str | None:
        """Extract the goal string ('Your task is to: ...') from the initial observation."""
        m = _TASK_RE.search(observation or "")
        return m.group(1).strip() if m else None

    def current_gamefile(self) -> str | None:
        if not self._last_info:
            return None
        gf = self._last_info.get("extra.gamefile")
        if isinstance(gf, (list, tuple)):
            return gf[0] if gf else None
        return gf


def default_config_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "configs", "alfworld_base.yaml")
