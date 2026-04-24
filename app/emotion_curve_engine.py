"""
Emotion Curve Engine – Generates emotional roles for song sections.

This module plans the emotional progression (curve) of a song based on
the main theme and emotion intensity level. It assigns specific emotional
roles to each section (VERSE1, CHORUS, VERSE2, BRIDGE, FINAL CHORUS),
which guides the LLM to write a song with a coherent emotional trajectory.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def build_emotion_curve(theme: str, emotion_level: int) -> Dict[str, str]:
    """
    Assigns emotional roles to song sections based on intensity.

    Parameters
    ----------
    theme : str
        The main theme of the song (e.g., 'aşk', 'ihanet').
    emotion_level : int
        Intensity of the emotion on a scale from 1 to 10.

    Returns
    -------
    dict:
        A dictionary mapping song sections to their emotional roles.
    """
    logger.info(f"Building emotion curve for theme='{theme}', level={emotion_level}")
    
    # Ensure emotion_level is within expected bounds
    level = max(1, min(10, emotion_level))

    if level <= 4:
        # Düşük yoğunluk (1-4)
        curve = {
            "verse1": "anlatım",
            "chorus": "hafif duygu",
            "verse2": "içsel sorgu",
            "bridge": "kısa geçiş",
            "final_chorus": "orta yoğunluk"
        }
    elif level <= 7:
        # Orta yoğunluk (5-7)
        curve = {
            "verse1": "kırgınlık veya anlatım",
            "chorus": "duygusal patlama",
            "verse2": "ego veya güç gösterisi",
            "bridge": "içsel kırılma",
            "final_chorus": "zirve"
        }
    else:
        # Yüksek yoğunluk (8-10)
        curve = {
            "verse1": "yoğun kırgınlık veya öfke",
            "chorus": "güçlü duygusal patlama",
            "verse2": "ego / meydan okuma",
            "bridge": "dramatik kırılma",
            "final_chorus": "maksimal duygu"
        }
        
    return curve


def format_emotion_curve(curve: Dict[str, str]) -> str:
    """
    Formats the emotion curve dictionary into a string for the prompt.
    """
    lines = [
        "EMOTION CURVE:",
        f"VERSE1 → {curve.get('verse1', 'anlatım')}",
        f"CHORUS → {curve.get('chorus', 'duygu')}",
        f"VERSE2 → {curve.get('verse2', 'ego')}",
        f"BRIDGE → {curve.get('bridge', 'geçiş')}",
        f"FINAL CHORUS → {curve.get('final_chorus', 'zirve')}",
        "",
        "Her bölüm bu duygusal rolü yansıtmalıdır."
    ]
    return "\n".join(lines)
