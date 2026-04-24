"""
Syllable Rhythm Analyzer – Turkish rap line rhythm consistency checker.

Counts syllables via Turkish vowel counting, then validates that
at least 60% of lines fall within ±3 syllables of the mean.
Target range for rap lines: 8–14 syllables.

Pure Python.  No external dependencies.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple

try:
    from app.bpm_profile import get_bpm_profile
except ImportError:
    get_bpm_profile = None

logger = logging.getLogger(__name__)

# Turkish vowels (uppercase + lowercase)
_TR_VOWELS = set("aeıioöuüAEIİOÖUÜ")

# Ideal syllable range for rap lines
_MIN_SYLLABLES = 8
_MAX_SYLLABLES = 14

# Rhythm consistency threshold
_RHYTHM_THRESHOLD = 0.60  # 60% of lines must be within ±3 of mean
_TOLERANCE = 3            # ±3 syllables


# ── Syllable counter ────────────────────────────────────────────────────

def count_syllables(text: str) -> int:
    """
    Count syllables in a Turkish text by counting vowels.

    This is a simple but effective heuristic for Turkish, where each
    syllable contains exactly one vowel.

    Parameters
    ----------
    text : str – a single line of text

    Returns
    -------
    int – estimated syllable count

    Examples
    --------
    >>> count_syllables("Gururum seni affetmez")
    8
    >>> count_syllables("Ey Hako")
    3
    """
    return sum(1 for ch in text if ch in _TR_VOWELS)


def count_syllables_per_line(lines: List[str]) -> List[int]:
    """
    Count syllables for each line in a list.

    Skips section tags (lines starting with '[') and blank lines.

    Returns
    -------
    list[int] – syllable count for each lyric line
    """
    counts: List[int] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("["):
            continue
        counts.append(count_syllables(stripped))
    return counts


# ── Rhythm analyzer ─────────────────────────────────────────────────────

def analyze_rhythm(lines: List[str], bpm: int = 120) -> Dict[str, Any]:
    """
    Analyze the rhythm consistency of lyric lines based on BPM.

    Algorithm
    ---------
    1. Count syllables per line.
    2. Get target syllable range from BPM profile.
    3. Check what fraction of lines are within the target range.
    4. If ≥40% are within bounds (i.e. not 60% outside), rhythm_valid = True.
       (User required: Eğer satırların %60'ı aralığın dışındaysa rhythm_invalid)

    Parameters
    ----------
    lines : list[str] – lyric lines (may include section tags)
    bpm : int – beats per minute, used for target range

    Returns
    -------
    dict with keys:
        rhythm_valid     – bool
        message          – str
        avg_syllables    – float
        rhythm_score     – float (fraction of lines inside range)
        syllable_counts  – list[int]
        in_range_count   – int
        total_lines      – int
    """
    counts = count_syllables_per_line(lines)

    if len(counts) < 4:
        return {
            "rhythm_valid": True,
            "message": "too few lines to evaluate rhythm",
            "avg_syllables": 0.0,
            "rhythm_score": 1.0,
            "syllable_counts": counts,
            "in_range_count": 0,
            "total_lines": len(counts),
        }

    avg = sum(counts) / len(counts)

    # Get target range for BPM
    if get_bpm_profile is not None:
        profile = get_bpm_profile(bpm)
        syl_min, syl_max = profile["syllable_range"]
    else:
        syl_min, syl_max = (_MIN_SYLLABLES, _MAX_SYLLABLES)

    # Lines within target BPM range
    in_range = sum(1 for c in counts if syl_min <= c <= syl_max)
    rhythm_score = in_range / len(counts)
    
    # User rule: if 60% are outside range, it is invalid (meaning less than 40% are inside range) -> score < 0.40
    rhythm_valid = rhythm_score >= 0.40

    pct = round(rhythm_score * 100)

    if rhythm_valid:
        msg = f"rhythm OK: {pct}% within {syl_min}-{syl_max} range for {bpm} BPM (avg={avg:.1f})"
        logger.info("✅ %s", msg)
    else:
        msg = f"rhythm irregular: {pct}% within {syl_min}-{syl_max} range for {bpm} BPM (avg={avg:.1f})"
        logger.warning("⚠️ %s", msg)

    return {
        "rhythm_valid": rhythm_valid,
        "message": msg,
        "avg_syllables": round(avg, 1),
        "rhythm_score": round(rhythm_score, 3),
        "syllable_counts": counts,
        "in_range_count": in_range,
        "total_lines": len(counts),
    }


def analyze_rhythm_from_text(text: str, bpm: int = 120) -> Dict[str, Any]:
    """
    Convenience wrapper: accepts full lyrics text, splits into lines,
    and analyzes rhythm against BPM.
    """
    lines = text.strip().splitlines()
    return analyze_rhythm(lines, bpm=bpm)
