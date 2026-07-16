"""CPU-only smoke test: reset one Seen-split ALFWorld episode, print the observation, the
admissible commands, and their tau tags. Its real job is to validate the tau tagger against
REAL admissible commands and surface any command family that tau_of() does not recognize.

Run on the server under Jagent:
  cd /Users/t/sclab && lg run -- bash -lc \
    'ALFWORLD_DATA=/home/user/.cache/alfworld PYTHONPATH=<dacs> \
     /opt/anaconda3/envs/Jagent/bin/python <dacs>/scripts/smoke_env.py'
"""
import sys

from src.env.alfworld_env import AlfworldEnv, default_config_path


def main(n_steps: int = 3):
    env = AlfworldEnv(default_config_path(), split="eval_in_distribution")
    print(f"[smoke] seen game files discovered: {len(env.game_files)}")

    r = env.reset()
    print(f"[smoke] gamefile: {env.current_gamefile()}")
    print(f"[smoke] task: {env.task_description(r.observation)!r}")
    print(f"[smoke] initial obs (truncated):\n{r.observation[:400]}\n")

    unknown = []
    def report(res, label):
        print(f"--- {label}: {len(res.admissible_commands)} admissible commands ---")
        for c, t in zip(res.admissible_commands, res.admissible_tau):
            tag = t.as_dict() if t is not None else "UNRECOGNIZED"
            if t is None:
                unknown.append(c)
            print(f"  {c:<45} -> {tag}")

    report(r, "reset")
    # take a few cheap navigation/look steps to see more command families
    for i in range(n_steps):
        cmds = r.admissible_commands
        pick = next((c for c in cmds if c.startswith("go to")), cmds[0] if cmds else None)
        if not pick:
            break
        print(f"\n[smoke] step {i}: {pick!r}")
        r = env.step(pick)
        print(f"  obs: {r.observation[:200]!r}")
        report(r, f"after step {i}")
        if r.done:
            print("[smoke] episode done."); break

    print("\n[smoke] RESULT:",
          "all admissible commands recognized by tau_of()" if not unknown
          else f"UNRECOGNIZED families ({len(unknown)}): {sorted(set(unknown))}")
    return 0 if not unknown else 2


if __name__ == "__main__":
    sys.exit(main())
