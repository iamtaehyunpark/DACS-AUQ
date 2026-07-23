"""Environment-derived transition tags for HotpotQA ReAct actions."""
from __future__ import annotations

import re


def tau_dict(action: str):
    action = (action or "").strip().lower()
    if re.fullmatch(r"(search|lookup)\[[^\r\n]*\]", action):
        return {"I": 1, "W": 0, "R": 1, "C": "free"}
    if re.fullmatch(r"finish\[[^\r\n]*\]", action):
        # Finish commits the answer and irreversibly terminates this episode.
        return {"I": 0, "W": 1, "R": 0, "C": "costly"}
    return None


if __name__ == "__main__":
    assert tau_dict("Search[Colorado orogeny]") == {"I": 1, "W": 0, "R": 1, "C": "free"}
    assert tau_dict("Lookup[eastern sector]") == {"I": 1, "W": 0, "R": 1, "C": "free"}
    assert tau_dict("Finish[Richard Nixon]") == {"I": 0, "W": 1, "R": 0, "C": "costly"}
    for invalid in ("", "Search", "Think[maybe]", "ACTION: Search[x]", "Finish[x]\nextra"):
        assert tau_dict(invalid) is None
    print("hotpot_tau_map: action-family and invalid-action tests pass")

