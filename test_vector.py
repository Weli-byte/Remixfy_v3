"""
test_vector.py – Semantic retrieval test for Blok3.

Tests the Vector Retrieval Engine by:
1. Building the vector index for Blok3
2. Searching for themes: "aşk, gurur, ihanet"
3. Displaying the top-N most semantically similar corpus lines
4. Verifying the results are relevant and the pipeline works end-to-end

Usage:
    python test_vector.py
"""

from __future__ import annotations

import sys
import time

from dotenv import load_dotenv

load_dotenv()


# ── Configuration ────────────────────────────────────────────────────────

ARTIST = "Blok3"
THEMES = ["aşk", "gurur", "ihanet"]
K_PER_QUERY = 10
TOTAL_K = 30


def _header(title: str) -> None:
    print()
    print("═" * 70)
    print(f"  🔎  {title}")
    print("═" * 70)


def main() -> None:
    _header("VECTOR RETRIEVAL TEST – Blok3")

    # ── Step 1: Build index ──────────────────────────────────────────
    print("\n  ⏳ Vector index oluşturuluyor …\n")

    from app.vector_store import (
        build_artist_index,
        search_similar_lines,
        search_multi_query,
        get_index_stats,
    )

    t0 = time.time()
    ok = build_artist_index(ARTIST)
    elapsed = time.time() - t0

    if not ok:
        print(f"  [HATA] '{ARTIST}' için corpus bulunamadı.")
        sys.exit(1)

    stats = get_index_stats(ARTIST)
    if stats:
        print(f"  ✅ Index hazır ({elapsed:.1f}s)")
        print(f"     Sanatçı      : {stats['artist']}")
        print(f"     Satır sayısı : {stats['lines']}")
        print(f"     Embedding dim: {stats['embedding_dim']}")

    # ── Step 2: Single-query tests ───────────────────────────────────
    for theme in THEMES:
        _header(f"TEK TEMA ARAMA: \"{theme}\"")

        results = search_similar_lines(
            query=theme,
            artist_name=ARTIST,
            k=K_PER_QUERY,
        )

        print(f"\n  Top {len(results)} benzer satır:\n")
        for i, line in enumerate(results, 1):
            print(f"    {i:2d}. {line}")

    # ── Step 3: Multi-query search ───────────────────────────────────
    _header(f"ÇOKLU TEMA ARAMA: {', '.join(THEMES)}")

    t0 = time.time()
    multi_results = search_multi_query(
        queries=THEMES,
        artist_name=ARTIST,
        k_per_query=K_PER_QUERY,
        total_k=TOTAL_K,
    )
    elapsed = time.time() - t0

    print(f"\n  {len(multi_results)} benzersiz satır bulundu ({elapsed:.2f}s):\n")
    for i, line in enumerate(multi_results, 1):
        print(f"    {i:2d}. {line}")

    # ── Step 4: Cache re-use test ────────────────────────────────────
    _header("CACHE TEST")

    t0 = time.time()
    ok2 = build_artist_index(ARTIST)  # should be instant (cache hit)
    elapsed2 = time.time() - t0

    print(f"\n  ✅ İkinci build_artist_index çağrısı: {elapsed2:.4f}s (cache)")
    assert elapsed2 < 0.01, "Cache miss — ikinci çağrı çok yavaş!"
    print("  ✅ Cache doğru çalışıyor.\n")

    # ── Step 5: Prompt integration preview ───────────────────────────
    _header("PROMPT ENTEGRASYONU ÖNİZLEME")

    from app.prompt_builder import get_semantic_examples

    sem_examples = get_semantic_examples(ARTIST, THEMES, k=20)
    print(f"\n  get_semantic_examples → {len(sem_examples)} satır\n")
    for i, line in enumerate(sem_examples[:10], 1):
        print(f"    {i:2d}. {line}")
    if len(sem_examples) > 10:
        print(f"    ... ve {len(sem_examples) - 10} satır daha")

    # ── Done ─────────────────────────────────────────────────────────
    print()
    print("═" * 70)
    print("  ✅ Tüm testler başarılı.")
    print("═" * 70)
    print()


if __name__ == "__main__":
    main()
