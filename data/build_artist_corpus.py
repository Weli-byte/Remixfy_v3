"""
Universal Artist Corpus Builder

Scans data/artists_corpus/ for .txt files,
cleans each one and injects the lyrics_corpus
into the matching artist entry in data/artists.json.

File name → artist name:
    blok3.txt  → Blok3
    ceza.txt   → Ceza
    ezhel.txt  → Ezhel

Usage:
    python data/build_artist_corpus.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "artists_corpus"
ARTISTS_FILE = ROOT / "artists.json"

# ── Section / header patterns to strip ───────────────────────────────────

_HEADER_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"^\[?(nakarat|verse|intro|outro|bridge|chorus|hook|"
        r"pre-chorus|post-chorus|interlude|ref|refren)\]?\s*:?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\[?(nakarat|verse|intro|outro|bridge|chorus|hook|"
        r"pre-chorus|post-chorus|interlude|ref|refren)\s*\d*\]?\s*:?\s*$",
        re.IGNORECASE,
    ),
    re.compile(r"^\[.*\]\s*$"),  # Any [TAG] lines
]

MIN_WORD_COUNT = 3  # Minimum word count per line


def _is_header(line: str) -> bool:
    """Check if a line is a section header that should be removed."""
    stripped = line.strip()
    for pat in _HEADER_PATTERNS:
        if pat.match(stripped):
            return True
    return False


def _normalize_case(line: str) -> str:
    """
    If the line is ALL CAPS, convert to title-case-like normalisation:
    first letter uppercase, rest lowercase.
    """
    stripped = line.strip()
    alpha_chars = [c for c in stripped if c.isalpha()]
    if alpha_chars and all(c.isupper() for c in alpha_chars):
        return stripped.capitalize()
    return stripped


def _artist_name_from_filename(filename: str) -> str:
    """
    Derive a display-ready artist name from a .txt filename.
    blok3.txt → Blok3
    ceza.txt  → Ceza
    sagopa.txt → Sagopa
    """
    stem = Path(filename).stem  # e.g. "blok3"
    return stem.capitalize()


def clean_corpus(raw_lines: list[str]) -> tuple[list[str], int]:
    """
    Clean raw lyrics lines.

    Rules applied:
    - Strip whitespace
    - Remove empty lines
    - Remove section headers ([VERSE], [CHORUS], [NAKARAT], [HOOK], etc.)
    - Remove lines with fewer than MIN_WORD_COUNT words
    - Normalize ALL-CAPS lines
    - Remove duplicate lines (case-insensitive)

    Returns:
        (cleaned_lines, duplicate_count)
    """
    seen: set[str] = set()
    cleaned: list[str] = []
    duplicates = 0

    for raw in raw_lines:
        line = raw.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip section headers
        if _is_header(line):
            continue

        # Skip lines that are too short (less than MIN_WORD_COUNT words)
        if len(line.split()) < MIN_WORD_COUNT:
            continue

        # Normalize all-caps lines
        line = _normalize_case(line)

        # Deduplicate (case-insensitive)
        key = line.lower()
        if key in seen:
            duplicates += 1
            continue

        seen.add(key)
        cleaned.append(line)

    return cleaned, duplicates


def main() -> None:
    # ── 1. Check corpus directory ────────────────────────────────────
    if not CORPUS_DIR.exists():
        print(f"❌ HATA: Corpus klasörü bulunamadı: {CORPUS_DIR}")
        print("   Önce data/artists_corpus/ klasörünü oluşturun.")
        sys.exit(1)

    txt_files = sorted(CORPUS_DIR.glob("*.txt"))

    if not txt_files:
        print(f"❌ HATA: {CORPUS_DIR} içinde hiç .txt dosyası bulunamadı!")
        print("   Sanatçı corpus dosyalarını ekleyin (örn: blok3.txt, ceza.txt)")
        sys.exit(1)

    # ── 2. Load artists.json ─────────────────────────────────────────
    if not ARTISTS_FILE.exists():
        print(f"❌ HATA: artists.json bulunamadı: {ARTISTS_FILE}")
        sys.exit(1)

    with open(ARTISTS_FILE, "r", encoding="utf-8") as f:
        artists = json.load(f)

    # Build a name → index lookup (case-insensitive)
    name_index: dict[str, int] = {}
    for i, artist in enumerate(artists):
        name_index[artist.get("name", "").lower()] = i

    # ── 3. Process each corpus file ──────────────────────────────────
    report_lines: list[str] = []

    for txt_file in txt_files:
        artist_name = _artist_name_from_filename(txt_file.name)
        raw_lines = txt_file.read_text(encoding="utf-8").splitlines()

        cleaned, dup_count = clean_corpus(raw_lines)

        # Find or create the artist entry
        lookup_key = artist_name.lower()

        if lookup_key in name_index:
            # Artist already exists → update lyrics_corpus
            idx = name_index[lookup_key]
            artists[idx]["lyrics_corpus"] = cleaned
            status = "güncellendi"
        else:
            # Artist does not exist → create a new entry
            new_entry = {
                "name": artist_name,
                "genre": "rap",
                "era": "",
                "dna": {
                    "signature_energy": "",
                    "cadence_pattern": "",
                    "word_texture": "",
                    "theme_bias": [],
                    "ego_vulnerability_ratio": "",
                    "hook_style": "",
                    "typical_imagery": [],
                    "style_fragments": [],
                    "style_imprint_lines": [],
                    "mechanics": {
                        "line_length_avg": "",
                        "line_break_style": "",
                        "punchline_model": "",
                        "rhyme_positioning": "",
                        "internal_rhyme_density": "",
                        "hook_structure": "",
                        "emotional_axis": "",
                    },
                },
                "lyrics_corpus": cleaned,
            }
            artists.append(new_entry)
            name_index[lookup_key] = len(artists) - 1
            status = "yeni eklendi"

        report_lines.append(
            f"Artist: {artist_name}\n"
            f"  lines loaded: {len(cleaned)}\n"
            f"  duplicates removed: {dup_count}\n"
            f"  status: {status}"
        )

    # ── 4. Save artists.json ─────────────────────────────────────────
    with open(ARTISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)

    # ── 5. Print report ──────────────────────────────────────────────
    print()
    print("=" * 40)
    print("  CORPUS BUILD REPORT")
    print("=" * 40)
    print()
    for block in report_lines:
        print(block)
        print()
    print("=" * 40)
    print(f"  ✅ {len(report_lines)} sanatçı işlendi.")
    print(f"  📁 artists.json güncellendi.")
    print("=" * 40)


if __name__ == "__main__":
    main()
