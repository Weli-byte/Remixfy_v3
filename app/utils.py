"""
Shared utility helpers used across the application.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_json(path: str | Path) -> Any:
    """
    Load and parse a JSON file.

    Parameters
    ----------
    path : str | Path
        Absolute or relative path to the JSON file.

    Returns
    -------
    Any
        Parsed JSON content (usually a dict or list).

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    logger.debug("Loaded JSON from %s (%d top-level items)", file_path, len(data) if isinstance(data, (list, dict)) else 1)
    return data


def sanitize_text(text: str) -> str:
    """
    Clean up generated text by stripping leading/trailing whitespace,
    collapsing multiple blank lines, and removing stray control characters.
    """
    lines = text.strip().splitlines()
    cleaned: list[str] = []
    prev_blank = False
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(stripped)
            prev_blank = False
    return "\n".join(cleaned)


def truncate(text: str, max_length: int = 500, suffix: str = "…") -> str:
    """Return *text* truncated to *max_length* characters with a suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def count_bars(text: str) -> int:
    """Count the number of non-empty lines (bars) in a block of lyrics."""
    return sum(1 for line in text.strip().splitlines() if line.strip())
