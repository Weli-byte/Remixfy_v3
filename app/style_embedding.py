"""
Artist Style Embedding Engine – Learns the dense style vector for an artist.

Calculates the average embedding of all lines in the artist's lyrics_corpus
using sentence-transformers ('all-MiniLM-L6-v2').

Embeddings are saved to data/style_embeddings.json.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Re-use the lazy-loaded model from vector_store to avoid loading twice
try:
    from app.vector_store import _get_model
except ImportError:
    # Fallback if vector_store is not available for some reason
    _model = None
    def _get_model():
        global _model
        if _model is None:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        return _model

try:
    from app.flow_analyzer import get_corpus_for_artist
except ImportError:
    def get_corpus_for_artist(artist_name: str) -> List[str]:
        return []

_EMBEDDINGS_PATH = Path(__file__).resolve().parent.parent / "data" / "style_embeddings.json"


def build_artist_embedding(artist_name: str) -> Optional[List[float]]:
    """
    Computes and saves the average style embedding for an artist.
    Returns the vector as a list of floats.
    """
    corpus = get_corpus_for_artist(artist_name)
    lines = [l.strip() for l in corpus if l.strip()]

    if not lines:
        logger.warning("No corpus lines for '%s' – cannot build style embedding.", artist_name)
        return None

    model = _get_model()
    
    logger.info("Computing style embedding for '%s' (%d lines) ...", artist_name, len(lines))
    embeddings = model.encode(
        lines,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    # Average the embeddings to get a single style vector
    avg_embedding = np.mean(embeddings, axis=0)
    
    # Normalize the average vector (important for cosine similarity)
    norm = np.linalg.norm(avg_embedding)
    if norm > 0:
        avg_embedding = avg_embedding / norm

    # Convert to standard Python float list
    style_vector = avg_embedding.tolist()

    # Save to JSON
    _save_embedding_to_file(artist_name, style_vector)
    
    logger.info("✅ Style embedding built for '%s'.", artist_name)
    return style_vector


def get_artist_embedding(artist_name: str) -> Optional[List[float]]:
    """
    Loads the style embedding for an artist from disk.
    If not found, builds it on the fly.
    """
    if _EMBEDDINGS_PATH.exists():
        try:
            with open(_EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if artist_name in data:
                    return data[artist_name]
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read style_embeddings.json")

    # If we fall through, compute and save
    logger.info("Style embedding not found for '%s', building now...", artist_name)
    return build_artist_embedding(artist_name)


def _save_embedding_to_file(artist_name: str, embedding: List[float]) -> None:
    """Helper to save the embedding to the JSON dictionary file."""
    data = {}
    if _EMBEDDINGS_PATH.exists():
        try:
            with open(_EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    data[artist_name] = embedding

    # Create directory if it doesn't exist
    _EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(_EMBEDDINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
