"""The two agent loops (spec §0.5, E1★.3). Both write the frozen schema.

PROBE V (verbalized, in-generation — PRIMARY, both architectures, theory §2.4): confidence
emitted in the same generation as the content it qualifies. Entangled: AUQ's verbatim
suffix (its parsed <confidence> IS U_T_verbalized). Decoupled: v2 prompts instruct a
closing <confidence> tag on both stages; the tag is STRIPPED before anything is passed
downstream (action prompt, env execution, history) — the verbalized value never feeds
forward. The ONLY sanctioned feedback is Cell B's AUQ mechanism (in-context persistence
is the published design under evaluation).

Entangled (Cells A+B): AUQ baseline system prompt (App. A.6.1) + elicitation suffix
(App. A.6.2), ONE generation per step emitting <think>/<action>/<confidence>/<explanation>.
Cell A entropy comes from this run's logprobs.

Decoupled (Cells C+D): ReDAct two-call (Fig 5 reasoning -> Fig 6 action), v2 contracts with
the confidence tag. Stage entropy (thought_*/action_*) is computed over the PRE-TAG span
only, so Cell C's anchor comparison is not contaminated by tag tokens. cfg.verbalized=False
switches to the v1 (tag-free) prompts — the E1b contamination-ablation arm.

Post-hoc self-evaluation probes (P1/U_A-numeric — comparators) ride along as extra calls.

Interpretation decisions not pinned by either paper (documented, config-controlled):
- entangled history entry: "Step i: Observation: {obs} Action: {action}" (AUQ A.6.2's
  structure, WITHOUT confidence propagation — UAM is their mechanism, not the probe);
- decoupled HISTORY: initial observation followed by Action:/Observation: lines
  (thoughts excluded by default — ReDAct regenerates reasoning per step).

tau comes from tau_of() on the EXECUTED action string; unrecognized -> tau None + counted.
Seeds (amended 2026-07-20, pre E0-full data, jointly for E0+E1): episode base
= seed_base + task_index * _SEED_STRIDE, and step t generates under base + t.
task_index is the game's position in the SORTED game_files list — deterministic
across runs regardless of env reset order (spec §0.1). The old per-episode seed
(reused for every step) made the RNG stream identical across steps; combined with
the copy-collapsed distributions of stuck loops it produced byte-exact locked
repetition (smoke: 41 identical thoughts, P(exact) ~0.3/step under independent
draws). Per-step seeds keep full reproducibility while restoring across-step
sampling independence — loops may still repeat (the distribution is collapsed
either way) but drift and fork as they would in deployment.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field

from src.agent.llm import ContextOverflowError, VLLMClient
from src.agent.parse import parse_entangled, patch_unclosed, choose_executable, parse_verb_arg
from src.agent.prompts import fill, load_prompt, prompt_path
from src.env.alfworld_env import AlfworldEnv
from src.env.tau_map import tau_of
from src.metrics.elicited import (auq_entangled, remove_self_assessment,
                                  strip_confidence_tag, verbalized_confidence)
from src.metrics.logprob import char_span_to_token_range, stage_metrics
from src.probes import posthoc
from src.schema import make_record, new_probes


@dataclass
class LoopConfig:
    step_cap: int = 50
    seed_base: int = 1000
    history_window: int = 0            # 0 = full history
    history_include_thoughts: bool = False
    max_action_tokens: int = 80        # room for the command line + confidence tag (v2)
    verbalized: bool = True            # decoupled: v2 (tagged) prompts; False = E1b ablation arm
    posthoc_numeric_thought: bool = True
    posthoc_numeric_action: bool = True
    posthoc_guided: bool = False
    auq_suffix: bool = True            # entangled only; False = vanilla-ReAct reserve run


@dataclass
class Prompts:
    entangled: str = ""
    entangled_suffix: str = ""
    thought: str = ""                  # v2 (confidence tag) — primary
    action: str = ""                   # v2 (confidence tag) — primary
    thought_v1: str = ""               # tag-free — contamination-ablation arm
    action_v1: str = ""
    posthoc_numeric: str = ""
    posthoc_numeric_action: str = ""

    @classmethod
    def load(cls) -> "Prompts":
        return cls(
            entangled=load_prompt(prompt_path("auq_baseline_system.txt")),
            entangled_suffix=load_prompt(prompt_path("elicit_auq_entangled.txt")),
            thought=load_prompt(prompt_path("redact_reasoning_v2.txt")),
            action=load_prompt(prompt_path("redact_action_v2.txt")),
            thought_v1=load_prompt(prompt_path("redact_reasoning.txt")),
            action_v1=load_prompt(prompt_path("redact_action.txt")),
            posthoc_numeric=load_prompt(prompt_path("posthoc_numeric.txt")),
            posthoc_numeric_action=load_prompt(prompt_path("posthoc_numeric_action.txt")),
        )


@dataclass
class EpisodeOut:
    records: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def task_index_of(env: AlfworldEnv) -> int:
    """Position of the current game in the sorted game_files list (stable task identity)."""
    return sorted(env.game_files).index(env.current_gamefile())


def task_id_of(gamefile: str) -> str:
    """'.../valid_seen/<task_type>/<trial>/game.tw-pddl' -> 'alfworld/<task_type>/<trial>'."""
    parts = gamefile.rstrip("/").split("/")
    return "alfworld/" + "/".join(parts[-3:-1]) if len(parts) >= 3 else gamefile


def _sha(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


# Per-episode seed block width. Step t of episode e generates under
# seed_base + e*_SEED_STRIDE + t, so blocks never overlap while step_cap <= stride,
# and the max first-attempt seed (1000 + 139*100 + 49 = 15,949 over the full 140-task
# roster) stays far below the minimum retry seed (1000 + _RETRY_SEED_OFFSET = 101,003)
# — the two seed populations can never collide.
_SEED_STRIDE = 100


# Amendment 2026-07-20 (pre E0 rerun): one E0 episode degenerated into bare-EOS
# generations (empty text, finish_reason 'stop') for 39/50 steps — empty action ->
# "Nothing happens." -> blank history entry -> repeat. A same-seed retry would
# deterministically reproduce the same sample, so the single retry re-draws under
# seed + _RETRY_SEED_OFFSET (episode seeds are seed_base + task_index, far below the
# offset, so retry seeds can never collide with a first-attempt seed).
_RETRY_SEED_OFFSET = 100003


def _degenerate_entangled(text: str) -> bool:
    """A non-response under the entangled contract: the model neither finished thinking
    (no </think> variant) nor acted (no <action> opener). Observed mode (4bd6a08 smoke):
    first-token continuation of the instruction suffix's bullet list — per-step seeds
    sample the model's true per-draw tail risk ~50x/episode where the old per-episode
    seed sampled it once, so onsets that were latent became near-certain. Such text
    carries no measurable step content: no probe target, no executable action — only
    history-poisoning potential (the raw-action fallback would feed it forward as an
    <action>, which is what cascaded 2 onsets into 71/104 bad steps)."""
    lo = text.lower()
    return "</think" not in lo and "<action>" not in lo


_TAG_LEAK_RE = re.compile(r"<[a-zA-Z/]")


def _degenerate_action_line(text: str) -> bool:
    """Amendment 2026-07-20, decoupled loop-control diagnostic: the v1 (tag-free) action
    contract asks for exactly one bare command line. Qwen3.6's reasoning-tuned habits
    leak past it -- observed: an immediate blank first token (~45% of action calls in the
    diagnostic), and on RETRY, a stray '</think>' (a vestigial close of reasoning the
    one-line contract suppressed) accepted as the literal action because the retry path
    had no content check, only an emptiness check. '</think>' then executed raw
    ("Nothing happens") and rendered into the next step's history as
    'Action: </think>' -- same failure CLASS as the entangled instruction-echo cascade
    (0617ee5), different symptom. No legitimate ALFWorld command contains '<': admissible
    strings are plain lowercase phrases (src/env/tau_map.py normalize_action), so any '<'
    followed by a letter or slash is tag leakage, never a real answer."""
    return bool(_TAG_LEAK_RE.search(text))


def _generate_nonempty(client: VLLMClient, prompt: str, *, seed: int,
                       degenerate=None, **kw):
    """One generation attempt plus AT MOST one re-draw if the model produced a
    non-response: empty/whitespace text, or text the `degenerate` predicate rejects —
    never on a length-cap hit (that is a truncated real response, not a non-response).
    Returns (gen, retry_log); retry_log is None when the first attempt stood, else
    {first_finish_reason, first_completion_tokens, retry_reason, retry_seed,
    retry_degenerate}. If the re-draw is degenerate too, it is KEPT and logged —
    never a third draw, never imputation."""
    first = client.generate(prompt, seed=seed, **kw)[0]
    is_empty = not first.text.strip()
    is_degen = degenerate is not None and degenerate(first.text)
    if (not is_empty and not is_degen) or first.finish_reason == "length":
        return first, None
    retry_seed = seed + _RETRY_SEED_OFFSET
    gen = client.generate(prompt, seed=retry_seed, **kw)[0]
    return gen, {"first_finish_reason": first.finish_reason,
                 "first_completion_tokens": first.completion_tokens,
                 "retry_reason": "empty" if is_empty else "degenerate",
                 "retry_seed": retry_seed,
                 "retry_degenerate": (not gen.text.strip()
                                      or (degenerate is not None and degenerate(gen.text)))}


def _repair_confidence(client: VLLMClient, base_prompt: str, generation_text: str,
                       samp: dict, seed: int):
    """EOS-repair continuation (pre-data amendment 2026-07-16). Trigger: the generation
    ended WITHOUT any <confidence> tag (smoke: 18/104 steps EOS'd after </action>).
    Mechanics: continue from prompt + generation + '\\n<confidence>' under the SAME sampling
    params — autoregressively this samples the distribution the model would have continued
    with had it not emitted EOS; nothing is supplied, no judgment question is asked, so the
    reading stays in-generation under the §2.4 stipulation. Repaired values are flagged
    (U_*_verbalized_continued) and sensitivity-analyzed with/without.
    NOT triggered when a tag is present but malformed/out-of-range — that is a given answer,
    excluded per the frozen policy (overwriting it would be imputation). NOT triggered on
    length-truncated generations either (callers guard on finish_reason): a cap-hit stops
    the model mid-sentence, so the continuation-identity argument does not hold there.
    Returns (U, raw_tag, parsed, continuation_text)."""
    cont = client.generate(base_prompt + generation_text.rstrip() + "\n<confidence>",
                           **samp, max_tokens=8, seed=seed, stop=["</confidence>"])[0]
    tag = "<confidence>" + cont.text.strip() + "</confidence>"
    u, raw, ok, _ = verbalized_confidence(tag)
    return u, raw, ok, cont.text


def _window(items: list, window: int) -> list:
    return items if window <= 0 else items[-window:]


def run_episode(arch: str, client: VLLMClient, env: AlfworldEnv, res, *, run_id: str,
                condition: str, prompts: Prompts, sampling: dict, cfg: LoopConfig) -> EpisodeOut:
    """Roll out ONE episode. `res` is the StepResult from the caller's env.reset() — the
    caller resets so it can inspect the gamefile and SKIP non-target episodes before any
    generation cost is paid (env cycles games on reset; order is not assumed)."""
    gamefile = env.current_gamefile()
    t_index = task_index_of(env)
    task_id = task_id_of(gamefile)
    if cfg.step_cap > _SEED_STRIDE:
        raise ValueError(f"step_cap {cfg.step_cap} > seed stride {_SEED_STRIDE}: "
                         "episode seed blocks would overlap")
    ep_seed = cfg.seed_base + t_index * _SEED_STRIDE
    task = env.task_description(res.observation) or ""
    samp = {"temperature": sampling.get("temperature", 0.7),
            "top_p": sampling.get("top_p", 0.95)}
    max_tokens = sampling.get("max_tokens", 512)

    records: list[dict] = []
    history: list[dict] = []          # {obs, action, thought}
    initial_obs = res.observation
    current_obs = res.observation
    n_tau_unknown = 0
    success = False

    context_overflow_at: int | None = None
    for t in range(cfg.step_cap):
        step = _entangled_step if arch == "entangled" else _decoupled_step
        try:
            rec, action_exec = step(
                client, prompts, cfg, samp, max_tokens, ep_seed + t,
                task=task, initial_obs=initial_obs, current_obs=current_obs,
                history=history, admissible=res.admissible_commands, t=t,
            )
        except ContextOverflowError:
            # The prompt outgrew the SERVED window: end this episode like a step-cap hit —
            # logged in the summary, prior steps kept, run continues. Never trim history to
            # squeeze under the ceiling (that would silently change the condition).
            print(f"[loops] context overflow at step {t} of {task_id}; episode terminated")
            context_overflow_at = t
            break
        res = env.step(action_exec)
        tau = tau_of(action_exec)
        if tau is None:
            n_tau_unknown += 1

        record = make_record(
            run_id=run_id, condition=condition, task_id=task_id, step_idx=t,
            state_summary_hash=rec["state_hash"],
            thought_text=rec["thought"], action_text=action_exec,
            action_parsed=parse_verb_arg(action_exec),
            tau=tau.as_dict() if tau else None,
            observation_text=res.observation,
            probes=rec["probes"],
            sampling={**samp, "max_tokens": max_tokens, "seed": ep_seed + t,
                      "model": client.model},
            timing=rec["timing"],
        )
        record["extra"] = {**rec["extra"], "task": task, "gamefile": gamefile,
                           "task_index": t_index}
        records.append(record)

        history.append({"obs": current_obs, "action": action_exec, "thought": rec["thought"]})
        current_obs = res.observation
        success = res.success
        if res.done:
            break

    return EpisodeOut(records=records, summary={
        "run_id": run_id, "condition": condition, "task_id": task_id,
        "task_index": t_index, "gamefile": gamefile, "task": task, "seed": ep_seed,
        "n_steps": len(records), "success": bool(success),
        "n_tau_unrecognized": n_tau_unknown, "model": client.model,
        "context_overflow_at_step": context_overflow_at,
    })


# -- one step, entangled ----------------------------------------------------

def _entangled_step(client, prompts: Prompts, cfg: LoopConfig, samp, max_tokens, seed, *,
                    task, initial_obs, current_obs, history, admissible, t):
    shown = _window(history, cfg.history_window)
    # AUQ A.6.2 history format, VERIFIED against their PDF: the {action_history} slot carries
    # the prior generation's <think> + <action>. Confidence/explanation are NOT retained —
    # that retention is UAM (their System-1 mechanism), excluded by recorded decision
    # (probe, not mechanism); it also preserves the no-feedback invariant across steps.
    hist_str = " ".join(
        f"Step {i + 1}: Observation: {h['obs']} Action: "
        f"<think>{h['thought']}</think> <action>{h['action']}</action>"
        for i, h in enumerate(shown)
    ) or "(none)"
    prompt = fill(prompts.entangled, {
        "task_description": task, "step_count": t, "history_length": len(shown),
        "action_history": hist_str, "current_step": t + 1,
        "current_observation": current_obs,
        "admissible_actions": ", ".join(admissible),
    })
    if cfg.auq_suffix:
        prompt = prompt.rstrip() + "\n" + prompts.entangled_suffix
    stop_tag = "explanation" if cfg.auq_suffix else "action"
    # PREFILL (amendment 2026-07-20, post per-step-seed echo failure): the prompt ends
    # with the opening <think> tag, so token 1 is already inside the response block —
    # the degenerate openings (continue-the-instruction-list echo, bare EOS) become
    # unreachable at the root. Contract enforcement only: spec E1* already sanctions
    # pinning <think> (logit_bias); Probe V is still emitted in-generation, stage
    # entropy still spans only generated tokens, no probe value is touched.
    prompt = prompt.rstrip() + "\n<think>\n"

    t0 = time.time()
    gen, retry_log = _generate_nonempty(client, prompt, **samp, max_tokens=max_tokens,
                                        seed=seed, degenerate=_degenerate_entangled,
                                        stop=[f"</{stop_tag}>"])
    latency_ms = int((time.time() - t0) * 1000)
    text = patch_unclosed(gen.text, stop_tag)
    tagged = parse_entangled(text, prefilled_think=True)
    action_exec, match_kind = choose_executable(tagged.action, text, admissible)

    probes = new_probes()
    if tagged.think_span:
        a, b = char_span_to_token_range(gen.tokens, *tagged.think_span)
        m = stage_metrics(gen.tokens, gen.logprobs, gen.top_logprobs, a, b)
        probes.update(thought_mte=m["mte"], thought_ppl=m["ppl"], thought_sp=m["sp"])
    if tagged.action_span:
        a, b = char_span_to_token_range(gen.tokens, *tagged.action_span)
        m = stage_metrics(gen.tokens, gen.logprobs, gen.top_logprobs, a, b)
        probes.update(action_mte=m["mte"], action_ppl=m["ppl"], action_sp=m["sp"],
                      action_nll=m["sp"])
    repair_raw = None
    if cfg.auq_suffix:
        # AUQ's in-generation <confidence> IS Probe V for the entangled architecture.
        u, expl, ok = auq_entangled(text)
        _, raw, _, anomaly = verbalized_confidence(text)
        continued = False
        # Guards (2026-07-20): never attach a repaired confidence to an EMPTY or
        # DEGENERATE generation — there is no in-generation step content for the value
        # to qualify, so the §2.4 continuation-identity argument does not hold
        # (first E0: 39 empty-gen repairs; 4bd6a08 smoke: repairs on instruction echo
        # inflated the repaired fraction to 63.5%).
        if (not ok and "<confidence>" not in text.lower()
                and gen.finish_reason != "length" and gen.text.strip()
                and not _degenerate_entangled(gen.text)):
            u, raw, ok, repair_raw = _repair_confidence(client, prompt, gen.text, samp, seed)
            continued = True   # explanation stays absent on repaired steps; logged as such
        probes.update(U_T_verbalized=u, U_T_verbalized_raw=raw, U_T_verbalized_parsed=ok,
                      U_T_verbalized_continued=continued, auq_explanation_text=expl)
        if anomaly:
            print(f"[loops] ANOMALY: multiple <confidence> tags in entangled generation")

    extra = {"generation": text, "prompt": prompt, "action_match": match_kind,
             "action_tag_ok": tagged.action_tag_ok, "think_tag_ok": tagged.think_tag_ok,
             "generation_retry": retry_log,
             "admissible_commands": list(admissible), "posthoc_raw": {},
             "verbalized_repair_raw": repair_raw}
    # post-hoc context: the generation WITHOUT the self-assessment — confidence value AND
    # explanation excised (the explanation is the assessment in prose; leaving it leaks
    # Probe V into the post-hoc reading). think/action kept; explanation logged in probes.
    stage_ctx = prompt + remove_self_assessment(text)
    _posthoc(client, prompts, cfg, seed, stage_ctx, stage_ctx, probes, extra)

    return {"thought": tagged.think or "", "probes": probes, "state_hash": _sha(prompt),
            "timing": {"latency_ms": latency_ms, "prompt_tokens": gen.prompt_tokens,
                       "completion_tokens": gen.completion_tokens},
            "extra": extra}, action_exec


# -- one step, decoupled ------------------------------------------------------

def _decoupled_step(client, prompts: Prompts, cfg: LoopConfig, samp, max_tokens, seed, *,
                    task, initial_obs, current_obs, history, admissible, t):
    shown = _window(history, cfg.history_window)
    # h["obs"] is the observation BEFORE h's action; the obs AFTER it is the next entry's
    # "before" (or current_obs for the last entry). First line anchors the initial scene.
    lines = [f"Observation: {shown[0]['obs'] if shown else initial_obs}"]
    for i, h in enumerate(shown):
        if cfg.history_include_thoughts and h["thought"]:
            lines.append(f"Thought: {h['thought']}")
        lines.append(f"Action: {h['action']}")
        obs_after = shown[i + 1]["obs"] if i + 1 < len(shown) else current_obs
        lines.append(f"Observation: {obs_after}")
    hist_str = "\n".join(lines)
    cmds = ", ".join(admissible)

    probes = new_probes()

    # -- thought call (v2: ends with <confidence> tag; v1 in the ablation arm) --
    thought_prompt = fill(prompts.thought if cfg.verbalized else prompts.thought_v1, {
        "DESCRIPTION": task, "HISTORY": hist_str, "AVAILABLE COMMANDS": cmds})
    t0 = time.time()
    gen_t, retry_t = _generate_nonempty(client, thought_prompt, **samp,
                                        max_tokens=max_tokens, seed=seed,
                                        stop=["\nObservation:", "\nAVAILABLE COMMANDS"])
    raw_thought = patch_unclosed(gen_t.text, "confidence") if cfg.verbalized else gen_t.text
    # STRIP the tag before anything goes downstream (no-feedback invariant): the action
    # call, history, and env must never see the verbalized value.
    thought = strip_confidence_tag(raw_thought).strip()
    repair_raw = {"thought": None, "action": None}
    if cfg.verbalized:
        u, raw, ok, anomaly = verbalized_confidence(raw_thought)
        continued = False
        if (not ok and "<confidence>" not in raw_thought.lower()
                and gen_t.finish_reason != "length" and gen_t.text.strip()):
            u, raw, ok, repair_raw["thought"] = _repair_confidence(
                client, thought_prompt, gen_t.text, samp, seed)
            continued = True
        probes.update(U_T_verbalized=u, U_T_verbalized_raw=raw, U_T_verbalized_parsed=ok,
                      U_T_verbalized_continued=continued)
        if anomaly:
            print("[loops] ANOMALY: multiple <confidence> tags in thought generation")

    # -- action call (v2: command line, then confidence tag on the next line) --
    action_prompt = fill(prompts.action if cfg.verbalized else prompts.action_v1, {
        "DESCRIPTION": task, "HISTORY": hist_str, "THOUGHTS": thought,
        "AVAILABLE COMMANDS": cmds})
    a_stop = ["</confidence>"] if cfg.verbalized else ["\n"]
    # degenerate check scoped to v1 only: v2's contract legitimately ends the line with a
    # '<confidence>' tag, so tag presence cannot signal degeneracy there.
    a_degenerate = None if cfg.verbalized else _degenerate_action_line
    gen_a, retry_a = _generate_nonempty(client, action_prompt, **samp,
                                        max_tokens=cfg.max_action_tokens,
                                        seed=seed, degenerate=a_degenerate, stop=a_stop)
    latency_ms = int((time.time() - t0) * 1000)
    raw_action = patch_unclosed(gen_a.text, "confidence") if cfg.verbalized else gen_a.text
    command_line = strip_confidence_tag(raw_action).strip().split("\n")[0]
    action_exec, match_kind = choose_executable(command_line, raw_action, admissible)
    if cfg.verbalized:
        u, raw, ok, anomaly = verbalized_confidence(raw_action)
        continued = False
        if (not ok and "<confidence>" not in raw_action.lower()
                and gen_a.finish_reason != "length" and gen_a.text.strip()):
            u, raw, ok, repair_raw["action"] = _repair_confidence(
                client, action_prompt, gen_a.text, samp, seed)
            continued = True
        probes.update(U_A_verbalized=u, U_A_verbalized_raw=raw, U_A_verbalized_parsed=ok,
                      U_A_verbalized_continued=continued)
        if anomaly:
            print("[loops] ANOMALY: multiple <confidence> tags in action generation")

    # -- stage entropy over PRE-TAG spans only (tag tokens must not contaminate the
    #    Cell C anchor comparison; Kim & Kang within-cell rule still applies on top) --
    t_end = gen_t.text.lower().find("<confidence>")
    a, b = char_span_to_token_range(gen_t.tokens, 0, t_end if t_end >= 0 else len(gen_t.text))
    m = stage_metrics(gen_t.tokens, gen_t.logprobs, gen_t.top_logprobs, a, b)
    probes.update(thought_mte=m["mte"], thought_ppl=m["ppl"], thought_sp=m["sp"])
    a_end = gen_a.text.lower().find("<confidence>")
    a, b = char_span_to_token_range(gen_a.tokens, 0, a_end if a_end >= 0 else len(gen_a.text))
    m = stage_metrics(gen_a.tokens, gen_a.logprobs, gen_a.top_logprobs, a, b)
    probes.update(action_mte=m["mte"], action_ppl=m["ppl"], action_sp=m["sp"],
                  action_nll=m["sp"])

    extra = {"thought_prompt": thought_prompt, "action_prompt": action_prompt,
             "thought_generation": gen_t.text, "action_generation": gen_a.text,
             "action_match": match_kind,
             "generation_retry": {"thought": retry_t, "action": retry_a},
             "admissible_commands": list(admissible), "posthoc_raw": {},
             "verbalized_repair_raw": repair_raw}
    # post-hoc contexts use the STRIPPED stage outputs — never the in-generation value
    _posthoc(client, prompts, cfg, seed,
             thought_prompt + thought, action_prompt + command_line, probes, extra)

    return {"thought": thought, "probes": probes, "state_hash": _sha(thought_prompt),
            "timing": {"latency_ms": latency_ms,
                       "prompt_tokens": gen_t.prompt_tokens + gen_a.prompt_tokens,
                       "completion_tokens": gen_t.completion_tokens + gen_a.completion_tokens},
            "extra": extra}, action_exec


def _posthoc(client, prompts: Prompts, cfg: LoopConfig, seed,
             thought_ctx: str, action_ctx: str, probes: dict, extra: dict) -> None:
    """Post-hoc self-evaluation comparators (P1 numeric on the thought stage, numeric on the
    action stage). CALLERS pass contexts with the in-generation confidence value already
    removed — the post-hoc reading must not be anchored by Probe V (invariant §5.1)."""
    if cfg.posthoc_numeric_thought:
        e = posthoc.numeric(client, thought_ctx, prompts.posthoc_numeric,
                            seed=seed, guided=cfg.posthoc_guided)
        probes.update(U_T_posthoc_numeric=e.value, U_T_posthoc_numeric_parsed=e.parsed)
        extra["posthoc_raw"]["numeric_thought"] = e.raw_text
    if cfg.posthoc_numeric_action:
        e = posthoc.numeric(client, action_ctx, prompts.posthoc_numeric_action,
                            seed=seed, guided=cfg.posthoc_guided)
        probes.update(U_A_posthoc_numeric=e.value, U_A_posthoc_numeric_parsed=e.parsed)
        extra["posthoc_raw"]["numeric_action"] = e.raw_text
