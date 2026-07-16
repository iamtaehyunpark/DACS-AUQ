"""Tests for generation parsing + prompt loading (the entangled/decoupled loop plumbing)."""
from src.agent.parse import (choose_executable, parse_entangled, parse_verb_arg,
                             patch_unclosed)
from src.agent.prompts import fill, load_prompt, prompt_path


class TestPrompts:
    def test_footer_stripped(self):
        for name in ("auq_baseline_system.txt", "redact_reasoning.txt",
                     "redact_reasoning_v2.txt", "redact_action_v2.txt",
                     "judge_redact_fig9.txt", "posthoc_numeric.txt"):
            p = load_prompt(prompt_path(name))
            assert "# ---" not in p and "SOURCE" not in p, name

    def test_fill_literal_with_braces_in_body(self):
        jp = load_prompt(prompt_path("judge_redact_fig9.txt"))
        out = fill(jp, {"TRAJECTORY": "X"})
        assert "\nX" in out and '{"label": 1' in out  # JSON example intact

    def test_fill_missing_placeholder_raises(self):
        try:
            fill("no placeholder here", {"KEY": "v"})
            assert False, "should have raised"
        except ValueError:
            pass

    def test_redact_space_placeholder(self):
        t = load_prompt(prompt_path("redact_action.txt"))
        out = fill(t, {"DESCRIPTION": "d", "HISTORY": "h", "THOUGHTS": "t",
                       "AVAILABLE COMMANDS": "look, go to desk 1"})
        assert "{" not in out


class TestEntangledParse:
    GEN = ("<think>I need the mug. It could be on the desk.</think>\n"
           "<action>go to desk 1</action> <confidence>0.7</confidence> "
           "<explanation>desk is likely</explanation>")

    def test_spans_are_content_spans(self):
        tg = parse_entangled(self.GEN)
        assert self.GEN[tg.think_span[0]:tg.think_span[1]].strip() == tg.think
        assert self.GEN[tg.action_span[0]:tg.action_span[1]].strip() == tg.action
        assert tg.action == "go to desk 1" and tg.action_tag_ok

    def test_unclosed_action_tolerated(self):
        tg = parse_entangled("<think>x</think><action>open drawer 2")
        assert tg.action == "open drawer 2" and not tg.action_tag_ok

    def test_patch_unclosed(self):
        t = patch_unclosed("<explanation>partial", "explanation")
        assert t.endswith("</explanation>")
        assert patch_unclosed("<explanation>a</explanation>", "explanation").count("</explanation>") == 1


class TestChooseExecutable:
    ADM = ["go to desk 1", "open drawer 2", "look"]

    def test_exact_after_normalization(self):
        assert choose_executable("Go to desk 1.", "...", self.ADM) == ("go to desk 1", "exact")

    def test_contained_fallback(self):
        cmd, kind = choose_executable(None, "I will open drawer 2 now", self.ADM)
        assert (cmd, kind) == ("open drawer 2", "contained")

    def test_raw_passthrough(self):
        cmd, kind = choose_executable("fly to moon", "fly to moon", self.ADM)
        assert kind == "raw" and cmd == "fly to moon"


class TestVerbArg:
    def test_multiword_verbs(self):
        assert parse_verb_arg("go to desk 1") == {"verb": "go to", "arg": "desk 1"}
        assert parse_verb_arg("turn on desklamp 1") == {"verb": "turn on", "arg": "desklamp 1"}

    def test_unknown_verb_never_fails(self):
        assert parse_verb_arg("dance wildly") == {"verb": "dance", "arg": "wildly"}
