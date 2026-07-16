"""Regression tests for the post-hoc callers — the leading-newline failure mode observed in
the 2026-07-16 Step-3 smoke (stop=["\\n"] turned a leading-newline reply into empty text)."""
from src.agent.llm import Generation
from src.probes import posthoc


class Stub:
    model = "stub"

    def __init__(self, text):
        self.text = text
        self.calls = []

    def generate(self, prompt, **kw):
        self.calls.append(kw)
        return [Generation(text=self.text, tokens=[self.text], logprobs=[-0.1],
                           top_logprobs=[{self.text: -0.1}])]


class TestNumericCaller:
    def test_leading_newline_reply_parses(self):
        e = posthoc.numeric(Stub("\n85"), "ctx", "q?", seed=0)
        assert e.parsed and abs(e.value - 0.15) < 1e-9

    def test_continuation_junk_after_answer_ignored(self):
        # digits on later lines (transcript continuation) must not reach the parser
        e = posthoc.numeric(Stub("\n85\nObservation: you see 3 drawers"), "ctx", "q?", seed=0)
        assert e.parsed and abs(e.value - 0.15) < 1e-9

    def test_pure_junk_still_excluded(self):
        e = posthoc.numeric(Stub("\nno idea\n42"), "ctx", "q?", seed=0)
        assert not e.parsed and e.value is None  # first content line has no integer

    def test_no_stop_string_sent(self):
        s = Stub("85")
        posthoc.numeric(s, "ctx", "q?", seed=0)
        assert "stop" not in s.calls[0] or s.calls[0].get("stop") is None

    def test_raw_text_preserved_in_full(self):
        e = posthoc.numeric(Stub("\n85\njunk"), "ctx", "q?", seed=0)
        assert e.raw_text == "\n85\njunk"  # audit trail keeps the whole completion


class TestVerbalCaller:
    def test_leading_newline(self):
        e = posthoc.verbal(Stub("\nUnlikely."), "ctx", "q?", seed=0)
        assert e.parsed and e.value == 0.725
