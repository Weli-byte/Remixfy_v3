"""
Punchline Engine – Predicts and assigns slots for impactful lines.

Calculates optimal positions within a song's sections to insert 
punchlines (e.g., at ends of 4-bar units). Ensures the LLM delivers
witty and memorable lines at these specific structural checkpoints.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def detect_punchline_slots(section_length: int) -> List[int]:
    """
    Calculates where punchlines should be placed within a section based on its length.

    Parameters
    ----------
    section_length : int
        The total number of lines (bars) in the section.

    Returns
    -------
    list of int:
        A list of 1-indexed line numbers where the punchlines should be inserted.
    """
    if section_length >= 12:
        slots = [4, 8, 12]
    elif section_length >= 8:
        slots = [4, 8]
    elif section_length >= 4:
        slots = [4]
    else:
        slots = []
        
    return slots


def format_punchline_slots(slots: List[int]) -> str:
    """
    Formats the punchline slot list into text suitable for the prompt.
    """
    if not slots:
        return ""

    lines = ["PUNCHLINE PLAN:"]
    for slot in slots:
        lines.append(f"Satır {slot} → güçlü punchline")
        
    lines.extend([
        "",
        "Bu satırlarda:",
        "- zekice",
        "- vurucu",
        "- akılda kalıcı",
        "",
        "rap punchline kullan."
    ])
    
    return "\n".join(lines)
