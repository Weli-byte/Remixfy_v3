"""
Multi Rhyme Generator Engine

Extracts rhyming patterns from an artist's lyrics corpus, creates a rhyme 
bank of multi-syllable rhyme suggestions, and formats them to guide the 
LLM towards writing more complex, authentic rap lyrics.
"""

import logging
from collections import Counter
from typing import Dict, List

logger = logging.getLogger(__name__)


def extract_rhyme_patterns(lines: List[str]) -> Dict[str, int]:
    """
    Extracts common rhyme endings (the last 4 characters if long enough) from 
    the last words of each line to detect dominant rhyme patterns.
    """
    counts = Counter()
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        
        words = cleaned.split()
        if not words:
            continue
            
        last_word = words[-1].lower()
        
        # Keep it simple: use the last 4 characters as the rhyme pattern 
        # for multi-syllable rhymes (or the whole word if it's very short)
        suffix_len = min(4, len(last_word))
        if suffix_len >= 3:
            pattern = last_word[-suffix_len:]
            counts[pattern] += 1
            
    return dict(counts)


def build_rhyme_bank(artist_name: str) -> Dict[str, List[str]]:
    """
    Builds a rhyme bank mapping common patterns to actual words 
    from the artist's lyrics corpus.
    """
    try:
        from app.flow_analyzer import get_corpus_for_artist
        lines = get_corpus_for_artist(artist_name)
    except ImportError:
        logger.warning("Could not import get_corpus_for_artist; using empty lines.")
        lines = []

    if not lines:
        return {}
        
    # Get the frequencies
    pattern_freqs = extract_rhyme_patterns(lines)
    
    # We only care about patterns that appear frequently enough
    top_patterns = {p for p, c in pattern_freqs.items() if c >= 3}
    
    bank = {}
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
            
        words = cleaned.split()
        if not words:
            continue
            
        last_word = words[-1].lower()
        suffix_len = min(4, len(last_word))
        
        if suffix_len >= 3:
            pattern = last_word[-suffix_len:]
            if pattern in top_patterns:
                if pattern not in bank:
                    bank[pattern] = []
                if last_word not in bank[pattern]:
                    bank[pattern].append(last_word)
                    
    logger.info(f"Built rhyme bank for '{artist_name}' with {len(bank)} unique patterns.")
    return bank


def get_multi_rhyme_suggestions(pattern: str, rhyme_bank: Dict[str, List[str]], max_suggestions: int = 5) -> List[str]:
    """
    Returns suggestions for a given rhyme pattern from the custom rhyme bank.
    """
    pattern_lower = pattern.lower()
    if pattern_lower in rhyme_bank:
        return rhyme_bank[pattern_lower][:max_suggestions]
    return []
