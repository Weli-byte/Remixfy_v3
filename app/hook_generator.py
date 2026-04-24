"""
Hook Generator – Creates short, catchy hook lines for the CHORUS.

Step 1: Analyse the artist's corpus for short-line patterns (≤4 words).
Step 2: Extract the most common word structures.
Step 3: Use LLM to generate a concise, memorable hook (2-4 words).
Step 4: Inject the hook into the CHORUS section.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)


# ── Corpus analysis (pure Python) ───────────────────────────────────────

def _extract_short_patterns(corpus: List[str], max_words: int = 4) -> List[str]:
    """Return short lines (≤ *max_words*) from the corpus."""
    short: List[str] = []
    for line in corpus:
        stripped = line.strip()
        if stripped and len(stripped.split()) <= max_words:
            short.append(stripped)
    return short


def _top_word_structures(short_lines: List[str], top_n: int = 5) -> List[str]:
    """
    Find the most frequent word-length patterns in short lines.

    Example pattern: "3-2" means a 3-letter word followed by a 2-letter word.
    """
    patterns: Counter[str] = Counter()
    for line in short_lines:
        words = line.strip().split()
        pattern = "-".join(str(len(w)) for w in words)
        patterns[pattern] += 1

    return [p for p, _ in patterns.most_common(top_n)]


def _top_keywords(short_lines: List[str], top_n: int = 8) -> List[str]:
    """Extract the most common words from short lines."""
    word_counter: Counter[str] = Counter()
    for line in short_lines:
        for word in line.strip().split():
            clean = re.sub(r"[^\w]", "", word).lower()
            if clean and len(clean) > 1:
                word_counter[clean] += 1
    return [w for w, _ in word_counter.most_common(top_n)]


# ── Hook generation (uses LLM) ──────────────────────────────────────────

def generate_hook(
    artist_name: str,
    corpus: List[str],
    *,
    call_llm_fn: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    """
    Generate a short, catchy hook based on the artist's corpus patterns.

    Parameters
    ----------
    artist_name : str
    corpus      : list[str]  – the artist's lyrics_corpus
    call_llm_fn : callable   – function(prompt: str) -> str
                               If None, hook generation is skipped.

    Returns
    -------
    str | None – A 2-4 word hook line, or None if generation fails.
    """
    if not corpus:
        logger.info("No corpus for '%s' – skipping hook generation.", artist_name)
        return None

    short_lines = _extract_short_patterns(corpus, max_words=4)

    if len(short_lines) < 3:
        logger.info("Too few short lines for '%s' – skipping hook.", artist_name)
        return None

    keywords = _top_keywords(short_lines)
    structures = _top_word_structures(short_lines)

    prompt = (
        f"Sen Türkçe rap/hip-hop hook yazarısın.\n"
        f"Sanatçı stili: {artist_name}\n\n"
        f"Corpustan çıkarılan sık kelimeler: {', '.join(keywords)}\n"
        f"Tipik satır yapıları (harf-sayısı): {', '.join(structures)}\n\n"
        f"GÖREV:\n"
        f"- Kısa ve tekrar edilebilir bir hook üret.\n"
        f"- TAM OLARAK 2-4 kelime.\n"
        f"- Akılda kalıcı, vurucu, ritmik.\n"
        f"- Sadece hook'u yaz. Açıklama YAZMA.\n"
    )

    if call_llm_fn is None:
        logger.info("No LLM function provided – skipping hook generation.")
        return None

    try:
        raw = call_llm_fn(prompt)
        hook = raw.strip().splitlines()[0].strip()  # first line only

        # Sanity: must be 2-6 words (2-4 ideal but allow slight overflow)
        wc = len(hook.split())
        if wc < 2 or wc > 6:
            logger.warning("Hook word count (%d) out of range – discarding.", wc)
            return None

        logger.info("🎣 Generated hook for '%s': %s", artist_name, hook)
        return hook

    except Exception as exc:
        logger.warning("Hook generation failed: %s", exc)
        return None


# ── Chorus injection ─────────────────────────────────────────────────────

def inject_hook_into_chorus(text: str, hook: str) -> str:
    """
    Replace the first line of the CHORUS section with the generated hook.

    If the CHORUS section is not found, return the text unchanged.
    """
    lines = text.splitlines()
    result: List[str] = []
    in_chorus = False
    chorus_first_replaced = False

    for line in lines:
        if line.strip().upper() == "[CHORUS]":
            in_chorus = True
            result.append(line)
            continue

        if in_chorus and not chorus_first_replaced and line.strip():
            result.append(hook)
            chorus_first_replaced = True
            logger.info("🎣 Hook injected into CHORUS: %s", hook)
            continue

        # Reset section flag on next section tag
        if line.strip().upper().startswith("[") and in_chorus:
            in_chorus = False

        result.append(line)

    return "\n".join(result)
