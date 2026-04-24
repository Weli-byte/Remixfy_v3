"""
Stage Energy Engine - Plans the energy progression of a rap song.

Assigns descriptive energy roles and numeric energy scores to each
section of the song (verse, chorus, bridge), ensuring a dramatic
arc from buildup to final peak.
"""

import logging
from typing import Dict, Union

logger = logging.getLogger(__name__)


def build_energy_curve() -> Dict[str, str]:
    """
    Returns the descriptive energy role for each song section.

    Output:
        {
          "verse1": "build tension",
          "chorus": "energy explosion",
          "verse2": "emotional intensity",
          "bridge": "breakdown",
          "final_chorus": "peak energy"
        }
    """
    return {
        "verse1": "build tension",
        "chorus": "energy explosion",
        "verse2": "emotional intensity",
        "bridge": "breakdown",
        "final_chorus": "peak energy"
    }


def build_energy_scores() -> Dict[str, int]:
    """
    Returns numeric energy scores (1–10) for each song section.

    Output:
        {
          "verse1": 4,
          "chorus": 8,
          "verse2": 6,
          "bridge": 3,
          "final_chorus": 10
        }
    """
    return {
        "verse1": 4,
        "chorus": 8,
        "verse2": 6,
        "bridge": 3,
        "final_chorus": 10
    }


def build_stage_energy_profile() -> Dict[str, Union[Dict, str]]:
    """
    Combines energy curve and scores into a single stage energy profile.
    """
    curve = build_energy_curve()
    scores = build_energy_scores()
    logger.info("Stage Energy Profile built: %s", curve)
    return {
        "curve": curve,
        "scores": scores
    }


def format_stage_energy_block(profile: Dict) -> str:
    """
    Formats the stage energy profile into a prompt-ready text block.
    """
    curve = profile.get("curve", {})
    scores = profile.get("scores", {})

    lines = ["ENERGY CURVE:"]
    section_order = [
        ("verse1", "Verse 1"),
        ("chorus", "Chorus"),
        ("verse2", "Verse 2"),
        ("bridge", "Bridge"),
        ("final_chorus", "Final Chorus")
    ]

    for key, label in section_order:
        role = curve.get(key, "—")
        score = scores.get(key, "—")
        lines.append(f"{label} → {role}  [enerji: {score}/10]")

    lines.extend([
        "",
        "Talimat: Şarkının enerjisi bu sırayla yükselmeli.",
        "- Nakaratlarda patlama ve doruk olmalı.",
        "- Bridge kısmında enerji düşüşü ve kırılma olmalı.",
        "- Final chorus zirve enerjiyle kapanmalı."
    ])

    return "\n".join(lines)
