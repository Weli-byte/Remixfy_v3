"""
Audience Hook Engine - Analyzes and scores chorus hook quality.

Extracts hook patterns from chorus lines, measures repetition ratio,
simplicity, and rhyme density to compute an overall hook strength score.
The results guide the LLM to write memorable, repeatable chorus hooks.
"""

import logging
import re
from collections import Counter
from typing import Dict, List

logger = logging.getLogger(__name__)

_TURKISH_VOWELS = set("aeıioöuüAEIİOÖUÜ")
_PAUSE_MARKERS = re.compile(r"[,\.!\?;…–—]")


def extract_hook_patterns(lines: List[str]) -> Dict[str, str]:
    """
    Analyzes chorus lines to identify the dominant hook pattern type.
    Returns 'short slogan', 'repetitive chant', or 'lyrical hook'.
    """
    if not lines:
        return {"pattern": "short slogan"}

    # Average word count across non-empty lines
    word_counts = [len(l.split()) for l in lines if l.strip()]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

    if avg_words <= 4:
        pattern = "short slogan"
    elif avg_words <= 7:
        pattern = "repetitive chant"
    else:
        pattern = "lyrical hook"

    return {"pattern": pattern}


def analyze_hook_repeat(lines: List[str]) -> Dict[str, float]:
    """
    Calculates what ratio of lines are repeated in the chorus.
    repeat_ratio = (lines that appear more than once) / total_lines
    """
    valid_lines = [l.strip().lower() for l in lines if l.strip()]
    if not valid_lines:
        return {"repeat_ratio": 0.0}

    counter = Counter(valid_lines)
    repeated = sum(1 for line, count in counter.items() if count > 1)
    ratio = round(repeated / len(valid_lines), 2)
    return {"repeat_ratio": ratio}


def calculate_hook_simplicity(lines: List[str]) -> float:
    """
    Measures how 'simple/catchy' the hook is (0.0–1.0).
    Lines averaging 2–5 words get a high simplicity score.
    """
    valid_lines = [l.strip() for l in lines if l.strip()]
    if not valid_lines:
        return 0.5

    word_counts = [len(l.split()) for l in valid_lines]
    avg_words = sum(word_counts) / len(word_counts)

    # Peak simplicity at ~3 words, decays as lines get longer
    if 2 <= avg_words <= 5:
        simplicity = 1.0
    elif avg_words < 2:
        simplicity = 0.5
    elif avg_words <= 8:
        simplicity = max(0.0, 1.0 - (avg_words - 5) * 0.15)
    else:
        simplicity = 0.2

    return round(simplicity, 2)


def calculate_rhyme_score(lines: List[str]) -> float:
    """
    Quick end-rhyme density for the chorus lines (0.0–1.0).
    """
    valid_lines = [l.strip() for l in lines if l.strip()]
    if not valid_lines:
        return 0.0

    endings = Counter()
    for line in valid_lines:
        words = line.split()
        if words:
            last = words[-1].lower()
            if len(last) >= 3:
                endings[last[-3:]] += 1

    # Best rhyme group / total lines
    if endings:
        best = endings.most_common(1)[0][1]
        return round(min(1.0, best / len(valid_lines)), 2)
    return 0.0


def evaluate_hook_strength(lines: List[str]) -> Dict[str, float]:
    """
    Combines repeat_ratio + simplicity + rhyme_score into a hook_score.
    """
    repeat_ratio = analyze_hook_repeat(lines)["repeat_ratio"]
    simplicity = calculate_hook_simplicity(lines)
    rhyme_score = calculate_rhyme_score(lines)

    # Equal weight composite score
    hook_score = round((repeat_ratio + simplicity + rhyme_score) / 3.0, 2)

    logger.debug(
        "Hook Strength — repeat=%.2f, simplicity=%.2f, rhyme=%.2f, score=%.2f",
        repeat_ratio, simplicity, rhyme_score, hook_score
    )

    return {
        "hook_score": hook_score,
        "repeat_ratio": repeat_ratio,
        "simplicity": simplicity,
        "rhyme_score": rhyme_score
    }


def build_hook_profile(artist_name: str) -> Dict:
    """
    Builds a hook profile for the artist based on their corpus chorus-like lines.
    """
    try:
        from app.flow_analyzer import get_corpus_for_artist
        lines = get_corpus_for_artist(artist_name)
    except ImportError:
        lines = []

    # Use shorter lines as proxy for chorus content
    short_lines = [l for l in lines if l.strip() and len(l.split()) <= 6][:30]

    if not short_lines:
        return {"pattern": "short slogan", "hook_score": 0.65, "repeat_ratio": 0.40}

    pattern_data = extract_hook_patterns(short_lines)
    strength_data = evaluate_hook_strength(short_lines)

    profile = {
        "pattern": pattern_data["pattern"],
        **strength_data
    }

    logger.info(
        "Audience Hook Profile for '%s': pattern=%s, score=%.2f",
        artist_name, profile["pattern"], profile["hook_score"]
    )

    return profile
