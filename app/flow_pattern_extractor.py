"""
Flow Pattern Extractor v2 – Advanced rap flow analyzer.

Learns the artist's real rap flow behaviors from their corpus.
Analyzes line break styles, punchline positions, and detailed ratios.

Mevcut modülleri (vector retrieval, vb.) bozmadan sisteme eklenmek üzere tasarlandı.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Try to reuse the corpus loading function so we don't open the file manually
try:
    from app.flow_analyzer import get_corpus_for_artist
except ImportError:
    # Fallback to empty if not found, though we know it's there
    def get_corpus_for_artist(artist_name: str) -> List[str]:
        return []


def extract_flow_patterns(corpus_lines: List[str]) -> Dict[str, float]:
    """
    Extract basic word and punctuation flow metrics from corpus lines.
    """
    if not corpus_lines:
        return {
            "average_line_length": 0.0,
            "short_line_ratio": 0.0,
            "long_line_ratio": 0.0,
            "question_ratio": 0.0,
            "punctuation_pause_ratio": 0.0,
        }

    total_words = 0
    short_lines = 0
    long_lines = 0
    questions = 0
    pauses = 0

    for line in corpus_lines:
        words = line.strip().split()
        word_count = len(words)
        total_words += word_count

        if word_count <= 5:
            short_lines += 1
        elif word_count >= 10:
            long_lines += 1

        if "?" in line:
            questions += 1
        
        # Punctuation pauses (commas, periods, dashes)
        pauses += len(re.findall(r"[,.\-]", line))

    total = len(corpus_lines)
    return {
        "average_line_length": round(total_words / total, 2),
        "short_line_ratio": round(short_lines / total, 2),
        "long_line_ratio": round(long_lines / total, 2),
        "question_ratio": round(questions / total, 2),
        "punctuation_pause_ratio": round(pauses / total, 2),
    }


def detect_line_break_style(lines: List[str]) -> str:
    """
    Detect the style of line breaks:
    - staccato (very short, lots of pauses)
    - narrative (long, few pauses)
    - balanced
    """
    metrics = extract_flow_patterns(lines)
    avg_words = metrics["average_line_length"]
    short_ratio = metrics["short_line_ratio"]
    pauses = metrics["punctuation_pause_ratio"]

    # Simple heuristic
    if short_ratio > 0.6 or (avg_words < 6.0 and pauses > 0.5):
        return "staccato"
    elif avg_words > 9.0 and pauses < 0.3:
        return "narrative"
    else:
        return "balanced"


def detect_punchline_positions(lines: List[str]) -> List[int]:
    """
    Analyze which line indices (in chunks of 4 or 8) usually carry the punchline.
    We detect "punchlines" by looking for exclamations, questions, or unusually short/long lines
    towards the end of a typical 4-bar or 8-bar schema.
    Returns something like [4, 8].
    """
    position_scores = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    
    # We treat every 8 lines as a block.
    # Lines are 1-indexed in the block.
    block_size = 8
    
    valid_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith("[")]
    
    blocks = [valid_lines[i:i + block_size] for i in range(0, len(valid_lines), block_size)]
    
    for block in blocks:
        for i, line in enumerate(block):
            pos = i + 1
            # Give points to lines that look like punchlines
            points = 0
            if "!" in line or "?" in line:
                points += 2
            
            # Very strong rhyme endings or distinct flow shifts could be punchlines.
            # We add a generic base point for ending positions traditionally used in rap
            if pos in [4, 8]:
                points += 1
                
            position_scores[pos] += points

    # Find the top 2 positions that scored the highest
    sorted_pos = sorted(position_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Extract top 2 positions that have some score
    best = [pos for pos, score in sorted_pos if score > 0][:2]
    
    if not best:
        # Fallback rap default
        return [4, 8]
        
    return sorted(best)


def build_flow_pattern_profile(artist_name: str) -> Dict[str, Any]:
    """
    Builds the full flow profile from corpus.
    """
    corpus = get_corpus_for_artist(artist_name)
    if not corpus:
        return {
            "avg_line_length": 5.0,
            "short_ratio": 0.0,
            "pause_style": "balanced",
            "break_style": "balanced",
            "punchline_positions": [4, 8]
        }
        
    metrics = extract_flow_patterns(corpus)
    break_style = detect_line_break_style(corpus)
    punchlines = detect_punchline_positions(corpus)
    
    # Define pause_style to be compatible with requested output format
    pause_style = "staccato" if break_style == "staccato" else ("medium" if break_style == "balanced" else "long")

    profile = {
        "avg_line_length": metrics["average_line_length"],
        "short_ratio": metrics["short_line_ratio"],
        "pause_style": pause_style,
        "break_style": break_style,
        "punchline_positions": punchlines
    }
    
    logger.info("🧠 Flow Pattern Profile generated: %s", profile)
    return profile
