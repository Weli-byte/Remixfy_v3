"""
Rhyme Quality Engine - Analyzes rhyme density and internal rhymes.

This module acts as a quality control layer after generation.
It ensures that the generated lyrics contain strong multi-syllable
end rhymes and make sufficient use of internal rhyming.
"""

import logging
from collections import Counter
from typing import Dict, List, Union

logger = logging.getLogger(__name__)


def analyze_rhyme_density(lines: List[str]) -> Dict[str, Union[bool, float]]:
    """
    Analyzes the end-of-line rhyme density based on the last 3 chars.
    Expects at least 40% (0.40) density for the most common pattern.
    """
    total_valid_lines = 0
    counts = Counter()
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
            
        words = cleaned.split()
        if not words:
            continue
            
        last_word = words[-1].lower()
        if len(last_word) >= 3:
            pattern = last_word[-3:]
            counts[pattern] += 1
        total_valid_lines += 1
        
    if total_valid_lines == 0:
        return {"valid": False, "density": 0.0}
        
    if not counts:
        return {"valid": False, "density": 0.0}
        
    most_common_pattern, count = counts.most_common(1)[0]
    density = count / total_valid_lines
    
    return {
        "valid": density >= 0.40,
        "density": density
    }


def detect_internal_rhyme(line: str) -> bool:
    """
    Detects if there are repeating 3-character suffixes among words
    in a single line (internal rhyme).
    """
    words = line.strip().split()
    if len(words) < 2:
        return False
        
    counts = Counter()
    for word in words:
        word_lower = word.lower()
        
        # Strip simple punctuation from ends for better detection
        import string
        word_lower = word_lower.strip(string.punctuation)
        
        if len(word_lower) >= 3:
            pattern = word_lower[-3:]
            counts[pattern] += 1
            
            if counts[pattern] >= 2:
                # Found at least two words with the same 3-char ending in this line
                return True
                
    return False


def analyze_internal_rhyme(lines: List[str]) -> Dict[str, float]:
    """
    Calculates what ratio of lines contain internal rhymes.
    """
    total_lines = 0
    internal_rhyme_count = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        total_lines += 1
        if detect_internal_rhyme(line):
            internal_rhyme_count += 1
            
    ratio = 0.0
    if total_lines > 0:
        ratio = internal_rhyme_count / total_lines
        
    return {
        "internal_rhyme_ratio": ratio
    }


def validate_rhyme_quality(lines: List[str]) -> str:
    """
    Validates the overall generated lyric rhyme quality.
    Checks if density >= 0.40 and internal_ratio >= 0.15.
    Returns 'RHYME_WEAK' if it fails either, 'RHYME_OK' if tests pass.
    """
    density_result = analyze_rhyme_density(lines)
    internal_result = analyze_internal_rhyme(lines)
    
    density = density_result["density"]
    internal_ratio = internal_result["internal_rhyme_ratio"]
    
    logger.debug(f"Rhyme Quality Check - Density: {density:.2f}, Internal Ratio: {internal_ratio:.2f}")
    
    if density < 0.40 or internal_ratio < 0.15:
        return "RHYME_WEAK"
        
    return "RHYME_OK"
