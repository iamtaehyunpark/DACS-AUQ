"""Model/runtime configuration shared by both HotpotQA acquisition arms."""
from __future__ import annotations

import os

from openai import OpenAI

from hotpot_common import append_jsonl


class Runtime:
    def __init__(self, default_run_id: str):
        self.model = os.environ.get("REACT_MODEL", "qwen")
        self.base_url = os.environ.get("REACT_BASE_URL", "http://localhost:8000/v1")
        self.client = OpenAI(api_key=os.environ.get("REACT_API_KEY", "EMPTY"), base_url=self.base_url)
        self.temperature = float(os.environ.get("REACT_TEMPERATURE", "0.7"))
        self.top_p = float(os.environ.get("REACT_TOP_P", "0.80"))
        self.top_k = int(os.environ.get("REACT_TOP_K", "20"))
        self.min_p = float(os.environ.get("REACT_MIN_P", "0.0"))
        self.presence_penalty = float(os.environ.get("REACT_PRESENCE_PENALTY", "1.5"))
        self.repetition_penalty = float(os.environ.get("REACT_REPETITION_PENALTY", "1.0"))
        self.n_episodes = int(os.environ.get("REACT_N_EPISODES", "10"))
        self.max_steps = int(os.environ.get("REACT_MAX_STEPS", "7"))
        self.uqlog = os.environ.get("REACT_UQLOG")
        self.tokenizer_path = os.environ.get("REACT_TOKENIZER", "Qwen/Qwen3.6-35B-A3B")
        self.seed_base = int(os.environ.get("REACT_SEED_BASE", "1000"))
        self.sample_seed = int(os.environ.get("REACT_SEED", "233"))
        self.run_id = os.environ.get("REACT_RUN_ID", default_run_id)
        self.split = os.environ.get("REACT_SPLIT", "dev")
        self.num_workers = int(os.environ.get("REACT_NUM_WORKERS", "1"))
        self.worker_id = int(os.environ.get("REACT_WORKER_ID", "0"))

    def log(self, record):
        append_jsonl(self.uqlog, record)

    def chat(self, prompt: str, *, max_tokens: int, seed: int):
        """Return (content, instrumented record or None), with identical generation settings."""
        if self.uqlog:
            from uqlog import instrumented_chat

            return instrumented_chat(
                self.client,
                [{"role": "user", "content": prompt}],
                model=self.model,
                tokenizer_path=self.tokenizer_path,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                min_p=self.min_p,
                presence_penalty=self.presence_penalty,
                repetition_penalty=self.repetition_penalty,
                max_tokens=max_tokens,
                seed=seed,
                enable_thinking=False,
            )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=max_tokens,
            seed=seed,
            presence_penalty=self.presence_penalty,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
                "top_k": self.top_k,
                "min_p": self.min_p,
                "repetition_penalty": self.repetition_penalty,
            },
        )
        return response.choices[0].message.content or "", None

