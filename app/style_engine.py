"""
Style Engine – loads the artist catalogue and exposes query functions
for genre, era, artist, and profile lookups.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings
from app.utils import load_json

logger = logging.getLogger(__name__)

# ── Module-level cache ───────────────────────────────────────────────────
_catalogue: list[dict[str, Any]] | None = None


def _load_catalogue() -> list[dict[str, Any]]:
    """Load the full artist catalogue from ``data/artists.json`` (cached)."""
    global _catalogue  # noqa: PLW0603
    if _catalogue is not None:
        return _catalogue

    settings = get_settings()
    path = Path(settings.artists_json_path)
    _catalogue = load_json(path)
    logger.info("Style engine loaded %d artists from %s.", len(_catalogue), path)
    return _catalogue


# ── Public API ───────────────────────────────────────────────────────────


def get_genres() -> list[str]:
    """Return a sorted list of unique genres available in the catalogue."""
    catalogue = _load_catalogue()
    return sorted({artist["genre"] for artist in catalogue})


def get_eras_by_genre(genre: str) -> list[str]:
    """
    Return a sorted list of eras available for the given *genre*.

    Returns an empty list when the genre does not exist.
    """
    genre_lower = genre.strip().lower()
    catalogue = _load_catalogue()
    eras = {
        artist["era"]
        for artist in catalogue
        if artist["genre"].lower() == genre_lower
    }
    if not eras:
        logger.warning("No eras found for genre '%s'.", genre)
    return sorted(eras)


def get_artists(genre: str, era: str) -> list[str]:
    """
    Return a sorted list of artist names matching *genre* **and** *era*.

    Returns an empty list when the combination yields no results.
    """
    genre_lower = genre.strip().lower()
    era_lower = era.strip().lower()
    catalogue = _load_catalogue()
    names = sorted(
        artist["name"]
        for artist in catalogue
        if artist["genre"].lower() == genre_lower
        and artist["era"].lower() == era_lower
    )
    if not names:
        logger.warning("No artists found for genre='%s', era='%s'.", genre, era)
    return names


def get_artist_profile(artist_name: str) -> Optional[dict[str, Any]]:
    """
    Look up an artist by name (case-insensitive) and return the full
    entry including ``dna``.

    Returns ``None`` if the artist is not found.
    """
    name_lower = artist_name.strip().lower()
    catalogue = _load_catalogue()
    for artist in catalogue:
        if artist["name"].lower() == name_lower:
            return artist
    logger.warning("Artist '%s' not found in catalogue.", artist_name)
    return None


def build_style_prompt_fragment(artist_name: str) -> str:
    """
    Build a natural-language fragment describing the requested artist's
    style. Falls back to a generic prompt when the artist is unknown.
    """
    artist = get_artist_profile(artist_name)
    if artist is None:
        return f"Write in a style inspired by {artist_name}."

    dna = artist.get("dna", {})
    mechanics = dna.get("mechanics", {})
    themes = ", ".join(dna.get("theme_bias", []))

    parts = [f"Write in the style of {artist['name']}."]
    if themes:
        parts.append(f"Themes: {themes}.")
    for k, v in mechanics.items():
        if v:
            parts.append(f"{k}: {v}")

    return " ".join(parts)


def list_available_artists() -> list[str]:
    """Return a sorted list of all artist names in the catalogue."""
    catalogue = _load_catalogue()
    return sorted(artist["name"] for artist in catalogue)


def reset_cache() -> None:
    """Clear the in-memory catalogue cache (useful for tests / hot-reload)."""
    global _catalogue  # noqa: PLW0603
    _catalogue = None
