"""
Vector Store – Semantic search over an artist's lyrics_corpus.

Uses sentence-transformers (all-MiniLM-L6-v2) to encode corpus lines
into dense embeddings, then sklearn NearestNeighbors for fast kNN retrieval.

Indexes are built once per artist and cached in-memory for the
lifetime of the process.  No persistent storage / no extra API calls.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Lazy-loaded heavy dependencies ──────────────────────────────────────
# We defer imports so that modules which don't need vector search
# (e.g. tests that mock LLM calls) don't pay the start-up cost.

_model = None          # SentenceTransformer instance (loaded once)
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    """Lazy-load the SentenceTransformer model (singleton)."""
    global _model
    if _model is not None:
        return _model

    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model '%s' …", _MODEL_NAME)
    t0 = time.time()
    _model = SentenceTransformer(_MODEL_NAME)
    logger.info("Model loaded in %.1f s", time.time() - t0)
    return _model


# ── Per-artist index cache ──────────────────────────────────────────────

class _ArtistIndex:
    """In-memory vector index for a single artist's corpus."""

    __slots__ = ("artist_name", "lines", "embeddings", "nn")

    def __init__(
        self,
        artist_name: str,
        lines: List[str],
        embeddings: np.ndarray,
    ) -> None:
        from sklearn.neighbors import NearestNeighbors

        self.artist_name = artist_name
        self.lines = lines
        self.embeddings = embeddings
        # cosine distance via brute-force — fast for <10 k lines
        self.nn = NearestNeighbors(
            n_neighbors=min(50, len(lines)),
            metric="cosine",
            algorithm="brute",
        )
        self.nn.fit(embeddings)


# artist_name (lowered) → _ArtistIndex
_index_cache: Dict[str, _ArtistIndex] = {}


# ── Public API ───────────────────────────────────────────────────────────

def build_artist_index(artist_name: str) -> bool:
    """
    Build (or retrieve from cache) the vector index for an artist.

    Reads the artist's ``lyrics_corpus`` from ``artists.json`` via the
    shared ``flow_analyzer.get_corpus_for_artist`` helper, embeds every
    non-empty line, and stores the result in an in-memory cache.

    Returns ``True`` if the index is ready, ``False`` if the corpus is
    empty or missing.
    """
    key = artist_name.strip().lower()

    # ── Cache hit ────────────────────────────────────────────────────
    if key in _index_cache:
        logger.debug("Index cache hit for '%s' (%d lines).",
                      artist_name, len(_index_cache[key].lines))
        return True

    # ── Load corpus ──────────────────────────────────────────────────
    from app.flow_analyzer import get_corpus_for_artist

    raw_corpus = get_corpus_for_artist(artist_name)
    # Keep only non-empty, stripped lines
    lines = [l.strip() for l in raw_corpus if l.strip()]

    if not lines:
        logger.warning("No corpus lines for '%s' – cannot build index.", artist_name)
        return False

    # ── Embed ────────────────────────────────────────────────────────
    model = _get_model()

    logger.info("Embedding %d corpus lines for '%s' …", len(lines), artist_name)
    t0 = time.time()
    embeddings: np.ndarray = model.encode(
        lines,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,    # pre-normalise for cosine
    )
    elapsed = time.time() - t0
    logger.info(
        "Embeddings ready: shape=%s, %.1f s (%.0f lines/s)",
        embeddings.shape, elapsed, len(lines) / max(elapsed, 0.001),
    )

    # ── Store ────────────────────────────────────────────────────────
    _index_cache[key] = _ArtistIndex(artist_name, lines, embeddings)
    return True


def search_similar_lines(
    query: str,
    artist_name: str,
    k: int = 20,
    style_embedding: Optional[List[float]] = None,
) -> List[str]:
    """
    Return the *k* most semantically similar corpus lines to *query*.

    The index for *artist_name* must already have been built (via
    ``build_artist_index``).  If not, this function will attempt to build
    it on-the-fly.

    Parameters
    ----------
    query           : str   – free-text search query (theme, topic, etc.)
    artist_name     : str   – artist whose corpus to search
    k               : int   – number of results to return (default 20)
    style_embedding : list  – optional semantic style vector to guide retrieval

    Returns
    -------
    list[str]  – up to *k* corpus lines, ordered by similarity (best first).
    """
    key = artist_name.strip().lower()

    # Auto-build if missing
    if key not in _index_cache:
        logger.info("Index not found for '%s' – building now …", artist_name)
        ok = build_artist_index(artist_name)
        if not ok:
            logger.warning("Cannot search — no index for '%s'.", artist_name)
            return []

    idx = _index_cache[key]
    k_actual = min(k, len(idx.lines))

    if k_actual == 0:
        return []

    # ── Encode query ─────────────────────────────────────────────────
    model = _get_model()
    q_vec: np.ndarray = model.encode(
        [query],
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    # Combine with style_embedding if available
    if style_embedding is not None:
        style_vec = np.array([style_embedding], dtype=np.float32)
        # 60% query topic, 40% artist style
        q_vec = 0.6 * q_vec + 0.4 * style_vec
        # Re-normalize
        norm = np.linalg.norm(q_vec, axis=1, keepdims=True)
        q_vec = q_vec / norm

    # ── kNN search ───────────────────────────────────────────────────
    # NearestNeighbors was fit with n_neighbors=min(50, corpus_len)
    # so we cap k_actual at that value.
    k_query = min(k_actual, idx.nn.n_neighbors)
    distances, indices = idx.nn.kneighbors(q_vec, n_neighbors=k_query)

    results: List[str] = []
    for i, dist in zip(indices[0], distances[0]):
        results.append(idx.lines[i])

    logger.info(
        "🔎 Semantic search for '%s' → %d results (best_dist=%.3f)",
        query[:50], len(results),
        float(distances[0][0]) if len(distances[0]) > 0 else -1,
    )

    return results


def search_multi_query(
    queries: List[str],
    artist_name: str,
    k_per_query: int = 10,
    total_k: int = 30,
    style_embedding: Optional[List[float]] = None,
) -> List[str]:
    """
    Search for multiple queries simultaneously, deduplicate results,
    and return up to *total_k* unique lines.

    Useful when the prompt has multiple themes — each theme contributes
    its top matches, then duplicates are removed.
    """
    seen: set = set()
    results: List[str] = []

    for q in queries:
        hits = search_similar_lines(q, artist_name, k=k_per_query, style_embedding=style_embedding)
        for line in hits:
            if line not in seen:
                seen.add(line)
                results.append(line)
            if len(results) >= total_k:
                break
        if len(results) >= total_k:
            break

    logger.info(
        "🔎 Multi-query search (%d queries) → %d unique results",
        len(queries), len(results),
    )
    return results[:total_k]


# ── Cache management ─────────────────────────────────────────────────────

def is_indexed(artist_name: str) -> bool:
    """Check whether an artist already has an in-memory index."""
    return artist_name.strip().lower() in _index_cache


def get_index_stats(artist_name: str) -> Optional[Dict[str, Any]]:
    """Return basic stats about a cached index (or None if not cached)."""
    key = artist_name.strip().lower()
    idx = _index_cache.get(key)
    if idx is None:
        return None
    return {
        "artist": idx.artist_name,
        "lines": len(idx.lines),
        "embedding_dim": idx.embeddings.shape[1],
    }


def clear_cache() -> None:
    """Drop all cached indexes (useful for tests / hot-reload)."""
    _index_cache.clear()
    logger.info("Vector index cache cleared.")
