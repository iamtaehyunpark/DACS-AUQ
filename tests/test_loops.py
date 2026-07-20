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


REPAIR_CONF = "0.66"    # value the model completes after a forced '<confidence>' prefix


class FakeClient:
    model = "fake"

    def __init__(self, omit_tag=False, malformed_tag=False, finish_reason="stop",
                 empty_gens=0):
        self.prompts: list[str] = []    # every prompt sent, for the invariant test
        self.seeds: list[int] = []      # seed of every call, for the retry-seed test
        self.omit_tag = omit_tag
        self.malformed_tag = malformed_tag
        self.finish_reason = finish_reason
        self.empty_gens = empty_gens    # first N MAIN-STAGE calls return empty text

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        self.seeds.append(kw.get("seed"))
        if prompt.rstrip().endswith("<confidence>"):
            # EOS-repair continuation: model completes the forced prefix
            text = f"{REPAIR_CONF}"
        elif "single integer" in prompt:
            text = "85"
        elif self.empty_gens > 0:
            # bare-EOS main-stage generation (the E0 episode-16 failure mode)
            self.empty_gens -= 1
            return [Generation(text="", tokens=[], logprobs=[], top_logprobs=[],
                               prompt_tokens=10, completion_tokens=1,
                               finish_reason="stop")]
        elif "YOUR CURRENT REASONING" in prompt:
            if self.omit_tag:
                text = "go to desk 1"
            elif self.malformed_tag:
                text = "go to desk 1\n<confidence>1.5</confidence>"
            else:  # v2 action contract: command line, then tag (close eaten by the stop string)
                text = f"go to desk 1\n<confidence>{ACTION_CONF}"
        elif "Your thought process" in prompt:
            if self.omit_tag:
                text = "I should look for the mug on the desk."
            elif self.malformed_tag:
                text = "I should look for the mug on the desk.\n<confidence>1.5</confidence>"
            else:
                text = (f"I should look for the mug on the desk.\n"
                        f"<confidence>{THOUGHT_CONF}</confidence>")
        else:  # entangled; </explanation> eaten by the stop string on purpose
            if self.omit_tag:
                text = "<think>I need the mug.</think>\n<action>go to desk 1</action>"
            else:
                text = (f"<think>I need the mug.</think>\n<action>go to desk 1</action> "
                        f"<confidence>{ENTANGLED_CONF}</confidence> "
                        f"<explanation>desk is likely")
        return [Generation(text=text, tokens=[text], logprobs=[-0.5],
                           top_logprobs=[{text: -0.5}], prompt_tokens=10,
                           completion_tokens=1, finish_reason=self.finish_reason)]


def _run(arch, client=None, **cfg_kw):
    env = FakeEnv()
    client = client or FakeClient()
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
        # per-step seeds (2026-07-20): episode base = seed_base + task_index*100,
        # step t generates under base + t; the summary keeps the episode base
        assert r["sampling"]["seed"] == 1100
        assert out.records[1]["sampling"]["seed"] == 1101
        assert out.summary["seed"] == 1100

    def test_no_feedback_invariant(self):
        _, client = _run("entangled", auq_suffix=True)
        # the in-generation value must not appear in ANY prompt: history keeps <think>+<action>
        # but NOT confidence/explanation (UAM excluded), post-hoc contexts are excised
        assert all(ENTANGLED_CONF not in p for p in client.prompts)
        # the explanation (self-assessment prose) must not reach the post-hoc context either
        posthoc_prompts = [p for p in client.prompts if "single integer" in p]
        assert posthoc_prompts and all("desk is likely" not in p for p in posthoc_prompts)

    def test_history_is_auq_format_with_think(self):
        out, _ = _run("entangled", auq_suffix=True)
        hp = out.records[1]["extra"]["prompt"]
        # AUQ A.6.2 slot format: prior thoughts ARE in entangled history, tags reconstructed,
        # confidence/explanation NOT retained (checked by value in the invariant test)
        assert "Action: <think>I need the mug.</think> <action>go to desk 1</action>" in hp


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


class TestEosRepair:
    def test_natural_parse_not_continued(self):
        out, _ = _run("decoupled")
        p = out.records[0]["probes"]
        assert p["U_T_verbalized_continued"] is False
        assert p["U_A_verbalized_continued"] is False

    def test_missing_tag_repaired_and_flagged(self):
        out, client = _run("decoupled", client=FakeClient(omit_tag=True))
        p = out.records[0]["probes"]
        assert p["U_T_verbalized_parsed"] and p["U_T_verbalized_continued"] is True
        assert abs(p["U_T_verbalized"] - (1 - float(REPAIR_CONF))) < 1e-9
        assert p["U_A_verbalized_parsed"] and p["U_A_verbalized_continued"] is True
        # a continuation prompt ends with the forced prefix
        assert any(pr.rstrip().endswith("<confidence>") for pr in client.prompts)
        assert out.records[0]["extra"]["verbalized_repair_raw"]["thought"] == REPAIR_CONF

    def test_entangled_missing_tag_repaired(self):
        out, _ = _run("entangled", client=FakeClient(omit_tag=True), auq_suffix=True)
        p = out.records[0]["probes"]
        assert p["U_T_verbalized_parsed"] and p["U_T_verbalized_continued"] is True
        assert abs(p["U_T_verbalized"] - (1 - float(REPAIR_CONF))) < 1e-9
        assert p["auq_explanation_text"] is None    # absent by construction, not backfilled

    def test_malformed_tag_not_repaired(self):
        # a given (out-of-range) answer is excluded, never overwritten
        out, client = _run("decoupled", client=FakeClient(malformed_tag=True))
        p = out.records[0]["probes"]
        assert p["U_T_verbalized"] is None and p["U_T_verbalized_parsed"] is False
        assert p["U_T_verbalized_continued"] is False
        assert not any(pr.rstrip().endswith("<confidence>") for pr in client.prompts)

    def test_length_truncation_not_repaired(self):
        out, client = _run("decoupled",
                           client=FakeClient(omit_tag=True, finish_reason="length"))
        p = out.records[0]["probes"]
        assert p["U_T_verbalized_parsed"] is False
        assert p["U_T_verbalized_continued"] is False
        assert not any(pr.rstrip().endswith("<confidence>") for pr in client.prompts)

    def test_empty_generation_never_repaired(self):
        # 2026-07-20 guard: a bare-EOS generation has no content for a confidence to
        # qualify — no forced-prefix continuation may fire (E0: 39 such repairs)
        out, client = _run("entangled", client=FakeClient(empty_gens=999), auq_suffix=True)
        p = out.records[0]["probes"]
        assert p["U_T_verbalized_parsed"] is False
        assert p["U_T_verbalized_continued"] is False
        assert not any(pr.rstrip().endswith("<confidence>") for pr in client.prompts)

    def test_repaired_value_never_feeds_forward(self):
        _, client = _run("decoupled", client=FakeClient(omit_tag=True))
        # the repaired confidence must not leak into any subsequent prompt (except the
        # forced-prefix continuation call itself, which contains only the prefix)
        for pr in client.prompts:
            if not pr.rstrip().endswith("<confidence>"):
                assert REPAIR_CONF not in pr


class TestEmptyGenerationRetry:
    """2026-07-20 amendment: one seed-offset re-draw on an empty non-cap generation."""

    def test_entangled_retry_recovers(self):
        out, client = _run("entangled", client=FakeClient(empty_gens=1), auq_suffix=True)
        r = out.records[0]
        assert r["thought_text"] == "I need the mug."     # retry produced the real generation
        retry = r["extra"]["generation_retry"]
        assert retry is not None and retry["retry_empty"] is False
        assert retry["first_finish_reason"] == "stop"
        assert retry["retry_seed"] == r["sampling"]["seed"] + 100003
        assert retry["retry_seed"] in client.seeds
        assert r["probes"]["U_T_verbalized_parsed"]
        # later steps were non-empty on the first attempt -> no retry logged
        assert out.records[1]["extra"]["generation_retry"] is None

    def test_entangled_double_empty_kept_unrepaired(self):
        out, _ = _run("entangled", client=FakeClient(empty_gens=999), auq_suffix=True)
        r = out.records[0]
        assert r["thought_text"] == ""
        assert r["extra"]["generation_retry"]["retry_empty"] is True
        assert r["probes"]["U_T_verbalized_continued"] is False

    def test_decoupled_double_empty_kept_unrepaired(self):
        out, client = _run("decoupled", client=FakeClient(empty_gens=999))
        p = out.records[0]["probes"]
        assert p["U_T_verbalized_parsed"] is False and p["U_T_verbalized_continued"] is False
        assert p["U_A_verbalized_parsed"] is False and p["U_A_verbalized_continued"] is False
        assert not any(pr.rstrip().endswith("<confidence>") for pr in client.prompts)
        retry = out.records[0]["extra"]["generation_retry"]
        assert retry["thought"]["retry_empty"] and retry["action"]["retry_empty"]
