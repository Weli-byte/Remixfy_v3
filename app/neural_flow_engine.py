"""
Neural Flow Engine - Analyzes and models rap flow patterns from artist corpus.

Computes syllable averages, pause patterns, and dominant bar-syllable groupings
to produce a comprehensive flow profile used to guide LLM lyric generation.
"""

import logging
import re
from collections import Counter
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_TURKISH_VOWELS = set("aeıioöuüAEIİOÖUÜ")


def count_syllables(line: str) -> int:
    """
    Counts syllables in a line using Turkish vowel counting.
    Every vowel character (aeıioöuü) counts as one syllable.
    """
    return sum(1 for ch in line if ch in _TURKISH_VOWELS)


def _detect_dominant_pattern(syllable_counts: List[int]) -> str:
    """
    Detects the most common bar-grouping pattern based on syllable counts.
    Groups counts into 3 segments to produce a pattern like "4-3-4".
    """
    if not syllable_counts:
        return "4-3-4"
    
    avg = sum(syllable_counts) / len(syllable_counts)

    # Classify each line as short / mid / long relative to average
    def bucket(n: float) -> int:
        if n < avg * 0.8:
            return 3
        elif n > avg * 1.2:
            return 5
        else:
            return 4

    buckets = [bucket(s) for s in syllable_counts]
    
    # Return the 3-part pattern of most representative thirds
    third = max(1, len(buckets) // 3)
    p1 = Counter(buckets[:third]).most_common(1)[0][0]
    p2 = Counter(buckets[third:2*third]).most_common(1)[0][0]
    p3 = Counter(buckets[2*third:]).most_common(1)[0][0]
    
    return f"{p1}-{p2}-{p3}"


def detect_pause_patterns(lines: List[str]) -> float:
    """
    Estimates the pause ratio from comma/period/question marks in lines.
    pause_ratio = lines_with_pauses / total_lines
    """
    total = 0
    paused = 0
    
    pause_markers = re.compile(r"[,\.!\?;…–—]")
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        total += 1
        if pause_markers.search(cleaned):
            paused += 1
            
    return round(paused / total, 2) if total > 0 else 0.0


def analyze_flow_patterns_from_corpus(lines: List[str]) -> Dict:
    """
    Core flow analysis given a list of lines.
    Returns avg_syllables and pause_ratio.
    """
    syllable_counts = []
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        syllable_counts.append(count_syllables(cleaned))
        
    if not syllable_counts:
        return {"avg_syllables": 11, "pause_ratio": 0.30, "dominant_pattern": "4-3-4"}
        
    avg = round(sum(syllable_counts) / len(syllable_counts), 1)
    pause_ratio = detect_pause_patterns(lines)
    dominant = _detect_dominant_pattern(syllable_counts)
    
    return {
        "avg_syllables": avg,
        "pause_ratio": pause_ratio,
        "dominant_pattern": dominant
    }


def build_flow_profile(artist_name: str) -> Dict:
    """
    Builds a full flow profile for an artist from their lyrics corpus.

    Output:
        {
          "avg_syllables": 11,
          "pause_ratio": 0.35,
          "dominant_pattern": "4-3-4"
        }
    """
    try:
        from app.flow_analyzer import get_corpus_for_artist
        lines = get_corpus_for_artist(artist_name)
    except ImportError:
        logger.warning("Could not import get_corpus_for_artist; using fallback values.")
        lines = []

    if not lines:
        logger.info("No corpus lines found for '%s' — using defaults.", artist_name)
        return {"avg_syllables": 11, "pause_ratio": 0.30, "dominant_pattern": "4-3-4"}
    
    profile = analyze_flow_patterns_from_corpus(lines)
    logger.info(
        "Neural Flow Profile for '%s': avg=%.1f, pause=%.0f%%, pattern=%s",
        artist_name, profile["avg_syllables"],
        profile["pause_ratio"] * 100,
        profile["dominant_pattern"]
    )
    return profile


def format_flow_profile_block(profile: Dict) -> str:
    """
    Formats the flow profile into a prompt-ready text block.
    """
    avg = profile.get("avg_syllables", 11)
    pause_pct = int(profile.get("pause_ratio", 0.30) * 100)
    pattern = profile.get("dominant_pattern", "4-3-4")
    
    return (
        "NEURAL FLOW PROFİLİ:\n"
        f"Ortalama hece sayısı: {avg}\n"
        f"Durak oranı: %{pause_pct}\n"
        f"Dominant ritim kalıbı: {pattern}\n"
        "\n"
        "Talimat: Satırları bu ritim kalıbına yakın yaz."
    )
