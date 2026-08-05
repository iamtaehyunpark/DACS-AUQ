"""Shared machinery for the UNCERTAINTY-FEEDBACK intervention runs.

Unlike every other probe in this repo, this is an INTERVENTION, not a post-hoc read: the P(True)
uncertainty of step t is written back into the agent's own context before step t+1, so the agent
can (in principle) react to having been unsure. Originally-FAILED episodes are re-run under three
arms:

    control   plain re-run. Nothing injected. Measures the retry baseline — some failed episodes
              succeed on a second attempt at temperature 0.7 purely by chance, and any recovery
              claimed for the feedback arms has to beat that.
    prod      the production P(True) prompt measures step t (task + history + reasoning + action)
    c5        the C5 pre-hindsight prompt measures step t (same, PLUS the observation the action
              produced). Causally legitimate here: by the time the annotation is shown at step
              t+1, the outcome of step t is already known.

Injected format (CUMULATIVE — every history turn carries its own score):

    > take mug 2 from cabinet 1
    Nothing happens.
    [uncertainty 0.78 — HIGHLY UNCERTAIN about this action]

The warning label fires when U > threshold, where the threshold is the ORIGINAL MEAN UNCERTAINTY
OF JUDGE-INCORRECT STEPS, measured per (domain, arm) so the two feedback arms warn at comparable
RATES rather than differing mainly in how often they shout:

    alfworld/prod  0.491   PTRUE_CTXRULE_REPORT n=300, C3/R0 mean U on incorrect steps
    alfworld/c5    0.684   PTRUE_CTXRULE_REPORT n=300, C5/R0 mean U on incorrect steps
    hotpot/prod    0.524   runs/hotpot_500, ptrue stage=action, unanimous-incorrect steps
    hotpot/c5      set by uq_feedback_calibrate.py (same definition, C5 prompt)

TWO HISTORIES ARE KEPT DELIBERATELY. The agent sees the annotated history; every PROBE call sees
the CLEAN one. If the probe saw its own annotations, U would drift with the accumulated text (the
horizon sweep showed U inflates with context volume regardless of content) and the fixed threshold
would stop meaning anything.
"""
from __future__ import annotations

import os

import probes

ARMS = ("control", "prod", "c5")

# (domain, arm) -> mean U of judge-incorrect steps. Override with UQFB_THRESH_<DOMAIN>_<ARM>.
THRESHOLDS = {
    ("alfworld", "prod"): 0.491,
    ("alfworld", "c5"): 0.684,
    ("hotpot", "prod"): 0.524,
    ("hotpot", "c5"): 0.635,        # provisional until uq_feedback_calibrate.py runs
}


def threshold(domain, arm):
    env = os.environ.get("UQFB_THRESH_%s_%s" % (domain.upper(), arm.upper()))
    if env:
        return float(env)
    return THRESHOLDS[(domain, arm)]


# --------------------------------------------------------------------------- probe prompts

def probe_prompt(domain, arm, *, task, history, commands, thought, action, obs):
    """The prompt that measures step t. `history` MUST be the clean (unannotated) history the
    agent had BEFORE taking this action — the same context the frozen corpus was measured in,
    which is what makes the calibrated threshold applicable."""
    if domain == "hotpot":
        base = probes.prompt_hotpot_ptrue_action(task, history, commands, thought, action)
    else:
        base = probes.prompt_ptrue_action(task, history, commands, thought, action)
    if arm != "c5":
        return base
    # splice the outcome in just before the question, mirroring ptrue_context_rule_probe's C5
    head, sep, question = base.rpartition("\n\n")
    return "%s\nRESULT OF THE PROPOSED ACTION:\n%s\n%s%s" % (head, obs, sep, question)


def measure_u(client, cfg, domain, arm, *, task, history, commands, thought, action, obs, seed):
    """One single-token P(True) call. Returns (U, parse_ok, prompt, record). U is NEVER imputed:
    an unparseable answer yields U=None and that step simply carries no annotation."""
    prompt = probe_prompt(domain, arm, task=task, history=history, commands=commands,
                          thought=thought, action=action, obs=obs)
    _c, rec = probes._call(client, cfg, prompt, max_tokens=4, seed=seed)
    top = probes._first_nonws_top(rec["gen_logprobs"])
    _p_yes, _p_no, _conf, U, ok = probes.yesno_mass(top)
    return (U if ok else None), ok, prompt, rec


# --------------------------------------------------------------------------- annotation

WARN = "HIGHLY UNCERTAIN about this action"


def annotation_line(U, thr):
    """Text appended to a history turn. Score always shown; the warning label only when the step
    is at least as uncertain as the average step the judges called incorrect."""
    if U is None:
        return ""
    return ("\n[uncertainty %.2f — %s]" % (U, WARN)) if U > thr else ("\n[uncertainty %.2f]" % U)
