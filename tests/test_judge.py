"""Tests for the judge pipeline: trajectory formatting and response parsing."""
from src.judge.pipeline import format_trajectory, group_by_trajectory, parse_judge_json


def _steps():
    return [
        {"run_id": "r", "task_id": "t", "step_idx": 1, "thought_text": "b",
         "action_text": "open drawer 2", "observation_text": "The drawer is open."},
        {"run_id": "r", "task_id": "t", "step_idx": 0, "thought_text": "a",
         "action_text": "go to desk 1", "observation_text": "You arrive at desk 1."},
    ]


class TestFormat:
    def test_numbering_from_one_and_ordering(self):
        groups = group_by_trajectory(_steps())
        steps = groups[("r", "t")]
        assert [s["step_idx"] for s in steps] == [0, 1]  # sorted despite input order
        txt = format_trajectory("find mug", steps)
        assert txt.index("step 1:") < txt.index("go to desk 1") < txt.index("step 2:")

    def test_thought_excluded_when_off(self):
        txt = format_trajectory("x", sorted(_steps(), key=lambda s: s["step_idx"]),
                                include_thought=False)
        assert "thought:" not in txt


class TestParseJudgeJson:
    def test_plain(self):
        out = parse_judge_json('{"step 1": {"label": 1, "reason": "ok"},'
                               ' "step 2": {"label": 0, "reason": "loop"}}')
        assert out == {0: (1, "ok"), 1: (0, "loop")}

    def test_code_fences_and_prose(self):
        out = parse_judge_json('Sure!\n```json\n{"step 1": {"label": 0, "reason": "r"}}\n```')
        assert out == {0: (0, "r")}

    def test_bad_label_value_skipped(self):
        assert parse_judge_json('{"step 1": {"label": 2, "reason": "r"}}') is None

    def test_garbage_is_none(self):
        assert parse_judge_json("I cannot evaluate this.") is None
        assert parse_judge_json("") is None
