"""Regression tests for the elicitation parsers — every case here is a failure mode that was
either observed during inspection (2026-07-16) or guards the frozen exclude-never-impute policy."""
import math

from src.metrics import elicited as E


class TestNumeric:
    def test_plain_integer(self):
        assert E.numeric_uncertainty("85") == (0.15000000000000002, True)

    def test_embedded_integer(self):
        u, ok = E.numeric_uncertainty("I am 85% confident")
        assert ok and abs(u - 0.15) < 1e-9

    def test_scale_echo_not_parsed_as_zero(self):
        # BUG (found 2026-07-16): first-integer rule parsed the echoed scale's "0" -> U=1.0.
        u, ok = E.numeric_uncertainty("On a scale of 0-100, I'd say 85")
        assert ok and abs(u - 0.15) < 1e-9

    def test_out_of_hundred_denominator(self):
        u, ok = E.numeric_uncertainty("85/100")
        assert ok and abs(u - 0.15) < 1e-9
        u, ok = E.numeric_uncertainty("I'd say 85 out of 100")
        assert ok and abs(u - 0.15) < 1e-9

    def test_over_100_excluded_not_clamped(self):
        # BUG (found 2026-07-16): 150 was clamped to 100 -> U=0.0; clamping is imputation.
        assert E.numeric_uncertainty("150") == (None, False)

    def test_bounds(self):
        assert E.numeric_uncertainty("0") == (1.0, True)
        assert E.numeric_uncertainty("100") == (0.0, True)

    def test_junk_excluded(self):
        assert E.numeric_uncertainty("no idea") == (None, False)
        assert E.numeric_uncertainty("") == (None, False)
        assert E.numeric_uncertainty(None) == (None, False)


class TestVerbal:
    def test_longest_phrase_wins(self):
        assert E.verbal_uncertainty("almost certainly not") == (0.95, True)
        assert E.verbal_uncertainty("almost certain") == (0.05, True)

    def test_unlikely_before_likely(self):
        assert E.verbal_uncertainty("Unlikely.") == (0.725, True)
        assert E.verbal_uncertainty("Likely") == (0.275, True)

    def test_junk_excluded(self):
        assert E.verbal_uncertainty("maybe?") == (None, False)


class TestYesNo:
    def test_renormalizes_variants(self):
        top = {"Yes": math.log(0.6), " No": math.log(0.3), "no": math.log(0.05)}
        u, ok = E.yesno_uncertainty(top)
        assert ok and abs(u - 0.35 / 0.95) < 1e-9

    def test_no_mass_excluded(self):
        assert E.yesno_uncertainty({"Maybe": -0.1}) == (None, False)
        assert E.yesno_uncertainty(None) == (None, False)


class TestVerbalizedConfidence:
    def test_well_formed(self):
        u, raw, ok, anomaly = E.verbalized_confidence("thought text\n<confidence>0.8</confidence>")
        assert ok and abs(u - 0.2) < 1e-9 and raw == "<confidence>0.8</confidence>" and not anomaly

    def test_missing(self):
        assert E.verbalized_confidence("no tag here") == (None, None, False, False)
        assert E.verbalized_confidence("") == (None, None, False, False)
        assert E.verbalized_confidence(None) == (None, None, False, False)

    def test_malformed_out_of_range(self):
        u, raw, ok, anomaly = E.verbalized_confidence("<confidence>1.5</confidence>")
        assert (u, ok) == (None, False) and raw is not None

    def test_multiple_tags_first_wins_anomaly_flagged(self):
        u, raw, ok, anomaly = E.verbalized_confidence(
            "<confidence>0.3</confidence> junk <confidence>0.9</confidence>")
        assert ok and abs(u - 0.7) < 1e-9 and anomaly

    def test_case_insensitive(self):
        u, _, ok, _ = E.verbalized_confidence("<Confidence>0.5</Confidence>")
        assert ok and abs(u - 0.5) < 1e-9


class TestStripAndRemove:
    def test_strip_byte_identical_pre_tag(self):
        # handoff §4.5: stripping leaves thought_text byte-identical to pre-tag content
        pre = "I should check the desk first.\nThe mug might be there."
        assert E.strip_confidence_tag(pre + "\n<confidence>0.8</confidence>") == pre

    def test_strip_no_tag_is_noop_modulo_rstrip(self):
        assert E.strip_confidence_tag("plain thought  ") == "plain thought"

    def test_strip_unclosed_tag(self):
        assert E.strip_confidence_tag("thought\n<confidence>0.8") == "thought"

    def test_remove_keeps_surrounding_text(self):
        t = ("<action>go</action> <confidence>0.7</confidence> "
             "<explanation>desk is likely</explanation>")
        out = E.remove_confidence_tags(t)
        assert "<confidence>" not in out and "0.7" not in out
        assert "<action>go</action>" in out and "desk is likely" in out

    def test_remove_unclosed_tag(self):
        out = E.remove_confidence_tags("line one\n<confidence>0.9\nline two")
        assert "0.9" not in out and "line one" in out and "line two" in out

    def test_remove_self_assessment_excises_confidence_and_explanation(self):
        t = ("<think>hm</think><action>go</action> <confidence>0.7</confidence> "
             "<explanation>I am fairly sure about the desk</explanation>")
        out = E.remove_self_assessment(t)
        assert "0.7" not in out and "fairly sure" not in out
        assert "<think>hm</think>" in out and "<action>go</action>" in out

    def test_remove_self_assessment_unclosed_explanation(self):
        out = E.remove_self_assessment("<action>go</action> <confidence>0.7</confidence> "
                                       "<explanation>partial text")
        assert "partial text" not in out and "0.7" not in out and "<action>go</action>" in out


class TestAuqEntangled:
    def test_full_parse(self):
        t = "<action>go</action><confidence>0.8</confidence><explanation>ok</explanation>"
        u, expl, ok = E.auq_entangled(t)
        assert ok and abs(u - 0.2) < 1e-9 and expl == "ok"

    def test_out_of_range_confidence_excluded(self):
        u, expl, ok = E.auq_entangled("<confidence>1.5</confidence>")
        assert (u, ok) == (None, False)

    def test_explanation_kept_when_confidence_fails(self):
        u, expl, ok = E.auq_entangled("<explanation>hmm</explanation>")
        assert (u, ok) == (None, False) and expl == "hmm"
