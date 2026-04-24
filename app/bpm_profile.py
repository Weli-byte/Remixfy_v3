"""
BPM Profile – Maps Beat Per Minute to flow style and syllable range.

Provides tempo-aware syllable targets so that generated lyrics
match the rhythmic feel of the intended beat.

Pure Python.  No external dependencies.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# ── BPM → Flow Style mapping ────────────────────────────────────────────

_BPM_TIERS = [
    # (max_bpm, syllable_min, syllable_max, flow_label, description)
    (95,  12, 16, "boom_bap",     "Yavaş, ağır boom-bap. Uzun, detaylı satırlar."),
    (110, 11, 14, "old_school",   "Old-school hip-hop. Dengeli ritim, orta uzunluk."),
    (125, 10, 13, "trap",         "Trap / modern rap. Orta hızda, ritmik satırlar."),
    (140,  9, 12, "fast_trap",    "Hızlı trap / drill. Kısa, vurucu satırlar."),
    (999,  8, 11, "double_time",  "Çok hızlı / double-time. Kısa, hızlı satırlar."),
]

_DEFAULT_BPM = 120


def get_bpm_profile(bpm: int = _DEFAULT_BPM) -> Dict[str, Any]:
    """
    Return a BPM-aware profile with syllable range and flow label.

    Parameters
    ----------
    bpm : int – beats per minute (default 120)

    Returns
    -------
    dict with keys:
        bpm             – int
        syllable_range  – list[int, int], [min, max] syllables per line
        flow            – str, flow style label
        description     – str, human-readable description
    """
    bpm = max(60, min(bpm, 220))  # clamp to reasonable range

    for max_bpm, syl_min, syl_max, flow, desc in _BPM_TIERS:
        if bpm < max_bpm:
            profile = {
                "bpm": bpm,
                "syllable_range": [syl_min, syl_max],
                "flow": flow,
                "description": desc,
            }
            logger.info(
                "🎛️ BPM profile: %d BPM → %s (%d–%d syllables)",
                bpm, flow, syl_min, syl_max,
            )
            return profile

    # Fallback (should not reach here due to 999 catch-all)
    return {
        "bpm": bpm,
        "syllable_range": [8, 14],
        "flow": "standard",
        "description": "Standart rap ritmi.",
    }


def get_flow_label(bpm: int) -> str:
    """Return just the flow label for a given BPM."""
    return get_bpm_profile(bpm)["flow"]


def get_syllable_range(bpm: int) -> Tuple[int, int]:
    """Return (min, max) syllable range for a given BPM."""
    profile = get_bpm_profile(bpm)
    return tuple(profile["syllable_range"])
def get_prompt_bpm_block(bpm: int) -> str:
    """
    Return a text block describing BPM flow for prompt injection.
    """
    profile = get_bpm_profile(bpm)

    min_s, max_s = profile["syllable_range"]

    return (
        f"BEAT TEMPO: {profile['bpm']} BPM\n"
        f"FLOW STYLE: {profile['flow']}\n"
        f"{profile['description']}\n"
        f"Satır başına yaklaşık {min_s}-{max_s} hece hedefle."
    )