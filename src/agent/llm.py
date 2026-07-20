"""vLLM client for DACS — written from scratch against the OpenAI Completions API.

We use the raw Completions endpoint (not Chat) so WE own the prompt string verbatim: the AUQ
baseline system prompt, the AUQ elicitation suffix, and the ReDAct two-call prompts are sent
exactly as transcribed in prompts/. Every generation requests top-k logprobs (default 20) so
MTE/PPL/SP and the yes/no first-token probe all compute from one pass.

Thinking is OFF (spec E1★.2, frozen): we never emit a native-thinking trigger, and we optionally
pin `<think>` out of the vocabulary via logit_bias when it is a single token — belt-and-suspenders.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class ContextOverflowError(Exception):
    """prompt + max_tokens exceeded the SERVED context window (vLLM 400). Raised as a
    distinct type so the episode driver can end THAT EPISODE gracefully (logged, like the
    step cap) instead of crashing the whole run. 2026-07-20: a 50-step entangled episode
    with full AUQ history reached 30,721 prompt tokens and killed a smoke run mid-flight;
    the serve-side cap was raised 32,768 -> 65,536 (model-native RoPE window is 262,144,
    so the raise is behavior-identical), and this guard covers whatever ceiling is served."""


@dataclass
class Generation:
    text: str
    tokens: list[str] = field(default_factory=list)
    logprobs: list[float] = field(default_factory=list)        # chosen-token logprobs, per position
    top_logprobs: list[dict] = field(default_factory=list)     # per position {token: logprob}, top-k
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str | None = None


class VLLMClient:
    def __init__(self, base_url: str, model: str, *, api_key: str = "EMPTY",
                 top_logprobs: int = 20, timeout: float = 300.0,
                 chat_max_tokens: int | None = None):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self.base_url = base_url
        self.model = model
        self.top_logprobs = top_logprobs
        self.logit_bias: dict[str, int] = {}
        # chat() completion cap override (config-driven). Reasoning-tier judges spend
        # hidden reasoning tokens INSIDE max_completion_tokens, so the report-only
        # gpt-5.6-sol arm needs headroom the 4096 default doesn't give.
        self.chat_max_tokens = chat_max_tokens
        # Set True after a judge model rejects the temperature parameter (reasoning-tier
        # models lock temperature=1); subsequent chat() calls omit it. See chat().
        self._omit_chat_temperature = False

    # -- thinking-off enforcement -----------------------------------------
    def ban_token(self, s: str) -> bool:
        """Pin string `s` out of the vocabulary via logit_bias -100. Only works if `s` is a
        single token; returns whether the ban took effect (logged either way). Used for `<think>`."""
        import requests
        root = self.base_url.rsplit("/v1", 1)[0]
        try:
            r = requests.post(f"{root}/tokenize", json={"model": self.model, "prompt": s}, timeout=30)
            ids = r.json().get("tokens", [])
        except Exception as e:  # tokenize endpoint optional; a failed ban is a logged no-op, not a crash
            print(f"[llm] tokenize probe failed for {s!r}: {e}")
            return False
        if len(ids) != 1:
            print(f"[llm] cannot ban {s!r}: tokenizes to {len(ids)} tokens {ids}")
            return False
        self.logit_bias[str(ids[0])] = -100
        print(f"[llm] banned {s!r} (token id {ids[0]}) via logit_bias for ALL generations")
        return True

    # -- generation --------------------------------------------------------
    def generate(self, prompt: str, *, temperature: float = 0.7, top_p: float = 0.95,
                 n: int = 1, max_tokens: int = 512, seed: int = 0,
                 stop: list[str] | None = None,
                 guided_regex: str | None = None,
                 guided_choice: list[str] | None = None) -> list[Generation]:
        # guided_* wire vLLM structured outputs (harness-level format regulation). OFF by
        # default everywhere: forcing a format turns a refusal into an arbitrary sampled
        # token — imputation by the sampler — and erases the parse-rate signal E1★.6 reports.
        extra: dict = {}
        if guided_regex:
            extra["guided_regex"] = guided_regex
        if guided_choice:
            extra["guided_choice"] = guided_choice
        from openai import BadRequestError
        try:
            resp = self.client.completions.create(
                model=self.model, prompt=prompt, temperature=temperature, top_p=top_p,
                n=n, max_tokens=max_tokens, seed=seed, stop=stop,
                logprobs=self.top_logprobs, logit_bias=self.logit_bias or None,
                extra_body=extra or None,
            )
        except BadRequestError as e:
            if "maximum context length" in str(e):
                raise ContextOverflowError(str(e)) from e
            raise
        out = []
        for choice in resp.choices:
            lp = choice.logprobs
            tokens = list(lp.tokens or []) if lp else []
            chosen = [x if x is not None else 0.0 for x in (lp.token_logprobs or [])] if lp else []
            top = [dict(t) if t else {} for t in (lp.top_logprobs or [])] if lp else []
            out.append(Generation(
                text=choice.text, tokens=tokens, logprobs=chosen, top_logprobs=top,
                prompt_tokens=(resp.usage.prompt_tokens if resp.usage else 0),
                completion_tokens=len(tokens), finish_reason=choice.finish_reason,
            ))
        return out

    def chat(self, messages: list[dict], *, temperature: float = 0.0,
             max_tokens: int | None = None, seed: int = 0) -> str:
        """Chat endpoint (server applies the model's chat template). Used by the judge only —
        agent generations go through generate() so we own the prompt string verbatim.

        Sends `max_completion_tokens` (2026-07-20): GPT-5.x deployments reject the legacy
        `max_tokens` on chat ("Unsupported parameter", verified against the Foundry
        gpt-5.2 judge deployment); vLLM's OpenAI-compatible chat endpoint accepts both.
        temperature=0 verified accepted by gpt-5.2. Same request otherwise.

        Temperature fallback (2026-07-20, for the REPORT-ONLY gpt-5.6-sol robustness
        arm): reasoning-tier deployments reject any non-default temperature
        ("'temperature' does not support 0.0", verified live). On that specific error
        the call retries once WITHOUT the parameter and all later calls omit it, logged
        loudly — a documented deviation of the robustness arm only. The decisional
        judges (local vLLM, gpt-5.2) accept temperature=0 and never take this path."""
        from openai import BadRequestError
        cap = max_tokens if max_tokens is not None else (self.chat_max_tokens or 4096)
        kw: dict = dict(model=self.model, messages=messages,
                        max_completion_tokens=cap, seed=seed)
        if not self._omit_chat_temperature:
            kw["temperature"] = temperature
        try:
            resp = self.client.chat.completions.create(**kw)
        except BadRequestError as e:
            if "temperature" not in str(e):
                raise
            print(f"[llm] NOTE: {self.model} rejects the temperature parameter "
                  f"(reasoning-tier); omitting it for this and all later chat() calls. "
                  f"Requested temperature={temperature} is NOT honored.")
            self._omit_chat_temperature = True
            kw.pop("temperature", None)
            resp = self.client.chat.completions.create(**kw)
        return resp.choices[0].message.content or ""
