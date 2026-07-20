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

    # -- 2026-07-20 amendment: tolerant think extraction (observed E0 failure modes) --

    def test_thinking_spelled_close(self):
        g = "<think>I need the mug.</thinking>\n<action>go to desk 1</action>"
        tg = parse_entangled(g)
        assert tg.think == "I need the mug." and tg.think_tag_ok
        assert g[tg.think_span[0]:tg.think_span[1]].strip() == tg.think
        assert tg.action == "go to desk 1"

    def test_thinking_spelled_open(self):
        tg = parse_entangled("<thinking>plan A</think><action>look</action>")
        assert tg.think == "plan A" and tg.think_tag_ok

    def test_unclosed_think_stops_at_next_tag(self):
        g = "<think>I will go to armchair 1 first.\n<action>go to armchair 1</action>"
        tg = parse_entangled(g)
        assert tg.think == "I will go to armchair 1 first." and not tg.think_tag_ok
        assert g[tg.think_span[0]:tg.think_span[1]].strip() == tg.think
        assert tg.action == "go to armchair 1"

    def test_unclosed_think_to_end_of_text(self):
        tg = parse_entangled("<think>truncated reasoning")
        assert tg.think == "truncated reasoning" and not tg.think_tag_ok

    def test_first_nonempty_think_block_wins(self):
        g = "<think>\n</think>\n<think>real plan</think>\n<action>look</action>"
        tg = parse_entangled(g)
        assert tg.think == "real plan" and tg.think_tag_ok

    def test_all_empty_think_blocks_keep_empty(self):
        tg = parse_entangled("<think>\n</think>\n<action>look</action>")
        assert tg.think == "" and tg.think_tag_ok

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


class TestPrefilledThink:
    """prefilled_think=True: the prompt ends with <think>, generation starts inside it."""

    def test_basic_close_and_action(self):
        g = "I need the mug. It is on the desk.\n</think>\n<action>go to desk 1</action>"
        tg = parse_entangled(g, prefilled_think=True)
        assert tg.think == "I need the mug. It is on the desk." and tg.think_tag_ok
        assert g[tg.think_span[0]:tg.think_span[1]].strip() == tg.think
        assert tg.action == "go to desk 1"

    def test_thinking_spelled_close(self):
        tg = parse_entangled("plan A</thinking><action>look</action>", prefilled_think=True)
        assert tg.think == "plan A" and tg.think_tag_ok

    def test_redundant_opener_stripped(self):
        tg = parse_entangled("<think>\nplan B</think><action>look</action>",
                             prefilled_think=True)
        assert tg.think == "plan B" and tg.think_tag_ok

    def test_unclosed_falls_to_next_tag(self):
        g = "partial reasoning\n<action>look</action>"
        tg = parse_entangled(g, prefilled_think=True)
        assert tg.think == "partial reasoning" and not tg.think_tag_ok
        assert tg.action == "look"

    def test_no_tags_at_all_whole_text_is_thought(self):
        tg = parse_entangled("rambling with no tags", prefilled_think=True)
        assert tg.think == "rambling with no tags" and not tg.think_tag_ok
        assert tg.action is None

    def test_empty_generation(self):
        tg = parse_entangled("", prefilled_think=True)
        assert tg.think == "" and not tg.think_tag_ok
