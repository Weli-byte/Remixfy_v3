"""
Blok3 Corpus Builder

Reads data/blok3_corpus.txt, cleans it line-by-line, and injects
the resulting lyrics_corpus into data/artists.json under the Blok3 entry.

Usage:
    python data/build_blok3_corpus.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
CORPUS_FILE = ROOT / "blok3_corpus.txt"
ARTISTS_FILE = ROOT / "artists.json"

# ── Section / header patterns to strip ───────────────────────────────────

_HEADER_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\[?(nakarat|verse|intro|outro|bridge|chorus|hook|pre-chorus|post-chorus|interlude|ref|refren)\]?\s*:?\s*$", re.IGNORECASE),
    re.compile(r"^\[?(nakarat|verse|intro|outro|bridge|chorus|hook|pre-chorus|post-chorus|interlude|ref|refren)\s*\d*\]?\s*:?\s*$", re.IGNORECASE),
    re.compile(r"^\[.*\]\s*$"),  # Any [TAG] lines
]


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
    # Only normalize if every alphabetic character is uppercase
    alpha_chars = [c for c in stripped if c.isalpha()]
    if alpha_chars and all(c.isupper() for c in alpha_chars):
        return stripped.capitalize()
    return stripped


def clean_corpus(raw_lines: list[str]) -> tuple[list[str], int]:
    """
    Clean raw lyrics lines.

    Returns:
        (cleaned_lines, duplicate_count)
    """
    seen: set[str] = set()
    cleaned: list[str] = []
    duplicates = 0

    for raw in raw_lines:
        # Strip whitespace
        line = raw.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip section headers
        if _is_header(line):
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
    # ── 1. Read corpus file ──────────────────────────────────────────
    if not CORPUS_FILE.exists():
        print(f"❌ HATA: Corpus dosyası bulunamadı: {CORPUS_FILE}")
        print("   Önce data/blok3_corpus.txt dosyasını oluşturun.")
        sys.exit(1)

    raw_lines = CORPUS_FILE.read_text(encoding="utf-8").splitlines()
    print(f"📄 Dosya okundu: {len(raw_lines)} ham satır")

    # ── 2. Clean ─────────────────────────────────────────────────────
    cleaned, dup_count = clean_corpus(raw_lines)
    print(f"🧹 Temizleme tamamlandı:")
    print(f"   • {len(cleaned)} temiz satır")
    print(f"   • {dup_count} duplicate kaldırıldı")
    print(f"   • {len(raw_lines) - len(cleaned) - dup_count} boş/başlık satır kaldırıldı")

    if not cleaned:
        print("⚠️  UYARI: Temizleme sonrası corpus boş! İşlem durduruldu.")
        sys.exit(1)

    # ── 3. Load artists.json ─────────────────────────────────────────
    if not ARTISTS_FILE.exists():
        print(f"❌ HATA: artists.json bulunamadı: {ARTISTS_FILE}")
        sys.exit(1)

    with open(ARTISTS_FILE, "r", encoding="utf-8") as f:
        artists = json.load(f)

    # ── 4. Find Blok3 ────────────────────────────────────────────────
    blok3_entry = None
    blok3_index = -1

    for i, artist in enumerate(artists):
        if artist.get("name", "").lower() == "blok3":
            blok3_entry = artist
            blok3_index = i
            break

    if blok3_entry is None:
        print("❌ HATA: 'Blok3' sanatçısı artists.json içinde bulunamadı!")
        sys.exit(1)

    print(f"🎤 Blok3 bulundu (index: {blok3_index})")

    # ── 5. Inject lyrics_corpus ──────────────────────────────────────
    old_count = len(blok3_entry.get("lyrics_corpus", []))
    blok3_entry["lyrics_corpus"] = cleaned
    artists[blok3_index] = blok3_entry

    # ── 6. Save ──────────────────────────────────────────────────────
    with open(ARTISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)

    print()
    print("═" * 50)
    print(f"  ✅ Blok3 lyrics_corpus güncellendi!")
    print(f"  • Eski satır sayısı : {old_count}")
    print(f"  • Yeni satır sayısı : {len(cleaned)}")
    print(f"  • Duplicate temizlenen: {dup_count}")
    print("═" * 50)


if __name__ == "__main__":
    main()
