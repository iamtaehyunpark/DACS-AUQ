"""End-to-end dry run of both loop drivers against a fake client + fake env: a full episode
must produce frozen-schema-valid records with verbalized (Probe V) + post-hoc probes, stage
metrics, and tau set — and the verbalized VALUE must never appear in any downstream prompt
(grep-level invariant, handoff 2026-07-16 §4.5)."""
from src.agent.llm import Generation
from src.agent.loops import LoopConfig, Prompts, run_episode
from src.env.alfworld_env import StepResult
from src.env.tau_map import tau_of
from src.schema import validate_record

ADM = ["go to desk 1", "open drawer 2", "look", "help"]

# distinctive confidence values so the no-feedback invariant is grep-able
THOUGHT_CONF = "0.83"   # decoupled thought tag
ACTION_CONF = "0.91"    # decoupled action tag
ENTANGLED_CONF = "0.77"  # entangled AUQ tag


class FakeEnv:
    game_files = ["/x/valid_seen/pick_and_place/trial_b/game.tw-pddl",
                  "/x/valid_seen/pick_and_place/trial_a/game.tw-pddl"]

    def __init__(self):
        self.n = 0

    def current_gamefile(self):
        return self.game_files[0]

    def reset(self):
        return StepResult("-= Welcome =-\nYour task is to: put a mug on the desk.",
                          ADM, False, False, [tau_of(c) for c in ADM])

    def step(self, cmd):
        self.n += 1
        return StepResult(f"You executed {cmd}.", ADM, self.n >= 2, self.n >= 2,
                          [tau_of(c) for c in ADM])

    @staticmethod
    def task_description(obs):
        return "put a mug on the desk."


class FakeClient:
    model = "fake"

    def __init__(self):
        self.prompts: list[str] = []    # every prompt sent, for the invariant test

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        if "single integer" in prompt:
            text = "85"
        elif "YOUR CURRENT REASONING" in prompt:
            # v2 action contract: command line, then tag (close eaten by the stop string)
            text = f"go to desk 1\n<confidence>{ACTION_CONF}"
        elif "Your thought process" in prompt:
            text = (f"I should look for the mug on the desk.\n"
                    f"<confidence>{THOUGHT_CONF}</confidence>")
        else:  # entangled; </explanation> eaten by the stop string on purpose
            text = (f"<think>I need the mug.</think>\n<action>go to desk 1</action> "
                    f"<confidence>{ENTANGLED_CONF}</confidence> "
                    f"<explanation>desk is likely")
        return [Generation(text=text, tokens=[text], logprobs=[-0.5],
                           top_logprobs=[{text: -0.5}], prompt_tokens=10,
                           completion_tokens=1, finish_reason="stop")]


def _run(arch, **cfg_kw):
    env = FakeEnv()
    client = FakeClient()
    out = run_episode(arch, client, env, env.reset(), run_id="t", condition=arch,
                      prompts=Prompts.load(), sampling={"temperature": 0.7},
                      cfg=LoopConfig(step_cap=5, **cfg_kw))
    for r in out.records:
        validate_record(r)
    return out, client


class TestEntangled:
    def test_episode(self):
        out, _ = _run("entangled", auq_suffix=True)
        assert out.summary["success"] and out.summary["n_steps"] == 2
        assert out.summary["task_index"] == 1          # sorted(game_files) position
        assert out.summary["task_id"] == "alfworld/pick_and_place/trial_b"
        r = out.records[0]
        assert r["thought_text"] == "I need the mug."
        assert r["action_text"] == "go to desk 1"
        assert r["tau"] == {"I": 1, "W": 0, "R": 1, "C": "cheap"}
        p = r["probes"]
        assert abs(p["U_T_verbalized"] - (1 - float(ENTANGLED_CONF))) < 1e-9
        assert p["U_T_verbalized_parsed"] and ENTANGLED_CONF in p["U_T_verbalized_raw"]
        assert p["auq_explanation_text"] == "desk is likely"
        assert abs(p["U_T_posthoc_numeric"] - 0.15) < 1e-9
        assert p["thought_mte"] is not None and p["action_sp"] is not None
        assert r["sampling"]["seed"] == 1001           # seed_base + task_index

    def test_no_feedback_invariant(self):
        _, client = _run("entangled", auq_suffix=True)
        # the in-generation value must not appear in ANY prompt (incl. post-hoc contexts;
        # our history keeps plain actions, so this holds globally even for Cell B)
        assert all(ENTANGLED_CONF not in p for p in client.prompts)


class TestDecoupled:
    def test_episode(self):
        out, _ = _run("decoupled")
        r = out.records[0]
        # tag stripped: thought_text is byte-identical pre-tag content
        assert r["thought_text"] == "I should look for the mug on the desk."
        assert r["action_text"] == "go to desk 1"
        p = r["probes"]
        assert abs(p["U_T_verbalized"] - (1 - float(THOUGHT_CONF))) < 1e-9
        assert abs(p["U_A_verbalized"] - (1 - float(ACTION_CONF))) < 1e-9
        assert p["U_T_verbalized_parsed"] and p["U_A_verbalized_parsed"]
        assert abs(p["U_T_posthoc_numeric"] - 0.15) < 1e-9
        assert abs(p["U_A_posthoc_numeric"] - 0.15) < 1e-9
        assert p["thought_ppl"] == 0.5 and p["action_nll"] == p["action_sp"]
        assert "thought_prompt" in r["extra"] and "action_prompt" in r["extra"]

    def test_no_feedback_invariant(self):
        _, client = _run("decoupled")
        for prompt in client.prompts:
            assert THOUGHT_CONF not in prompt, "thought confidence leaked into a prompt"
            assert ACTION_CONF not in prompt, "action confidence leaked into a prompt"

    def test_action_prompt_gets_stripped_thought(self):
        out, _ = _run("decoupled")
        ap = out.records[0]["extra"]["action_prompt"]
        assert "I should look for the mug on the desk." in ap
        assert f"<confidence>{THOUGHT_CONF}" not in ap

    def test_ablation_arm_uses_v1_and_skips_probe_v(self):
        out, client = _run("decoupled", verbalized=False)
        p = out.records[0]["probes"]
        assert p["U_T_verbalized"] is None and p["U_T_verbalized_parsed"] is None
        assert p["U_A_verbalized"] is None
        # v1 prompt has no confidence instruction
        assert "confidence" not in out.records[0]["extra"]["thought_prompt"].lower()

    def test_history_interleaves(self):
        out, _ = _run("decoupled")
        hp = out.records[1]["extra"]["thought_prompt"]
        assert hp.index("Observation: -= Welcome") < hp.index("Action: go to desk 1") \
            < hp.index("Observation: You executed")
