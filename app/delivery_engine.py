"""
Delivery Simulation Engine - Models the performance delivery style of an artist.

Analyzes pause patterns, breath intervals, and derives a delivery style
(e.g., 'controlled aggressive') from the artist's lyrics corpus.
This data guides the LLM to produce lyrics that feel performable and natural.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

_TURKISH_VOWELS = set("aeıioöuüAEIİOÖUÜ")
_PAUSE_MARKERS = re.compile(r"[,\.!\?;…–—]")


def _count_syllables(line: str) -> int:
    """Counts syllables in a line by counting Turkish vowels."""
    return sum(1 for ch in line if ch in _TURKISH_VOWELS)


def extract_pause_patterns(lines: List[str]) -> Dict[str, float]:
    """
    Measures how many lines contain pause markers (comma, period, etc.)
    and returns the pause_ratio (lines_with_pauses / total_lines).
    """
    total = 0
    paused = 0

    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        total += 1
        if _PAUSE_MARKERS.search(cleaned):
            paused += 1

    ratio = round(paused / total, 2) if total > 0 else 0.0
    return {"pause_ratio": ratio}


def detect_breath_points(line: str) -> Dict[str, int]:
    """
    Estimates natural breath intervals based on syllable count.
    Assumes a breath point every 8-12 syllables.
    """
    syllables = _count_syllables(line)

    # Clamp breath interval within 8–12 syllable range 
    if syllables <= 8:
        interval = 8
    elif syllables >= 12:
        interval = 12
    else:
        interval = syllables

    return {"breath_interval": interval}


def build_delivery_profile(artist_name: str) -> Dict:
    """
    Builds a delivery profile for the artist based on corpus analysis.

    Output:
        {
          "pause_ratio": 0.28,
          "breath_interval": 10,
          "delivery_style": "controlled aggressive"
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
            "pause_ratio": 0.28,
            "breath_interval": 10,
            "delivery_style": "controlled aggressive"
        }

    pause_data = extract_pause_patterns(lines)
    pause_ratio = pause_data["pause_ratio"]

    # Estimate avg breath interval from non-empty lines
    content_lines = [l.strip() for l in lines if l.strip()]
    if content_lines:
        intervals = [detect_breath_points(l)["breath_interval"] for l in content_lines]
        avg_interval = round(sum(intervals) / len(intervals))
    else:
        avg_interval = 10

    # Derive delivery style from pause ratio
    if pause_ratio > 0.40:
        delivery_style = "lyrical and measured"
    elif pause_ratio > 0.20:
        delivery_style = "controlled aggressive"
    else:
        delivery_style = "rapid fire"

    result = {
        "pause_ratio": pause_ratio,
        "breath_interval": avg_interval,
        "delivery_style": delivery_style
    }

    logger.info(
        "Delivery profile for '%s': pause=%.0f%%, breath_interval=%d, style=%s",
        artist_name, pause_ratio * 100, avg_interval, delivery_style
    )

    return result


def format_delivery_block(profile: Dict) -> str:
    """
    Formats the delivery profile into a prompt-ready text block.
    """
    pause_pct = int(profile.get("pause_ratio", 0.28) * 100)
    breath = profile.get("breath_interval", 10)
    style = profile.get("delivery_style", "controlled aggressive")

    return (
        "DELİVERY PROFİLİ:\n"
        f"Durak oranı: %{pause_pct}\n"
        f"Ortalama nefes aralığı: {breath} hece\n"
        f"Delivery stili: {style}\n"
        "\n"
        "Talimat:\n"
        "- Satırlarda doğal duraklar kullan.\n"
        "- Bazı satırları ortasında kır.\n"
        "- Performans hissi oluştur."
    )
