"""
update_artists.py – Ensures required rap artists exist in data/artists.json.

Actions:
  1. Add missing artists with realistic style profiles.
  2. Fix genre/era if an artist exists but under wrong values.
  3. Remove duplicates (keep first occurrence).
  4. Keep total count under 260.
  5. Overwrite artists.json safely.
  6. Print summary of all changes.
"""

from __future__ import annotations

import json
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
ARTISTS_PATH = SCRIPT_DIR / "artists.json"

# ── Required artists (genre=rap, era=new) ────────────────────────────────
REQUIRED: dict[str, dict] = {
    "Era7capone": {
        "flow_description": "Aggressive drill-trap hybrid with gritty street cadence",
        "rhyme_complexity": "medium",
        "emotional_tone": "cold, menacing",
        "common_themes": ["street credibility", "survival", "loyalty"],
        "structural_tendency": "short hook",
    },
    "Poizi": {
        "flow_description": "Melodic emo-rap delivery with autotuned vulnerability",
        "rhyme_complexity": "low",
        "emotional_tone": "melancholic, introspective",
        "common_themes": ["heartbreak", "loneliness", "late nights"],
        "structural_tendency": "repetitive chorus",
    },
    "Heijan": {
        "flow_description": "Melodic arabesk-rap fusion with emotional delivery",
        "rhyme_complexity": "medium",
        "emotional_tone": "melancholic, passionate",
        "common_themes": ["heartbreak", "betrayal", "struggle"],
        "structural_tendency": "repetitive chorus",
    },
    "Muti": {
        "flow_description": "Dark boom-bap flow with dense lyrical layers",
        "rhyme_complexity": "high",
        "emotional_tone": "dark, thoughtful",
        "common_themes": ["inner conflict", "resilience", "underground pride"],
        "structural_tendency": "long verse",
    },
    "Jeff Redd": {
        "flow_description": "Smooth R&B-infused rap with laid-back groove",
        "rhyme_complexity": "medium",
        "emotional_tone": "cool, confident",
        "common_themes": ["nightlife", "romance", "self-expression"],
        "structural_tendency": "short hook",
    },
    "Mavi": {
        "flow_description": "Conscious lyrical flow with jazz-rap undertones",
        "rhyme_complexity": "high",
        "emotional_tone": "reflective, poetic",
        "common_themes": ["identity", "culture", "growth"],
        "structural_tendency": "long verse",
    },
    "Critical": {
        "flow_description": "Hard-hitting punchline rap with aggressive energy",
        "rhyme_complexity": "high",
        "emotional_tone": "fierce, confrontational",
        "common_themes": ["battle rap", "dominance", "technical skill"],
        "structural_tendency": "long verse",
    },
}

TARGET_GENRE = "rap"
TARGET_ERA = "new"
MAX_TOTAL = 260


def main() -> None:
    # ── Load ─────────────────────────────────────────────────────────────
    if not ARTISTS_PATH.exists():
        print(f"ERROR: {ARTISTS_PATH} not found.")
        return

    with ARTISTS_PATH.open("r", encoding="utf-8") as f:
        catalogue: list[dict] = json.load(f)

    print(f"Loaded {len(catalogue)} artists from {ARTISTS_PATH.name}\n")

    added: list[str] = []
    fixed_genre: list[str] = []
    fixed_era: list[str] = []
    duplicates_removed: list[str] = []

    # ── 1. Deduplicate (keep first occurrence) ───────────────────────────
    seen: dict[str, int] = {}
    unique: list[dict] = []
    for artist in catalogue:
        key = artist["name"].lower()
        if key in seen:
            duplicates_removed.append(artist["name"])
        else:
            seen[key] = len(unique)
            unique.append(artist)
    catalogue = unique

    # ── 2. Ensure required artists ───────────────────────────────────────
    name_index: dict[str, int] = {
        a["name"].lower(): i for i, a in enumerate(catalogue)
    }

    for name, profile in REQUIRED.items():
        key = name.lower()

        if key in name_index:
            idx = name_index[key]
            entry = catalogue[idx]

            # Fix genre
            if entry["genre"] != TARGET_GENRE:
                old = entry["genre"]
                entry["genre"] = TARGET_GENRE
                fixed_genre.append(f"{name} ({old} → {TARGET_GENRE})")

            # Fix era
            if entry["era"] != TARGET_ERA:
                old = entry["era"]
                entry["era"] = TARGET_ERA
                fixed_era.append(f"{name} ({old} → {TARGET_ERA})")

        else:
            # Add new artist
            new_entry = {
                "name": name,
                "genre": TARGET_GENRE,
                "era": TARGET_ERA,
                "style_profile": profile,
            }
            catalogue.append(new_entry)
            added.append(name)

    # ── 3. Enforce max count ─────────────────────────────────────────────
    trimmed = 0
    if len(catalogue) > MAX_TOTAL:
        # Remove excess from the end, but never remove a required artist
        required_lower = {n.lower() for n in REQUIRED}
        while len(catalogue) > MAX_TOTAL:
            # Walk backwards to find a non-required artist to remove
            for i in range(len(catalogue) - 1, -1, -1):
                if catalogue[i]["name"].lower() not in required_lower:
                    catalogue.pop(i)
                    trimmed += 1
                    break

    # ── 4. Write ─────────────────────────────────────────────────────────
    with ARTISTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)

    # ── 5. Summary ───────────────────────────────────────────────────────
    print("═" * 50)
    print("  UPDATE SUMMARY")
    print("═" * 50)

    if added:
        print(f"\n  ✅ Added ({len(added)}):")
        for n in added:
            print(f"     + {n}")

    if fixed_genre:
        print(f"\n  🔧 Genre fixed ({len(fixed_genre)}):")
        for n in fixed_genre:
            print(f"     ~ {n}")

    if fixed_era:
        print(f"\n  🔧 Era fixed ({len(fixed_era)}):")
        for n in fixed_era:
            print(f"     ~ {n}")

    if duplicates_removed:
        print(f"\n  🗑  Duplicates removed ({len(duplicates_removed)}):")
        for n in duplicates_removed:
            print(f"     - {n}")

    if trimmed:
        print(f"\n  ✂  Trimmed {trimmed} artist(s) to stay under {MAX_TOTAL}")

    if not any([added, fixed_genre, fixed_era, duplicates_removed, trimmed]):
        print("\n  ℹ  No changes needed – catalogue is already up to date.")

    print(f"\n  📊 Final count: {len(catalogue)} artists")
    print(f"  💾 Saved to: {ARTISTS_PATH.name}")
    print("═" * 50)


if __name__ == "__main__":
    main()
