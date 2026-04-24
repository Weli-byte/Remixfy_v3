"""
cli_app.py – Interactive terminal interface for Remixfy v3.

Uses the full Artist Style Engine pipeline:
  FLOW ANALYSIS → PROMPT BUILD → LLM GENERATION →
  RHYME VALIDATION → HOOK GENERATION → FINAL OUTPUT
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()

from app.style_engine import get_genres, get_eras_by_genre, get_artists, get_artist_profile
from app.llm_engine import generate_full_pipeline


# ── Helpers ──────────────────────────────────────────────────────────────

def _clear_line() -> None:
    print()


def _header(title: str) -> None:
    print()
    print("═" * 60)
    print(f"  🎤  {title}")
    print("═" * 60)


def _pick(label: str, options: list[str]) -> str:
    """Display numbered options and return the user's choice."""
    print()
    print(f"  {label}:")
    print("  " + "─" * 40)
    for i, opt in enumerate(options, 1):
        print(f"    [{i}] {opt}")
    print()

    while True:
        raw = input("  ▸ Seçiminiz (numara): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            chosen = options[int(raw) - 1]
            print(f"  ✓ {chosen}")
            return chosen
        print(f"  ✗ Geçersiz. 1–{len(options)} arası bir sayı girin.")


def _ask_themes() -> list[str]:
    """Prompt for comma-separated themes."""
    print()
    print("  Temalar (virgülle ayırın):")
    print("  Örnek: sokak hayatı, ihanet, karanlık geceler")
    print()
    raw = input("  ▸ ").strip()
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _ask_emotion() -> int:
    """Prompt for emotion intensity (1-10)."""
    print()
    print("  Duygu yoğunluğu (1-10):")
    print("  1–3: Yumuşak  │  4–7: Dengeli  │  8–10: Agresif")
    print()
    while True:
        raw = input("  ▸ ").strip()
        if raw.isdigit() and 1 <= int(raw) <= 10:
            val = int(raw)
            print(f"  ✓ {val}/10")
            return val
        print("  ✗ 1–10 arası bir sayı girin.")


def _ask_bpm() -> int:
    """Prompt for BPM (default 120)."""
    print()
    print("  BPM (Tempo), varsayılan: 120:")
    print("  Örnek: 90 (Boom bap), 120 (Trap), 140 (Drill)")
    print()
    while True:
        raw = input("  ▸ (BPM) [120]: ").strip()
        if not raw:
            print("  ✓ 120 BPM")
            return 120
        if raw.isdigit() and 60 <= int(raw) <= 220:
            val = int(raw)
            print(f"  ✓ {val} BPM")
            return val
        print("  ✗ 60–220 arası geçerli bir BPM değeri girin.")


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    _header("REMIXFY v3 – AI Şarkı Sözü Üretici")

    # 1. Genre
    genres = get_genres()
    if not genres:
        print("  [HATA] Tür bulunamadı.")
        sys.exit(1)
    genre = _pick("Tür seçin", genres)

    # 2. Era
    eras = get_eras_by_genre(genre)
    if not eras:
        print(f"  [HATA] '{genre}' için dönem bulunamadı.")
        sys.exit(1)
    era = _pick("Dönem seçin", eras)

    # 3. Artist
    artists = get_artists(genre, era)
    if not artists:
        print(f"  [HATA] '{genre}/{era}' için sanatçı bulunamadı.")
        sys.exit(1)
    artist_name = _pick("Sanatçı seçin", artists)

    profile = get_artist_profile(artist_name)
    if profile is None:
        print(f"  [HATA] '{artist_name}' profili yüklenemedi.")
        sys.exit(1)

    # 4. Themes
    themes = _ask_themes()

    # 5. Emotion
    emotion = _ask_emotion()

    # 6. BPM
    bpm = _ask_bpm()

    # ── Summary ──────────────────────────────────────────────────────
    _header("ÖZET")
    print(f"  Tür       : {genre}")
    print(f"  Dönem     : {era}")
    print(f"  Sanatçı   : {artist_name}")
    print(f"  Temalar   : {', '.join(themes) if themes else '—'}")
    print(f"  Yoğunluk  : {emotion}/10")
    print(f"  BPM       : {bpm}")

    # ── Full Pipeline ────────────────────────────────────────────────
    _header("ÜRETİLİYOR …")
    print("  ⏳ Artist Style Engine pipeline başlatılıyor …")
    print("     BPM PROFILE → FLOW ANALYSIS → VECTOR RETRIEVAL →")
    print("     FLOW CLUSTERING → PROMPT BUILD → LLM GENERATION →")
    print("     RHYME VALIDATION → SYLLABLE RHYTHM CHECK →")
    print("     HOOK GENERATION → FINAL OUTPUT")
    print()

    try:
        lyrics = generate_full_pipeline(
            artist_profile=profile,
            genre=genre,
            era=era,
            themes=themes,
            emotion_level=emotion,
            bpm=bpm,
        )
    except RuntimeError as exc:
        print(f"  [HATA] {exc}")
        sys.exit(1)

    # ── Output ───────────────────────────────────────────────────────
    _header("ÜRETİLEN ŞARKI SÖZLERİ")
    print()
    for line in lyrics.splitlines():
        print(f"  {line}")
    print()
    print("═" * 60)
    print("  ✅ Tamamlandı.")
    print("═" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  👋 Çıkış yapıldı.")
        sys.exit(0)
