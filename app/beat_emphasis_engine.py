"""
Beat Emphasis Engine - Analyzes syllable accent patterns for beat alignment.

Extracts the dominant accent/stress patterns from an artist's corpus,
identifies key beat positions (kick/snare beats 1 & 3 in 4/4 time),
and produces a profile that guides the LLM to place strong words on
rhythmically impactful beats.
"""

import logging
from collections import Counter
from typing import Dict, List

logger = logging.getLogger(__name__)

_TURKISH_VOWELS = set("aeıioöuüAEIİOÖUÜ")


def _count_syllables_in_word(word: str) -> int:
    """Returns the syllable count of a single word via vowel counting."""
    return sum(1 for ch in word if ch in _TURKISH_VOWELS)


def detect_word_stress(word: str) -> Dict[str, str]:
    """
    Determines stress position for a Turkish word.
    In Turkish, primary stress typically falls on the last syllable.
    """
    syl_count = _count_syllables_in_word(word)

    if syl_count == 0:
        return {"stress_position": "none", "syllables": 0}
    elif syl_count == 1:
        return {"stress_position": "only", "syllables": 1}
    else:
        # Turkish: stress is almost always on the final syllable
        return {"stress_position": "end", "syllables": syl_count}


def extract_accent_patterns(lines: List[str]) -> List[str]:
    """
    Extracts per-word syllable patterns from each line.
    Returns a list of pattern strings like '4-3', '3-4-3', etc.
    """
    patterns = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue

        words = cleaned.split()
        word_syllables = [_count_syllables_in_word(w) for w in words if _count_syllables_in_word(w) > 0]

        if len(word_syllables) >= 2:
            # Compress into a readable pattern by grouping into max 4 chunks
            pattern = "-".join(str(s) for s in word_syllables[:6])
            patterns.append(pattern)

    return patterns


def _compute_dominant_pattern(patterns: List[str]) -> str:
    """Returns the most common accent pattern from the list."""
    if not patterns:
        return "4-3-4"
    counter = Counter(patterns)
    return counter.most_common(1)[0][0]


def build_emphasis_profile(artist_name: str) -> Dict:
    """
    Builds a beat emphasis profile from the artist's lyrics corpus.

    Output:
        {
          "accent_positions": [1, 3],
          "dominant_pattern": "4-3-4",
          "stress_style": "end_stress"
        }
    """
    try:
        from app.flow_analyzer import get_corpus_for_artist
        lines = get_corpus_for_artist(artist_name)
    except ImportError:
        logger.warning("Could not import get_corpus_for_artist; using defaults.")
        lines = []

    if not lines:
        return {
            "accent_positions": [1, 3],
            "dominant_pattern": "4-3-4",
            "stress_style": "end_stress"
        }

    patterns = extract_accent_patterns(lines)
    dominant = _compute_dominant_pattern(patterns)

    logger.info(
        "Beat Emphasis Profile for '%s': pattern=%s, total_patterns=%d",
        artist_name, dominant, len(patterns)
    )

    return {
        "accent_positions": [1, 3],      # Beat 1 (kick) and Beat 3 (snare) in 4/4
        "dominant_pattern": dominant,
        "stress_style": "end_stress"     # Turkish phonological default
    }


def format_emphasis_block(profile: Dict) -> str:
    """
    Formats the beat emphasis profile into a prompt-ready text block.
    """
    pattern = profile.get("dominant_pattern", "4-3-4")
    positions = profile.get("accent_positions", [1, 3])
    pos_str = " ve ".join(f"beat {p}" for p in positions)

    return (
        "BEAT VURGU PROFİLİ:\n"
        f"Dominant ritim kalıbı: {pattern}\n"
        f"Vurgu noktaları: {pos_str}\n"
        "\n"
        "Talimat:\n"
        "- Kick vuruşlarında (beat 1) güçlü, ağır kelimeler kullan.\n"
        "- Snare vuruşlarında (beat 3) vurucu, çarpıcı kelimeler kullan."
    )
