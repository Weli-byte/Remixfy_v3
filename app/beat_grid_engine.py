"""
Beat Grid Alignment Engine - Calculates and validates rhythmic beat alignment.

Ensures rap lines fit musically over a given BPM grid by estimating
ideal syllable counts per bar and verifying generated lines against it.
"""

import logging
from typing import Dict, List, Tuple, Union

logger = logging.getLogger(__name__)


def build_beat_grid(bpm: int) -> Dict[str, Union[int, float]]:
    """
    Calculates the beat structure based on BPM.
    """
    # Assuming common 4/4 time signature
    beats_per_bar = 4
    
    # Duration of one beat in seconds
    if bpm <= 0:
        bpm = 120
        
    beat_duration = 60.0 / bpm
    bar_duration = beat_duration * beats_per_bar
    
    return {
        "bpm": bpm,
        "beats_per_bar": beats_per_bar,
        "beat_duration": round(beat_duration, 4),
        "bar_duration": round(bar_duration, 4)
    }


def estimate_syllables_for_bar(bpm: int) -> Tuple[int, int]:
    """
    Estimates the ideal syllable range per bar based on BPM.
    """
    if bpm < 95:
        return (12, 16)
    elif bpm < 110:
        return (11, 14)
    elif bpm < 130:
        return (10, 13)
    elif bpm < 145:
        return (9, 12)
    else:
        return (8, 11)


def count_syllables(line: str) -> int:
    """
    Simple Turkish syllable counter based on vowels.
    """
    vowels = "aeıioöuüAEIİOÖUÜ"
    return sum(1 for char in line if char in vowels)


def validate_beat_alignment(lines: List[str], bpm: int) -> Dict[str, Union[bool, float]]:
    """
    Validates if the generated lines align well with the beat grid.
    Ratio of lines within the ideal syllable range must be >= 0.60.
    """
    syllable_range = estimate_syllables_for_bar(bpm)
    min_syl, max_syl = syllable_range
    
    valid_lines_count = 0
    aligned_lines_count = 0
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
            
        valid_lines_count += 1
        syl_count = count_syllables(cleaned)
        
        # Check if line falls within the estimated ideal range
        if min_syl <= syl_count <= max_syl:
            aligned_lines_count += 1
            
    ratio = 0.0
    if valid_lines_count > 0:
        ratio = aligned_lines_count / valid_lines_count
        
    logger.debug(f"Beat Alignment - BPM: {bpm}, Range: {syllable_range}, Ratio: {ratio:.2f}")
    
    return {
        "valid": ratio >= 0.60,
        "ratio": ratio
    }
