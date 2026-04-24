"""
Rhyme Validator – Checks the rhyme density of generated lyrics.

Pure Python.  Compares the last 2 characters of each line's final word
to find pairwise rhyme matches.  If ≥40 % of lines share an ending
with at least one other line, the result is VALID.
"""

from __future__ import annotations

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

_MIN_RHYME_RATIO = 0.40  # 40 % threshold


# ── Helpers ──────────────────────────────────────────────────────────────

def _extract_last_word(line: str) -> str:
    """Return the last word of a line, stripped of trailing punctuation."""
    words = line.strip().split()
    if not words:
        return ""
    return re.sub(r"[^\w]", "", words[-1]).lower()


def _ending(word: str, n: int = 2) -> str:
    """Return the last *n* characters of a cleaned word."""
    return word[-n:] if len(word) >= n else word


# ── Public API ───────────────────────────────────────────────────────────

def validate_rhyme_scheme(text: str) -> Tuple[bool, str]:
    """
    Validate the rhyme density of generated lyrics.

    Algorithm
    ---------
    1. Extract the last word of every lyric line (skip section tags).
    2. Take the last 2 characters of each word.
    3. For every line, check if at least one other line shares the same
       2-character ending.
    4. If ≥40 % of lines have a rhyme partner → VALID.

    Returns
    -------
    (True,  "rhyme density OK: XX%")
    (False, "rhyme density too low: XX%")
    """
    lines = [
        l.strip()
        for l in text.strip().splitlines()
        if l.strip() and not l.strip().upper().startswith("[")
    ]

    if len(lines) < 4:
        return True, "too few lines to evaluate"

    endings: list[str] = []
    for line in lines:
        word = _extract_last_word(line)
        endings.append(_ending(word))

    # Count how many lines have at least one rhyme partner
    rhymed = 0
    for i, end_i in enumerate(endings):
        if not end_i:
            continue
        for j, end_j in enumerate(endings):
            if i != j and end_i == end_j:
                rhymed += 1
                break  # one partner is enough

    ratio = rhymed / len(endings) if endings else 0.0
    pct = round(ratio * 100)

    if ratio >= _MIN_RHYME_RATIO:
        logger.info("✅ Rhyme validation passed: %d%%", pct)
        return True, f"rhyme density OK: {pct}%"
    else:
        logger.warning("⚠️ Rhyme density too low: %d%%", pct)
        return False, f"rhyme density too low: {pct}%"
