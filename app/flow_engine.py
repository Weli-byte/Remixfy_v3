"""
Flow Engine – generates a structural flow skeleton (rhyme key + cadence map)
before any lyrics are written.  No lyrics produced here.
"""

from __future__ import annotations

import random
from typing import Any


# ── Rhyme ending pools ───────────────────────────────────────────────────

_HARD_ENDINGS = [
    "-arım", "-urum", "-anda", "-ıyor", "-acak",
    "-eder", "-aldım", "-oldum", "-ırım", "-ersin",
]

_SOFT_ENDINGS = [
    "-ımda", "-imde", "-inde", "-ken", "-ıyla",
    "-ince", "-sine", "-gibi", "-üzre", "-mışım",
]

_NEUTRAL_ENDINGS = [
    "-orum", "-eler", "-alar", "-inde", "-ıdır",
    "-enir", "-ülür", "-arak", "-erek", "-iken",
]

_AGGRESSIVE_ENDINGS = [
    "-arım", "-urum", "-anda", "-acak", "-ırım",
    "-aldım", "-oldum", "-eder", "-düm", "-tım",
]

_MELODIC_ENDINGS = [
    "-ımda", "-imde", "-ince", "-gibi", "-sine",
    "-üzre", "-mışım", "-ıyla", "-ken", "-miş",
]


# ── Ego ratio parser ────────────────────────────────────────────────────

def _parse_ego(ratio: str) -> int:
    """Extract ego percentage from 'XX/YY' format. Returns ego value."""
    try:
        parts = ratio.split("/")
        return int(parts[0])
    except (ValueError, IndexError):
        return 50


# ── Rhyme key selection ──────────────────────────────────────────────────

def _select_rhyme_key(ego: int, emotion: int) -> str:
    """
    Pick a rhyme ending based on ego dominance and emotion level.

    Priority order:
    1. Emotion 8–10 → aggressive pool
    2. Emotion 1–4  → melodic pool
    3. Ego > 60     → hard pool
    4. Ego < 40     → soft pool
    5. Otherwise    → neutral pool
    """
    if emotion >= 8:
        pool = _AGGRESSIVE_ENDINGS
    elif emotion <= 4:
        pool = _MELODIC_ENDINGS
    elif ego > 60:
        pool = _HARD_ENDINGS
    elif ego < 40:
        pool = _SOFT_ENDINGS
    else:
        pool = _NEUTRAL_ENDINGS

    return random.choice(pool)


# ── Cadence generation ───────────────────────────────────────────────────

def _generate_cadence(line_count: int, base_min: int = 8, base_max: int = 11) -> list[int]:
    """
    Generate a natural-feeling word count array for a section.

    Rules:
    - Values range between base_min and base_max.
    - No three consecutive identical values.
    - Pattern varies naturally.
    """
    counts: list[int] = []
    for _ in range(line_count):
        val = random.randint(base_min, base_max)

        # Prevent 3 identical in a row
        if len(counts) >= 2 and counts[-1] == counts[-2] == val:
            options = [v for v in range(base_min, base_max + 1) if v != val]
            val = random.choice(options)

        counts.append(val)

    return counts


def _ensure_unique_patterns(
    sections: dict[str, list[int]],
) -> dict[str, list[int]]:
    """
    Ensure no two sections share an identical cadence pattern.
    If collision detected, perturb one value in the duplicate.
    """
    seen: list[tuple[int, ...]] = []
    result: dict[str, list[int]] = {}

    for name, pattern in sections.items():
        t = tuple(pattern)
        while t in seen:
            # Perturb a random position
            idx = random.randint(0, len(pattern) - 1)
            current = pattern[idx]
            options = [v for v in range(8, 12) if v != current]
            pattern[idx] = random.choice(options)
            t = tuple(pattern)
        seen.append(t)
        result[name] = pattern

    return result


# ── Public API ───────────────────────────────────────────────────────────

def generate_flow_skeleton(
    artist_dna: dict[str, Any],
    emotion_level: int,
) -> dict[str, Any]:
    """
    Generate a pre-lyric flow skeleton containing rhyme key and
    per-section cadence maps.

    Parameters
    ----------
    artist_dna : dict
        The ``dna`` object from an artist profile.
    emotion_level : int
        Emotion intensity (1–10).

    Returns
    -------
    dict
        {
            "rhyme_key": str,
            "structure": {
                "VERSE 1": [int, ...],   # 6 word counts
                "CHORUS":  [int, ...],   # 4 word counts
                "VERSE 2": [int, ...],   # 4 word counts
            }
        }
    """
    ego = _parse_ego(artist_dna.get("ego_vulnerability_ratio", "50/50"))
    emotion = max(1, min(10, emotion_level))

    # Select rhyme key
    rhyme_key = _select_rhyme_key(ego, emotion)

    # Generate cadence per section
    raw_structure = {
        "VERSE 1": _generate_cadence(6),
        "CHORUS": _generate_cadence(4),
        "VERSE 2": _generate_cadence(4),
    }

    # Ensure no duplicate patterns across sections
    structure = _ensure_unique_patterns(raw_structure)

    return {
        "rhyme_key": rhyme_key,
        "structure": structure,
    }
