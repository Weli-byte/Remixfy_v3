"""
Phonetic Rhyme Validator – Validates rap rhyme quality via last-3-char matching.

Pure Python.  Extracts the last 3 characters of each line's final word,
then checks if ≥40% of lines share a rhyme sound with at least one other line.
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

_MIN_RHYME_RATIO = 0.40  # 40% threshold


# ── Core functions ───────────────────────────────────────────────────────

def get_rhyme_sound(word: str) -> str:
    """
    Extract the rhyme sound of a word (last 3 characters, lowered).

    Strips trailing punctuation and parenthetical ad-libs before extraction.

    Examples
    --------
    >>> get_rhyme_sound("gururum")
    'rum'
    >>> get_rhyme_sound("affetmez!")
    'mez'
    >>> get_rhyme_sound("(ey)")
    'ey'
    """
    # Remove common ad-lib wrappers
    cleaned = re.sub(r"\(.*?\)", "", word).strip()
    # If nothing left after removing parens, use original
    if not cleaned:
        cleaned = re.sub(r"[^\w]", "", word)
    # Strip non-word chars
    cleaned = re.sub(r"[^\w]", "", cleaned).lower()
    if len(cleaned) < 2:
        return cleaned
    return cleaned[-3:] if len(cleaned) >= 3 else cleaned


def _extract_last_word(line: str) -> str:
    """Return the last meaningful word from a line."""
    stripped = line.strip()
    if not stripped:
        return ""

    # Remove trailing ad-libs like "(ey)" "(grr)" "(yeah)"
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", stripped).strip()
    if not cleaned:
        cleaned = stripped

    words = cleaned.split()
    if not words:
        return ""
    return words[-1]


def _is_section_tag(line: str) -> bool:
    """Check if a line is a section tag like [VERSE 1], [CHORUS], etc."""
    return bool(line.strip()) and line.strip().startswith("[") and line.strip().endswith("]")


# ── Validation ───────────────────────────────────────────────────────────

def validate_rhyme(lines: List[str]) -> Tuple[bool, str]:
    """
    Validate rhyme quality of lyric lines.

    Algorithm
    ---------
    1. Extract the last word of every lyric line (skip section tags / blanks).
    2. Get the rhyme sound (last 3 chars) of each word.
    3. For every line, check if at least one other line shares the same sound.
    4. If ≥40% of lines have a rhyme partner → VALID.

    Parameters
    ----------
    lines : list[str] – lyric lines (may include section tags)

    Returns
    -------
    (True,  "phonetic rhyme OK: XX%")
    (False, "phonetic rhyme too low: XX%")
    """
    lyric_lines = [
        l.strip() for l in lines
        if l.strip() and not _is_section_tag(l)
    ]

    if len(lyric_lines) < 4:
        return True, "too few lines to evaluate"

    sounds: List[str] = []
    for line in lyric_lines:
        word = _extract_last_word(line)
        sound = get_rhyme_sound(word)
        sounds.append(sound)

    # Count lines with at least one rhyme partner
    rhymed = 0
    for i, s_i in enumerate(sounds):
        if not s_i or len(s_i) < 2:
            continue
        for j, s_j in enumerate(sounds):
            if i != j and s_i == s_j:
                rhymed += 1
                break  # one partner is enough

    ratio = rhymed / len(sounds) if sounds else 0.0
    pct = round(ratio * 100)

    if ratio >= _MIN_RHYME_RATIO:
        logger.info("✅ Phonetic rhyme OK: %d%%", pct)
        return True, f"phonetic rhyme OK: {pct}%"
    else:
        logger.warning("⚠️ Phonetic rhyme too low: %d%%", pct)
        return False, f"phonetic rhyme too low: {pct}%"


def validate_rhyme_from_text(text: str) -> Tuple[bool, str]:
    """
    Convenience wrapper: accepts full lyrics text, splits into lines,
    and validates rhyme.
    """
    lines = text.strip().splitlines()
    return validate_rhyme(lines)
