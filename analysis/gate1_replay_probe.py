#!/usr/bin/env python3
"""Feasibility probe for gate-1 Phase 3: can the ALFWorld expert planner be queried
offline, and how fast?

B1 needs the length of the REMAINING expert plan at every replayed state. Only
AlfredExpertType.PLANNER exposes that (`extra.expert_plan` = `policy_commands`, the
whole remaining plan); the HANDCODED expert returns a single next action, from which a
remaining length cannot be read. This script instantiates one trial both ways and
times them, so Phase 3 is costed before it is launched.

  gate1_replay_probe.py <task_id> [<task_id> ...]
"""
import os
import sys
import time

os.environ.setdefault("ALFWORLD_DATA", "/home/user/.cache/alfworld")

import textworld
import textworld.gym
from alfworld.agents.environment.alfred_tw_env import (AlfredDemangler, AlfredExpert,
                                                       AlfredExpertType, AlfredInfos)

ROOT = os.path.join(os.environ["ALFWORLD_DATA"], "json_2.1.1", "valid_seen")


def gamefile(task_id):
    return os.path.join(ROOT, task_id, "game.tw-pddl")


def make_env(task_id, expert_type):
    # NOTE: AlfredExpert.__init__ is (env=None, expert_type=HANDCODED), so the
    # expert type MUST be passed by keyword — alfworld's own init_env passes it
    # positionally, which silently binds it to `env` and leaves the expert on its
    # HANDCODED default. policy_commands is requested up front rather than relying
    # on the wrapper flipping it during load().
    infos = textworld.EnvInfos(won=True, admissible_commands=True,
                               policy_commands=True, facts=True,
                               extras=["gamefile", "expert_plan"])
    wrappers = [AlfredDemangler(shuffle=False), AlfredInfos]
    if expert_type is not None:
        wrappers.append(AlfredExpert(expert_type=expert_type))
    env_id = textworld.gym.register_games([gamefile(task_id)], infos, batch_size=1,
                                          asynchronous=True, max_episode_steps=50,
                                          wrappers=wrappers)
    return textworld.gym.make(env_id)


def probe(task_id):
    print("=" * 70)
    print(task_id)
    if not os.path.isfile(gamefile(task_id)):
        print("  NO GAME FILE")
        return
    for name, et in (("PLANNER", AlfredExpertType.PLANNER),
                     ("HANDCODED", AlfredExpertType.HANDCODED)):
        try:
            t0 = time.time()
            env = make_env(task_id, et)
            ob, info = env.reset()
            t_reset = time.time() - t0
            plan = info.get("extra.expert_plan", [[]])[0]
            pc = info.get("policy_commands", [None])[0]
            print("  %-9s policy_commands len=%s head=%s"
                  % (name, len(pc) if pc else pc, (pc or [])[:4]))
            print("  %-9s reset %.2fs  plan_len=%s" % (name, t_reset, len(plan) if plan else None))
            print("             plan head: %s" % (plan[:4] if plan else plan))
            # step once along the expert plan and re-read the remaining length
            if plan:
                t0 = time.time()
                ob2, _r, _d, info2 = env.step([plan[0]])
                plan2 = info2.get("extra.expert_plan", [[]])[0]
                print("             after '%s': %.2fs  plan_len=%s  obs=%r"
                      % (plan[0], time.time() - t0, len(plan2) if plan2 else None,
                         (ob2[0] or "")[:70]))
        except Exception as e:
            print("  %-9s FAILED: %s: %s" % (name, type(e).__name__, e))


if __name__ == "__main__":
    ids = sys.argv[1:]
    if not ids:
        ids = sorted(d + "/" + t for d in os.listdir(ROOT)
                     for t in os.listdir(os.path.join(ROOT, d))
                     if os.path.isfile(gamefile(d + "/" + t)))[:2]
    for t in ids:
        probe(t)
