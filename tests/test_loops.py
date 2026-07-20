"""End-to-end dry run of both loop drivers against a fake client + fake env: a full episode
must produce frozen-schema-valid records with verbalized (Probe V) + post-hoc probes, stage
metrics, and tau set — and the verbalized VALUE must never appear in any downstream prompt
(grep-level invariant, handoff 2026-07-16 §4.5)."""
import pytest

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
                 empty_gens=0, echo_gens=0, action_leak_gens=0, action_multiline_gens=0):
        self.prompts: list[str] = []    # every prompt sent, for the invariant test
        self.seeds: list[int] = []      # seed of every call, for the retry-seed test
        self.stops: list = []           # stop kwarg of every call, for the v1-stop test
        self.omit_tag = omit_tag
        self.malformed_tag = malformed_tag
        self.finish_reason = finish_reason
        self.empty_gens = empty_gens    # first N MAIN-STAGE calls return empty text
        self.echo_gens = echo_gens      # first N MAIN-STAGE calls echo the instruction list
        self.action_leak_gens = action_leak_gens  # first N v1 action calls leak '</think>'
        self.action_multiline_gens = action_multiline_gens  # v1 action: leading \n + ramble

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        self.seeds.append(kw.get("seed"))
        self.stops.append(kw.get("stop"))
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
        elif self.echo_gens > 0:
            # instruction-list echo (the 4bd6a08 smoke failure mode): no think-close,
            # no <action> -- a degenerate non-response under the entangled contract
            self.echo_gens -= 1
            t = "- The text inside the <explanation> tag must be a single paragraph"
            return [Generation(text=t, tokens=[t], logprobs=[-0.5],
                               top_logprobs=[{t: -0.5}], prompt_tokens=10,
                               completion_tokens=16, finish_reason="stop")]
        elif "YOUR CURRENT REASONING" in prompt and self.action_leak_gens > 0:
            # v1 decoupled action call leaking a vestigial close-of-thinking token
            # (the diagnostic's actual failure mode) instead of a bare command line
            self.action_leak_gens -= 1
            text = "</think>"
            return [Generation(text=text, tokens=[text], logprobs=[-0.5],
                               top_logprobs=[{text: -0.5}], prompt_tokens=10,
                               completion_tokens=1, finish_reason=self.finish_reason)]
        elif "YOUR CURRENT REASONING" in prompt and self.action_multiline_gens > 0:
            # 1.7.0 no-stop v1 draw: leading formatting newline, then the command, then
            # post-line ramble -- the shape the removed stop=["\n"] used to truncate at
            # token 1. Distinct per-token logprobs so the span test can pin the window.
            self.action_multiline_gens -= 1
            toks = ["\n", "go to", " desk 1", "\n", "AVAILABLE"]
            lps = [-1.0, -0.25, -0.25, -1.0, -2.0]
            return [Generation(text="".join(toks), tokens=toks, logprobs=lps,
                               top_logprobs=[{t: l} for t, l in zip(toks, lps)],
                               prompt_tokens=10, completion_tokens=len(toks),
                               finish_reason="stop")]
        elif "YOUR CURRENT REASONING" in prompt:
            # only the v2 prompt (redact_action_v2.txt) instructs a confidence tag --
            # detect it the way the real model would (by the instruction's presence),
            # so a v1 recovery draw is a bare command line with no tag to leak
            if self.omit_tag or "confidence" not in prompt.lower():
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
        assert retry is not None and retry["retry_degenerate"] is False
        assert retry["retry_reason"] == "empty"
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
        assert r["extra"]["generation_retry"]["retry_degenerate"] is True
        assert r["probes"]["U_T_verbalized_continued"] is False

    def test_decoupled_double_empty_kept_unrepaired(self):
        out, client = _run("decoupled", client=FakeClient(empty_gens=999))
        p = out.records[0]["probes"]
        assert p["U_T_verbalized_parsed"] is False and p["U_T_verbalized_continued"] is False
        assert p["U_A_verbalized_parsed"] is False and p["U_A_verbalized_continued"] is False
        assert not any(pr.rstrip().endswith("<confidence>") for pr in client.prompts)
        retry = out.records[0]["extra"]["generation_retry"]
        assert retry["thought"]["retry_degenerate"] and retry["action"]["retry_degenerate"]


class TestPrefillAndEchoRetry:
    """2026-07-20 amendment after the 4bd6a08 smoke echo failure: the entangled prompt
    prefills <think> so generation begins inside the response block, and a degenerate
    (no think-close, no <action>) first draw gets one seed-offset re-draw."""

    def test_entangled_prompt_ends_with_think_prefill(self):
        out, _ = _run("entangled", auq_suffix=True)
        assert out.records[0]["extra"]["prompt"].endswith("<think>\n")

    def test_redundant_opener_still_parsed(self):
        # FakeClient emits a redundant <think> opener; the prefilled parser strips it
        out, _ = _run("entangled", auq_suffix=True)
        assert out.records[0]["thought_text"] == "I need the mug."

    def test_echo_first_draw_retried_and_recovers(self):
        out, client = _run("entangled", client=FakeClient(echo_gens=1), auq_suffix=True)
        r = out.records[0]
        assert r["thought_text"] == "I need the mug."
        retry = r["extra"]["generation_retry"]
        assert retry["retry_reason"] == "degenerate"
        assert retry["retry_degenerate"] is False
        assert retry["retry_seed"] == r["sampling"]["seed"] + 100003
        assert r["probes"]["U_T_verbalized_parsed"]

    def test_persistent_echo_kept_flagged_unrepaired(self):
        out, client = _run("entangled", client=FakeClient(echo_gens=999), auq_suffix=True)
        r = out.records[0]
        retry = r["extra"]["generation_retry"]
        assert retry["retry_reason"] == "degenerate" and retry["retry_degenerate"] is True
        # degenerate text is never given a repaired confidence (nothing for it to qualify)
        assert r["probes"]["U_T_verbalized_parsed"] is False
        assert r["probes"]["U_T_verbalized_continued"] is False
        assert not any(pr.rstrip().endswith("<confidence>") for pr in client.prompts)


class TestContextOverflow:
    """2026-07-20: a prompt outgrowing the served window ends the EPISODE gracefully
    (like the step cap), never the run. History is never trimmed to fit."""

    def test_overflow_terminates_episode_keeps_prior_steps(self):
        from src.agent.llm import ContextOverflowError

        class OverflowAtStep2(FakeClient):
            def generate(self, prompt, **kw):
                # main entangled call of step 2 blows the window; earlier calls fine
                if "YOUR TASK" not in prompt and prompt.count("Action: <think>") >= 1 \
                        and not prompt.rstrip().endswith("<confidence>") \
                        and "single integer" not in prompt:
                    raise ContextOverflowError("maximum context length exceeded (test)")
                return super().generate(prompt, **kw)

        env = FakeEnv()
        env.step = lambda cmd: (env.__dict__.__setitem__("n", env.n + 1),
                                StepResult(f"You executed {cmd}.", ADM, False, False,
                                           [tau_of(c) for c in ADM]))[1]  # never done
        client = OverflowAtStep2()
        out = run_episode("entangled", client, env, env.reset(), run_id="t",
                          condition="entangled", prompts=Prompts.load(),
                          sampling={"temperature": 0.7}, cfg=LoopConfig(step_cap=5))
        assert out.summary["n_steps"] == 1                      # step 0 kept
        assert out.summary["context_overflow_at_step"] == 1     # terminated at step 1
        for r in out.records:
            validate_record(r)

    def test_normal_episode_reports_no_overflow(self):
        out, _ = _run("entangled", auq_suffix=True)
        assert out.summary["context_overflow_at_step"] is None


class TestDecoupledActionDegenerateRetry:
    """2026-07-20 amendment from the loop-control diagnostic: the v1 (tag-free) decoupled
    action call gets the same non-empty-AND-non-degenerate retry discipline as the
    entangled path. Degenerate here = tag leakage ('</think>' etc.) — no legitimate
    ALFWorld command contains '<'. v2 is exempt (its contract legitimately ends in a tag)."""

    def test_leaked_tag_first_draw_retried_and_recovers(self):
        out, client = _run("decoupled", client=FakeClient(action_leak_gens=1),
                           verbalized=False)
        r = out.records[0]
        assert r["action_text"] == "go to desk 1"
        retry = r["extra"]["generation_retry"]["action"]
        assert retry["retry_reason"] == "degenerate"
        assert retry["retry_degenerate"] is False
        assert retry["retry_seed"] == r["sampling"]["seed"] + 100003

    def test_persistent_leak_kept_and_correctly_flagged(self):
        # THIS is the diagnostic's actual failure: before this fix, a persistent
        # '</think>' leak was accepted as the action with retry_degenerate=False
        out, client = _run("decoupled", client=FakeClient(action_leak_gens=999),
                          verbalized=False)
        r = out.records[0]
        assert r["action_text"] == "</think>"          # kept, never fabricated
        retry = r["extra"]["generation_retry"]["action"]
        assert retry["retry_reason"] == "degenerate"
        assert retry["retry_degenerate"] is True        # NOW correctly flagged (was False)
        assert r["extra"]["action_match"] == "raw"

    def test_v2_action_call_not_subject_to_degenerate_check(self):
        # v2's contract legitimately ends with '<confidence>' -- must not be flagged
        out, _ = _run("decoupled", client=FakeClient())
        assert out.records[0]["extra"]["generation_retry"]["action"] is None

    def test_thought_call_unaffected_by_action_leak_mode(self):
        out, _ = _run("decoupled", client=FakeClient(action_leak_gens=1), verbalized=False)
        assert out.records[0]["thought_text"] == "I should look for the mug on the desk."


class TestV1ActionLeadingNewlineFix:
    """2026-07-20 amendment (schema 1.7.0): stop=["\n"] on a prompt already ending in
    "\n" terminated the v1 action draw on a LEADING newline (all 31 retried diagnostic
    first draws: 1 token, finish_reason='stop'). v1 now draws with NO stop string, the
    action is the first content line (fixed rule), the degenerate check judges that
    line only, and action entropy spans the command line's tokens only."""

    @staticmethod
    def _action_calls(client):
        # the main action-stage calls: REASONING marker present, and not a post-hoc
        # probe prompt (those embed the stage context, so the marker leaks into them)
        return [i for i, p in enumerate(client.prompts)
                if "YOUR CURRENT REASONING" in p and "single integer" not in p]

    def test_v1_action_call_sends_no_stop_string(self):
        out, client = _run("decoupled", verbalized=False)
        idx = self._action_calls(client)
        assert idx and all(client.stops[i] is None for i in idx)

    def test_v2_action_call_keeps_confidence_stop(self):
        out, client = _run("decoupled")
        idx = self._action_calls(client)
        assert idx and all(client.stops[i] == ["</confidence>"] for i in idx)

    def test_leading_newline_draw_reads_first_content_line(self):
        out, client = _run("decoupled", client=FakeClient(action_multiline_gens=999),
                           verbalized=False)
        r = out.records[0]
        assert r["action_text"] == "go to desk 1"
        assert r["extra"]["action_match"] == "exact"
        # a leading newline is formatting, not a non-response: no retry may fire
        assert r["extra"]["generation_retry"]["action"] is None

    def test_degenerate_check_judges_first_content_line_only(self):
        from src.agent.loops import _degenerate_action_line
        assert _degenerate_action_line("go to desk 1\n</think>") is False  # post-line ramble
        assert _degenerate_action_line("\n\n</think>") is True             # leak IS the read
        # fixed rule: the first content line is THE action -- never search past a bad one
        assert _degenerate_action_line("</think>\ngo to desk 1") is True

    def test_action_entropy_spans_command_line_only(self):
        out, _ = _run("decoupled", client=FakeClient(action_multiline_gens=999),
                      verbalized=False)
        p = out.records[0]["probes"]
        # tokens: ["\n", "go to", " desk 1", "\n", "AVAILABLE"], lps [-1,-.25,-.25,-1,-2]
        # span must cover exactly ["go to", " desk 1"] -> sp=0.5, ppl=0.25
        assert p["action_sp"] == pytest.approx(0.5)
        assert p["action_ppl"] == pytest.approx(0.25)
