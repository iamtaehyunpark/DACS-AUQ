import os
import json
import sys
import tempfile
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

# Keep contract tests independent of the heavyweight runtime dependencies.
openai = types.ModuleType("openai")
openai.OpenAI = type("DummyOpenAI", (), {"__init__": lambda self, *a, **k: None})
sys.modules.setdefault("openai", openai)

requests = types.ModuleType("requests")
requests.exceptions = types.SimpleNamespace(Timeout=type("Timeout", (Exception,), {}))
sys.modules.setdefault("requests", requests)

uqlog = types.ModuleType("uqlog")
uqlog.instrumented_chat = lambda *a, **k: None
uqlog.char_to_token_span = lambda gen, start, end: [0, 1] if end > start else [0, 0]
uqlog.content_span = lambda gen, raw, start, ends: [0, 1] if raw else None
sys.modules.setdefault("uqlog", uqlog)

import chat_react_hotpot as decoupled
import chat_react_hotpot_entangled as entangled
import audit_hotpot
import audit_hotpot_outputs
import probes
import run_probes
from hotpot_common import sample_indices, valid_action
from hotpot_tau_map import tau_dict


class FakeRuntime:
    def __init__(self, run_id, completions):
        self.run_id = run_id
        self.seed_base = 1000
        self.max_steps = 2
        self.uqlog = "enabled"
        self.completions = list(completions)
        self.records = []

    def chat(self, prompt, *, max_tokens, seed):
        content = self.completions.pop(0)
        record = {
            "prompt_templated": prompt,
            "prompt_token_ids": [1],
            "prompt_tokens": 1,
            "completion_raw": content,
            "completion_tokens": 1,
            "finish_reason": "stop",
            "gen_logprobs": [
                {
                    "token": content,
                    "bytes": [],
                    "logprob": -0.1,
                    "top": [
                        {"token": "candidate-%d" % i, "logprob": -0.1 - i}
                        for i in range(20)
                    ],
                }
            ],
            "config": {"seed": seed, "max_tokens": max_tokens},
            "latency_ms": 1.0,
        }
        return content, record

    def log(self, record):
        self.records.append(record)


class FakeEnv:
    def reset(self, idx=None):
        self.idx = idx
        return "Question: Who was Milhouse named after?"

    def step(self, action):
        self.action = action
        return (
            "Episode finished, reward = 1\n",
            1,
            True,
            {
                "answer": "Richard Nixon",
                "gt_answer": "Richard Nixon",
                "em": True,
                "f1": 1.0,
            },
        )


class HotpotAcquisitionTests(unittest.TestCase):
    def test_action_grammar_tau_and_sampling(self):
        self.assertTrue(valid_action("Search[Milhouse]"))
        self.assertTrue(valid_action("Lookup[named after]"))
        self.assertTrue(valid_action("Finish[Richard Nixon]"))
        self.assertFalse(valid_action("Thought: Search[Milhouse]"))
        self.assertEqual(tau_dict("Search[x]")["I"], 1)
        self.assertEqual(tau_dict("Finish[x]"), {"I": 0, "W": 1, "R": 0, "C": "costly"})
        full = sample_indices(20, 10, 233, 1, 0)
        shards = sample_indices(20, 10, 233, 2, 0) + sample_indices(20, 10, 233, 2, 1)
        self.assertEqual(set(full), set(shards))

    def test_decoupled_emits_alfworld_compatible_contract(self):
        runtime = FakeRuntime(
            "hotpot_decoupled",
            [
                "The evidence identifies Nixon.\n"
                "THOUGHT_TARGET: Milhouse was named after Richard Nixon.\n"
                "THOUGHT_CONFIDENCE: 0.90",
                "ACTION: Finish[Richard Nixon]\nACTION_CONFIDENCE: 0.95",
            ],
        )
        self.assertEqual(decoupled.run_episode(FakeEnv(), runtime, 7), 1)
        self.assertEqual([r["kind"] for r in runtime.records], ["call", "call", "step", "episode"])
        calls = [r for r in runtime.records if r["kind"] == "call"]
        self.assertEqual([r["call_kind"] for r in calls], ["thought", "action"])
        step = next(r for r in runtime.records if r["kind"] == "step")
        self.assertEqual(step["domain"], "hotpotqa")
        self.assertEqual(step["action_parsed"], "Finish[Richard Nixon]")
        self.assertAlmostEqual(step["U_T_targeted_ingen"], 0.1)
        self.assertAlmostEqual(step["U_A_targeted_ingen"], 0.05)
        self.assertEqual(FakeEnv().reset(), "Question: Who was Milhouse named after?")

        grouped = list(run_probes.group_steps(runtime.records))
        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["ctx"]["domain"], "hotpotqa")
        self.assertIn("Milhouse", grouped[0]["ctx"]["task"])
        self.assert_audit_passes(runtime.records, "decoupled")

    def test_entangled_emits_joint_contract(self):
        runtime = FakeRuntime(
            "hotpot_entangled",
            [
                "THOUGHT: The retrieved fact supports Richard Nixon.\n"
                "ACTION: Finish[Richard Nixon]\nCONFIDENCE: 0.80"
            ],
        )
        self.assertEqual(entangled.run_episode(FakeEnv(), runtime, 7), 1)
        self.assertEqual([r["kind"] for r in runtime.records], ["call", "step", "episode"])
        call = runtime.records[0]
        self.assertEqual(call["call_kind"], "joint")
        self.assertTrue(call["spans"]["thought"])
        self.assertTrue(call["spans"]["action"])
        step = runtime.records[1]
        self.assertAlmostEqual(step["U_verbalized"], 0.2)
        self.assert_audit_passes(runtime.records, "entangled")

    def test_hotpot_response_ptrue_is_agg_true_record(self):
        step = {
            "run_id": "hotpot_decoupled",
            "task_id": 7,
            "step_idx": 1,
            "source_call_kind": "thought",
            "ctx": {
                "domain": "hotpotqa",
                "task": "Who was Milhouse named after?",
                "history": "(no Wikipedia actions taken yet)",
                "commands": "\n".join(
                    ["Search[entity]", "Lookup[keyword]", "Finish[answer]"]
                ),
                "thought": "The retrieved fact says Richard Nixon.",
                "action": "Finish[Richard Nixon]",
            },
        }
        original_call = probes._call

        def fake_call(client, cfg, prompt, *, max_tokens, seed):
            return "Yes", {
                "gen_logprobs": [
                    {
                        "token": "Yes",
                        "top": [
                            {"token": "Yes", "logprob": -0.1},
                            {"token": "No", "logprob": -2.0},
                        ],
                    }
                ]
            }

        probes._call = fake_call
        try:
            cfg = probes.ProbeConfig(
                model="qwen",
                tokenizer_path="unused",
                base_url="unused",
            )
            records = probes.run_step_probes(
                None,
                cfg,
                step,
                kinds=["ptrue"],
                stages=["thought", "action"],
                response_kinds=["ptrue"],
            )
        finally:
            probes._call = original_call
        self.assertEqual([r["stage"] for r in records], ["thought", "action", "response"])
        agg = records[-1]
        self.assertEqual(agg["metric_field"], "U_R_ptrue")
        self.assertEqual(agg["prompt_version_id"], "hotpot_ptrue_v1")
        self.assertIn("Taken as a whole", agg["probe_prompt"])
        self.assertTrue(agg["parse_ok"])

    def test_completed_output_coverage_gate(self):
        uq = [
            {
                "kind": "step",
                "domain": "hotpotqa",
                "task_id": 7,
                "step_idx": 1,
                "action_parsed": "Finish[Richard Nixon]",
            }
        ]
        nested = {
            "gen_logprobs": [
                {
                    "token": "Yes",
                    "top": [{"token": "candidate-%d" % i} for i in range(20)],
                }
            ]
        }
        probes_out = []
        for kind, stages in (
            ("ptrue", ("thought", "action", "response")),
            ("sep_verbalized", ("thought", "action")),
            ("posthoc_numeric", ("thought", "action")),
            ("qt_extract", ("thought",)),
            ("targeted", ("thought",)),
        ):
            for stage in stages:
                probes_out.append(
                    {
                        "kind": "probe",
                        "domain": "hotpotqa",
                        "probe_kind": kind,
                        "stage": stage,
                        "task_id": 7,
                        "step_idx": 1,
                        "metric_field": "U_R_ptrue"
                        if (kind, stage) == ("ptrue", "response")
                        else "other",
                        "record": nested,
                    }
                )
        judge = [
            {
                "kind": "judge",
                "task_id": 7,
                "step_idx": 1,
                "votes": {"judge-a": {"incorrect": 0}},
            }
        ]
        paths = []
        try:
            for records in (uq, probes_out, judge):
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".jsonl", delete=False
                ) as f:
                    paths.append(f.name)
                    for record in records:
                        f.write(json.dumps(record) + "\n")
            old_argv = sys.argv
            sys.argv = ["audit_hotpot_outputs.py", *paths, "decoupled"]
            self.assertEqual(audit_hotpot_outputs.main(), 0)
        finally:
            sys.argv = old_argv
            for path in paths:
                os.unlink(path)

    def assert_audit_passes(self, records, arm):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            path = f.name
            for record in records:
                f.write(json.dumps(record) + "\n")
        old_argv = sys.argv
        try:
            sys.argv = ["audit_hotpot.py", path, arm]
            self.assertEqual(audit_hotpot.main(), 0)
        finally:
            sys.argv = old_argv
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
