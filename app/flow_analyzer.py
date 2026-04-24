"""
Flow Analyzer – Extracts flow patterns from an artist's lyrics_corpus.

Pure Python, no external API calls.  Returns statistical metrics that
describe the artist's writing rhythm and style.

These metrics are injected into the prompt so the LLM can mimic the
artist's natural cadence, line length tendencies, and pause patterns.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_ARTISTS_PATH = Path(__file__).resolve().parent.parent / "data" / "artists.json"

# ── Default (empty) profile returned when corpus is unavailable ──────────
_EMPTY_PROFILE: Dict[str, Any] = {
    "avg_words": 0.0,
    "short_ratio": 0.0,
    "question_ratio": 0.0,
    "exclamation_ratio": 0.0,
    "rhyme_endings": [],
    "pause_style": "medium",
}


# ── Helpers ──────────────────────────────────────────────────────────────

def _load_corpus(artist_name: str) -> List[str]:
    """Load lyrics_corpus lines for a given artist."""
    try:
        with open(_ARTISTS_PATH, "r", encoding="utf-8") as f:
            data: list[dict] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Could not load artists.json")
        return []

    for artist in data:
        if artist.get("name", "").lower() == artist_name.lower():
            return artist.get("lyrics_corpus", [])
    return []


def _extract_ending(word: str, n: int = 2) -> str:
    """Return the last *n* characters of a word (lowered, stripped)."""
    clean = re.sub(r"[^\w]", "", word.lower())
    return clean[-n:] if len(clean) >= n else clean


# ── Public API ───────────────────────────────────────────────────────────

def analyze_flow_patterns(artist_name: str) -> Dict[str, Any]:
    """
    Analyse an artist's corpus and return flow metrics.

    Returns
    -------
    dict with keys:
        avg_words          – float, average words per line
        short_ratio        – float, ratio of lines with ≤5 words
        question_ratio     – float, ratio of lines ending with '?'
        exclamation_ratio  – float, ratio of lines ending with '!'
        rhyme_endings      – list[str], top-5 most common 2-char endings
        pause_style        – str, dominant line-length category
                             ("short" / "medium" / "long")
    """
    corpus = _load_corpus(artist_name)

    if not corpus:
        logger.info("No corpus for '%s' – returning empty flow profile.", artist_name)
        return dict(_EMPTY_PROFILE)

    total = len(corpus)
    word_counts: List[int] = []
    questions = 0
    exclamations = 0
    short_lines = 0   # ≤5 words
    medium_lines = 0  # 6-9 words
    long_lines = 0    # ≥10 words
    ending_counter: Counter[str] = Counter()

    for line in corpus:
        stripped = line.strip()
        if not stripped:
            continue

        words = stripped.split()
        wc = len(words)
        word_counts.append(wc)

        # Length buckets
        if wc <= 5:
            short_lines += 1
        elif wc <= 9:
            medium_lines += 1
        else:
            long_lines += 1

        # Punctuation ratios
        if stripped.endswith("?"):
            questions += 1
        if stripped.endswith("!"):
            exclamations += 1

        # Rhyme ending (last word, last 2 chars)
        last_word = words[-1]
        ending = _extract_ending(last_word, 2)
        if ending:
            ending_counter[ending] += 1

    avg_words = round(sum(word_counts) / len(word_counts), 2) if word_counts else 0.0
    short_ratio = round(short_lines / total, 2)
    question_ratio = round(questions / total, 2)
    exclamation_ratio = round(exclamations / total, 2)

    # Top-5 rhyme endings formatted as "-XX"
    rhyme_endings = [f"-{ending}" for ending, _ in ending_counter.most_common(5)]

    # Dominant pause style
    buckets = {"short": short_lines, "medium": medium_lines, "long": long_lines}
    pause_style = max(buckets, key=buckets.get)  # type: ignore[arg-type]

    profile: Dict[str, Any] = {
        "avg_words": avg_words,
        "short_ratio": short_ratio,
        "question_ratio": question_ratio,
        "exclamation_ratio": exclamation_ratio,
        "rhyme_endings": rhyme_endings,
        "pause_style": pause_style,
    }

    logger.info(
        "Flow profile for '%s': avg=%.1f, short=%.0f%%, questions=%.0f%%, pause=%s",
        artist_name,
        avg_words,
        short_ratio * 100,
        question_ratio * 100,
        pause_style,
    )

    return profile


def get_corpus_for_artist(artist_name: str) -> List[str]:
    """
    Public wrapper around _load_corpus.

    Useful for other modules (e.g. hook_generator) that need raw corpus
    lines without duplicating the JSON loading logic.
    """
    return _load_corpus(artist_name)
