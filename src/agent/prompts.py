"""Prompt-file loading and placeholder filling.

Every prompt lives in prompts/ as a versioned text file (spec §0.2) and carries a trailing
provenance footer beginning with a line that starts with "# ---". The footer is documentation
(paper source, transcription notes) and is NEVER sent to the model — load_prompt() strips it.

Filling is literal string replacement, NOT str.format(): prompt bodies legitimately contain
braces (the judge prompt's JSON example) and one ReDAct placeholder contains a space
("{AVAILABLE COMMANDS}"), both of which break format(). fill() also enforces that every
requested placeholder actually existed in the template — a silently-unfilled prompt is a
corrupted experiment, not a warning.
"""
from __future__ import annotations

import os

_FOOTER_MARK = "# ---"


def load_prompt(path: str) -> str:
    """Read a prompt file and strip the provenance footer (first line starting '# ---' onward)."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        if line.startswith(_FOOTER_MARK):
            lines = lines[:i]
            break
    return "\n".join(lines).rstrip() + "\n"


def fill(template: str, mapping: dict[str, str]) -> str:
    """Replace every '{key}' in template with mapping[key], literally.

    Raises ValueError if a requested key has no placeholder in the template (typo'd prompt
    file or wrong template — fail loudly, never generate from a half-filled prompt).
    """
    out = template
    for key, value in mapping.items():
        ph = "{" + key + "}"
        if ph not in out:
            raise ValueError(f"placeholder {ph!r} not found in template")
        out = out.replace(ph, str(value))
    return out


def prompts_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "prompts")


def prompt_path(name: str) -> str:
    return os.path.join(prompts_dir(), name)
