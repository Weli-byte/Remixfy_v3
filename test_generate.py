"""
test_generate.py – End-to-end lyric generation test.

Uses the full Artist Style Engine pipeline:
  FLOW ANALYSIS → PROMPT BUILD → LLM GENERATION →
  RHYME VALIDATION → HOOK GENERATION → FINAL OUTPUT
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()

from app.style_engine import get_artist_profile
from app.llm_engine import generate_full_pipeline


# ── Configuration ────────────────────────────────────────────────────────

GENRE = "rap"
ERA = "new"
ARTIST = "Blok3"
THEMES = ["street survival", "ambition", "betrayal", "hunger"]
EMOTION_LEVEL = 8


def main() -> None:
    # 1. Resolve artist profile
    profile = get_artist_profile(ARTIST)
    if profile is None:
        print(f"[ERROR] Artist '{ARTIST}' not found in catalogue.")
        sys.exit(1)

    print(f"✅ Artist loaded: {profile['name']}  ({profile['genre']} / {profile['era']})")

    # 2. Run the full pipeline (Flow → Prompt → LLM → Rhyme → Hook → Save)
    print("⏳ Full Artist Style Engine pipeline başlatılıyor …\n")
    try:
        text = generate_full_pipeline(
            artist_profile=profile,
            genre=GENRE,
            era=ERA,
            themes=THEMES,
            emotion_level=EMOTION_LEVEL,
        )
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    # 3. Print results
    print("═" * 60)
    print("  GENERATED LYRICS")
    print("═" * 60)
    print()
    print(text)
    print()
    print("═" * 60)


if __name__ == "__main__":
    main()
