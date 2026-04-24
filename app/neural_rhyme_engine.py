"""
Neural Rhyme Engine – Advanced phonetic rhyme analyzer for rap lyrics.

Analyzes phonetic word endings to group lines into "rhyme families",
evaluates rhyme density, and detects multi-rhyme occurrences.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


# ── Rhyme Family Extractor ──────────────────────────────────────────────

def get_rhyme_family(word: str) -> str:
    """
    Extracts the rhyme family (last 3-4 phonetic characters) from a word.

    Examples:
        yazarım -> arım
        yanarım -> arım
        kararım -> arım
    """
    # Clean up word: remove punctuation and make lowercase
    clean = re.sub(r"[^\w\s]", "", word.lower()).strip()
    
    if len(clean) <= 4:
        return clean

    # For longer words, taking the last 4 characters usually captures
    # the phonetic suffix structure effectively in Turkish (e.g. "arım", "ında").
    return clean[-4:]


# ── Multi Rhyme Analyzer ────────────────────────────────────────────────

def detect_multi_rhyme(lines: List[str]) -> bool:
    """
    Checks if there is at least one rhyme family that appears in 3 or more lines.
    
    Returns True if a multi-rhyme pattern is detected.
    """
    families = []
    for line in lines:
        words = line.strip().split()
        if not words:
            continue
        # Only analyze the last word of the line
        last_word = words[-1]
        family = get_rhyme_family(last_word)
        if family:
            families.append(family)
            
    if not families:
        return False
        
    counts = Counter(families)
    # Check if any family has a count of 3 or more
    for count in counts.values():
        if count >= 3:
            return True
            
    return False


# ── Rhyme Density Analyzer ──────────────────────────────────────────────

def calculate_rhyme_density(lines: List[str]) -> Tuple[float, bool]:
    """
    Calculate the density of rhymes across all lines.
    
    A line is considered to be part of a rhyme if its rhyme family 
    appears at least twice in the text.
    
    Returns (density_ratio, rhyme_invalid)
    Where rhyme_invalid is True if density < 40% (0.40).
    """
    families = []
    valid_line_count = 0
    
    for line in lines:
        words = line.strip().split()
        if not words or line.strip().startswith("["):
            # skip empty lines and section tags
            continue
        last_word = words[-1]
        family = get_rhyme_family(last_word)
        if family:
            families.append(family)
            valid_line_count += 1
            
    if valid_line_count < 2:
        return (0.0, True)
        
    counts = Counter(families)
    
    # Count how many lines share a rhyme family with at least one other line
    rhymed_lines = sum(1 for f in families if counts[f] >= 2)
    
    density = rhymed_lines / valid_line_count
    rhyme_invalid = density < 0.40
    
    return (density, rhyme_invalid)


# ── Master Validation ───────────────────────────────────────────────────

def validate_neural_rhyme(lines: List[str]) -> bool:
    """
    Validates rules:
    - Rhyme density must be >= 40% (rhyme_invalid = False)
    - Must contain at least one multi-rhyme (>= 3 lines sharing a family)
    
    Returns True if valid, False otherwise.
    """
    density, rhyme_invalid = calculate_rhyme_density(lines)
    multi_rhyme = detect_multi_rhyme(lines)
    
    if rhyme_invalid:
        logger.warning(f"⚠️ Neural Rhyme Failed: Density low ({density:.0%})")
        return False
        
    if not multi_rhyme:
        logger.warning("⚠️ Neural Rhyme Failed: No multi-rhyme (3+ repetitions) detected.")
        return False
        
    logger.info(f"✅ Neural Rhyme Passed: Density {density:.0%} with multi-rhymes.")
    return True


def validate_neural_rhyme_from_text(text: str) -> bool:
    """
    Convenience wrapper to validate a block of text.
    """
    lines = text.strip().splitlines()
    return validate_neural_rhyme(lines)
