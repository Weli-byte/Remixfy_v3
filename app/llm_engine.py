"""
LLM Engine – OpenAI Chat Completions API wrapper (gpt-4.1).

Artist Style Engine pipeline (self-contained):
  ARTIST STYLE EMBEDDING → PERSONA ENGINE → NEURAL FLOW ENGINE → BEAT EMPHASIS ENGINE → DELIVERY ENGINE → STAGE ENERGY ENGINE → AUDIENCE HOOK ENGINE → BPM PROFILE → FLOW ANALYSIS → VECTOR RETRIEVAL → FLOW PATTERN EXTRACTOR → FLOW CLUSTERING → BAR STRUCTURE ENGINE → EMOTION CURVE ENGINE → PUNCHLINE ENGINE → MULTI RHYME ENGINE → PROMPT BUILD →
  LLM GENERATION → RHYME VALIDATION → NEURAL RHYME ENGINE → RHYME QUALITY ENGINE → SYLLABLE RHYTHM CHECK → BEAT GRID ALIGNMENT → HOOK GENERATION → FINAL OUTPUT
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.beat_grid_engine import validate_beat_alignment
from app.flow_analyzer import analyze_flow_patterns, get_corpus_for_artist
from app.hook_generator import generate_hook, inject_hook_into_chorus
from app.neural_rhyme_engine import validate_neural_rhyme_from_text
from app.phonetic_rhyme import validate_rhyme_from_text
from app.prompt_builder import build_prompt
from app.rhyme_quality_engine import validate_rhyme_quality
from app.syllable_analyzer import analyze_rhythm_from_text

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = 2
_MODEL = "gpt-4.1"

_OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
_ARTISTS_PATH = Path(__file__).resolve().parent.parent / "data" / "artists.json"

_client: Optional[OpenAI] = None


# ── Result dataclass (used by FastAPI route) ─────────────────────────────

@dataclass
class LLMResult:
    """Structured result returned by the async ``generate`` function."""
    text: str
    model: str = _MODEL
    prompt_tokens: int = 0
    completion_tokens: int = 0


# ── Expected structure ───────────────────────────────────────────────────

# Section order: VERSE1(12) → CHORUS(8) → VERSE2(12) → BRIDGE(4) → CHORUS(8)
_EXPECTED_STRUCTURE = [
    ("[VERSE 1]", 12),
    ("[CHORUS]",   8),
    ("[VERSE 2]", 12),
    ("[BRIDGE]",   4),
    ("[CHORUS]",   8),
]
_TOTAL_LYRIC_LINES = 44


# ── Validation (44-line structure: 12+8+12+4+8) ──────────────────────────

def _validate_structure(text: str) -> tuple:
    """
    Enforce 12+8+12+4+8 structure (44 lyric lines, 5 tags).
    """
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    # Parse sections in order
    sections: list = []  # list of (tag, [content_lines])
    current_tag: Optional[str] = None
    current_lines: list = []

    for line in lines:
        upper = line.upper()
        if upper in ("[VERSE 1]", "[CHORUS]", "[VERSE 2]", "[BRIDGE]"):
            if current_tag is not None:
                sections.append((current_tag, current_lines))
            current_tag = upper
            current_lines = []
        elif current_tag is not None:
            current_lines.append(line)

    if current_tag is not None:
        sections.append((current_tag, current_lines))

    # We expect exactly 5 sections
    if len(sections) < 5:
        return False, f"Expected 5 sections, got {len(sections)}"

    # Validate each section's line count
    expected = _EXPECTED_STRUCTURE
    for i, (exp_tag, exp_count) in enumerate(expected):
        if i >= len(sections):
            return False, f"Missing section {exp_tag} (#{i+1})"
        actual_tag, actual_lines = sections[i]
        if actual_tag != exp_tag:
            return False, f"Section #{i+1}: expected {exp_tag}, got {actual_tag}"
        if len(actual_lines) != exp_count:
            return False, (
                f"{actual_tag} (#{i+1}): expected {exp_count} lines, "
                f"got {len(actual_lines)}"
            )

    return True, "OK"


# ── Helpers ──────────────────────────────────────────────────────────────

def _get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file or "
            "export it as an environment variable."
        )

    _client = OpenAI(api_key=api_key)
    logger.info("OpenAI client ready – model=%s", _MODEL)
    return _client


def _clean_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name)
    cleaned = re.sub(r"[\s]+", "_", cleaned.strip())
    return cleaned.lower()


def _save_output(text: str, artist_name: str) -> Path:
    _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_name = _clean_filename(artist_name)
    filename = f"{safe_name}_{timestamp}.txt"
    filepath = _OUTPUTS_DIR / filename
    filepath.write_text(text, encoding="utf-8")
    logger.info("Lyrics saved → %s", filepath)
    return filepath


def _load_corpus(artist_name: str) -> List[str]:
    """Load lyrics_corpus for an artist from artists.json."""
    return get_corpus_for_artist(artist_name)


# ── Core LLM call ────────────────────────────────────────────────────────

def call_llm(prompt: str) -> str:
    """Single GPT-4.1 Chat Completions call with retry logic."""
    client = _get_client()

    last_error: Optional[Exception] = None
    backoff = _RETRY_BACKOFF

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.debug("Request [%d/%d] model=%s", attempt, _MAX_RETRIES, _MODEL)

            response = client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Generate the lyrics now."},
                ],
                temperature=0.85,
                top_p=0.95,
                frequency_penalty=0.6,
                presence_penalty=0.3,
                max_tokens=2500,
            )

            text = response.choices[0].message.content

            if not text or not text.strip():
                raise RuntimeError("GPT-4.1 returned empty text.")

            clean = text.strip()

            if response.usage:
                logger.info(
                    "Tokens – prompt: %d, completion: %d, total: %d",
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    response.usage.total_tokens,
                )

            logger.info("Response: %d chars (attempt %d).", len(clean), attempt)
            return clean

        except Exception as exc:
            last_error = exc
            logger.warning("Attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc)
            if attempt < _MAX_RETRIES:
                logger.info("Retrying in %ds …", backoff)
                time.sleep(backoff)
                backoff *= 2

    raise RuntimeError(
        f"All {_MAX_RETRIES} attempts failed. Last error: {last_error}"
    )


# ── Public API: Synchronous pipeline (CLI / test_generate) ──────────────

def generate_text(
    prompt: str,
    *,
    artist_name: str = "unknown",
    genre: str = "rap",
    bpm: int = 120,
    boost: bool = True,
    mechanics: Optional[dict] = None,
    bar_structure: Optional[Dict[str, int]] = None,
) -> str:
    """
    Artist Style Engine Pipeline (self-contained):
      1) LLM Generation
      2) Structure validation
      3) Phonetic rhyme validation → retry if failed
      3.5) Neural Rhyme Engine → retry if failed
      3.8) Rhyme Quality Engine → retry if failed
      4) Syllable rhythm validation → retry if failed
      4.5) Beat Grid Alignment → retry if failed
      5) Hook generation → inject into chorus
      6) Save & return
    """
    
    struc_str = "(12+8+12+4+8 = 44 satır)"
    if bar_structure:
        struc_str = f"({bar_structure.get('verse1_bars', 12)}+{bar_structure.get('chorus_bars', 8)}+{bar_structure.get('verse2_bars', 12)}+{bar_structure.get('bridge_bars', 4)}+{bar_structure.get('final_chorus_bars', 8)} = {bar_structure.get('total_bars', 44)} satır)"

    # ── Step 1: Generate ─────────────────────────────────────────────
    logger.info("📝 Step 1: Generating lyrics …")
    text = call_llm(prompt)

    # ── Step 2: Structure check ──────────────────────────────────────
    logger.info("📐 Step 2: Structure validation …")
    is_valid, reason = _validate_structure(text)
    if is_valid:
        logger.info("✅ Structure validation passed %s.", struc_str)
    else:
        logger.warning("⚠️ Structure note: %s — proceeding.", reason)

    # ── Step 3: Phonetic rhyme validation → retry if failed ──────────
    logger.info("🎵 Step 3: Phonetic rhyme validation …")
    rhyme_ok, rhyme_msg = validate_rhyme_from_text(text)

    if rhyme_ok:
        logger.info("✅ Phonetic rhyme passed: %s", rhyme_msg)
    else:
        logger.warning("⚠️ Rhyme weak: %s — retrying once …", rhyme_msg)

        retry_prompt = (
            f"{prompt}\n\n"
            f"ÖNEMLİ: Önceki üretimde kafiye yoğunluğu düşüktü ({rhyme_msg}).\n"
            f"Bu sefer daha güçlü kafiyeler kullan. Satır sonlarında uyak yap.\n"
            f"Yapıyı {struc_str} kesinlikle koru.\n"
            f"Her satır 6-11 kelime."
        )
        retried = call_llm(retry_prompt)

        retry_struct_ok, _ = _validate_structure(retried)
        retry_rhyme_ok, retry_rhyme_msg = validate_rhyme_from_text(retried)

        if retry_struct_ok and retry_rhyme_ok:
            logger.info("✅ Retry improved rhyme: %s", retry_rhyme_msg)
            text = retried
        elif retry_struct_ok:
            logger.info("⚠️ Retry rhyme still weak but structure OK — using retry.")
            text = retried
        else:
            logger.warning("⚠️ Retry broke structure — keeping original.")

    # ── Step 3.5: Neural Rhyme Engine validation → retry if failed ───
    logger.info("🧠 Step 3.5: Neural Rhyme Engine validation …")
    neural_rhyme_ok = validate_neural_rhyme_from_text(text)
    
    if neural_rhyme_ok:
        logger.info("✅ Neural rhyme passed.")
    else:
        logger.warning("⚠️ Neural rhyme weak — retrying once …")

        neural_retry_prompt = (
            f"{prompt}\n\n"
            f"ÖNEMLİ: Rap kafiyesi yeterince güçlü değil.\n"
            f"Satır sonlarında fonetik uyum ve çoklu kafiye kullan.\n"
            f"Yapıyı {struc_str} kesinlikle koru.\n"
        )
        retried_n = call_llm(neural_retry_prompt)

        retry_struct_ok_n, _ = _validate_structure(retried_n)
        retry_neural_ok = validate_neural_rhyme_from_text(retried_n)

        if retry_struct_ok_n and retry_neural_ok:
            logger.info("✅ Retry improved neural rhyme.")
            text = retried_n
        elif retry_struct_ok_n:
            logger.info("⚠️ Retry neural rhyme still weak but structure OK — using retry.")
            text = retried_n
        else:
            logger.warning("⚠️ Retry broke structure — keeping original.")

    # ── Step 3.8: Rhyme Quality Engine ───────────────────────────────
    logger.info("💎 Step 3.8: Rhyme Quality Engine validation …")
    quality_status = validate_rhyme_quality(text.split("\n"))
    
    if quality_status == "RHYME_OK":
        logger.info("✅ Rhyme Quality passed (Good density & internal rhymes).")
    else:
        logger.warning("⚠️ Rhyme Quality weak — retrying once …")
        
        quality_retry_prompt = (
            f"{prompt}\n\n"
            f"ÖNEMLİ: Rap kafiyesi zayıf. Daha güçlü multi-syllable rhyme kullan.\n"
            f"Satır sonlarında uyak sayısını ve yoğunluğunu artır.\n"
            f"Satır içlerinde de kafiye (internal rhyme) kullan.\n"
            f"Yapıyı {struc_str} kesinlikle koru."
        )
        retried_q = call_llm(quality_retry_prompt)
        
        retry_struct_ok_q, _ = _validate_structure(retried_q)
        retry_quality_status = validate_rhyme_quality(retried_q.split("\n"))
        
        if retry_struct_ok_q and retry_quality_status == "RHYME_OK":
            logger.info("✅ Retry improved rhyme quality.")
            text = retried_q
        elif retry_struct_ok_q:
            logger.info("⚠️ Retry rhyme quality still weak but structure OK — using retry.")
            text = retried_q
        else:
            logger.warning("⚠️ Retry broke structure on quality check — keeping original.")

    # ── Step 4: Syllable rhythm validation → retry if failed ────────
    logger.info("🪘 Step 4: Syllable rhythm validation (BPM: %d) …", bpm)
    rhythm_result = analyze_rhythm_from_text(text, bpm=bpm)
    logger.info(
        "📊 Rhythm stats: avg_syllables=%.1f, score=%.0f%%, in_range(8-14)=%d/%d",
        rhythm_result["avg_syllables"],
        rhythm_result["rhythm_score"] * 100,
        rhythm_result["in_range_count"],
        rhythm_result["total_lines"],
    )

    if rhythm_result["rhythm_valid"]:
        logger.info("✅ Rhythm passed: %s", rhythm_result["message"])
    else:
        logger.warning("⚠️ Rhythm irregular: %s — retrying once …", rhythm_result["message"])

        rhythm_retry_prompt = (
            f"{prompt}\n\n"
            f"ÖNEMLİ: Rap ritmi BPM ile uyumsuz ({rhythm_result['message']}).\n"
            f"Rap ritmi BPM ile uyumsuz. Satırların hece sayısını tempo ile uyumlu yaz.\n"
            f"Yapıyı {struc_str} kesinlikle koru."
        )
        retried_r = call_llm(rhythm_retry_prompt)

        retry_struct_ok_r, _ = _validate_structure(retried_r)
        retry_rhythm = analyze_rhythm_from_text(retried_r, bpm=bpm)

        if retry_struct_ok_r and retry_rhythm["rhythm_valid"]:
            logger.info("✅ Retry improved rhythm: %s", retry_rhythm["message"])
            text = retried_r
        elif retry_struct_ok_r:
            logger.info("⚠️ Retry rhythm still weak but structure OK — using retry.")
            text = retried_r
        else:
            logger.warning("⚠️ Retry broke structure — keeping original.")

    # ── Step 4.5: Beat Grid Alignment Engine ─────────────────────────
    logger.info("📏 Step 4.5: Beat Grid Alignment validation (BPM: %d) …", bpm)
    beat_alignment = validate_beat_alignment(text.split("\n"), bpm)
    
    if beat_alignment["valid"]:
        logger.info("✅ Beat alignment passed (ratio: %.2f).", beat_alignment["ratio"])
    else:
        logger.warning("⚠️ Beat alignment weak (ratio: %.2f) — retrying once …", beat_alignment["ratio"])
        
        beat_retry_prompt = (
            f"{prompt}\n\n"
            f"ÖNEMLİ: Satırların ritmi beat temposuna uymuyor.\n"
            f"BPM'e uygun hece sayıları kullan.\n"
            f"Yapıyı {struc_str} kesinlikle koru."
        )
        retried_b = call_llm(beat_retry_prompt)
        
        retry_struct_ok_b, _ = _validate_structure(retried_b)
        retry_beat_alignment = validate_beat_alignment(retried_b.split("\n"), bpm)
        
        if retry_struct_ok_b and retry_beat_alignment["valid"]:
            logger.info("✅ Retry improved beat alignment.")
            text = retried_b
        elif retry_struct_ok_b:
            logger.info("⚠️ Retry beat alignment still weak but structure OK — using retry.")
            text = retried_b
        else:
            logger.warning("⚠️ Retry broke structure on beat alignment — keeping original.")

    # ── Step 5: Hook generation & injection ──────────────────────────
    if boost:
        logger.info("🎣 Step 5: Hook generation …")
        corpus = _load_corpus(artist_name)

        hook = generate_hook(
            artist_name=artist_name,
            corpus=corpus,
            call_llm_fn=call_llm,
        )

        if hook:
            injected = inject_hook_into_chorus(text, hook)
            logger.info("✅ Hook injected into chorus.")
            text = injected
        else:
            logger.info("ℹ️ No hook generated — skipping injection.")
    else:
        logger.info("ℹ️ Step 5: Hook generation skipped (boost=False).")

    # ── Step 6: Save & return ────────────────────────────────────────
    logger.info("💾 Step 6: Saving output …")
    _save_output(text, artist_name)

    return text


# ── Public API: Full self-contained pipeline ─────────────────────────────

def generate_full_pipeline(
    artist_profile: Dict[str, Any],
    genre: str,
    era: str,
    themes: List[str],
    emotion_level: int,
    *,
    bpm: int = 120,
    boost: bool = True,
) -> str:
    """
    Complete Artist Style Engine pipeline — from raw inputs to final lyrics.

    ARTIST STYLE EMBEDDING → PERSONA ENGINE → NEURAL FLOW ENGINE → BEAT EMPHASIS ENGINE → DELIVERY ENGINE → STAGE ENERGY ENGINE → AUDIENCE HOOK ENGINE → BPM PROFILE → FLOW ANALYSIS → VECTOR RETRIEVAL → FLOW PATTERN EXTRACTOR → FLOW CLUSTERING → BAR STRUCTURE ENGINE → EMOTION CURVE ENGINE → PUNCHLINE ENGINE → MULTI RHYME ENGINE → PROMPT BUILD →
    LLM GENERATION → RHYME VALIDATION → NEURAL RHYME ENGINE → RHYME QUALITY ENGINE → SYLLABLE RHYTHM CHECK → BEAT GRID ALIGNMENT → HOOK GENERATION → FINAL OUTPUT

    This is the recommended entry point for new consumers.
    """
    name = artist_profile.get("name", "unknown")

    # ── Step 0: Flow analysis ────────────────────────────────────────
    logger.info("🔍 Step 0: Flow analysis for '%s' …", name)
    flow_profile = analyze_flow_patterns(name)
    logger.info(
        "✅ Flow profile: avg=%.1f, short=%.0f%%, pause=%s",
        flow_profile["avg_words"],
        flow_profile["short_ratio"] * 100,
        flow_profile["pause_style"],
    )

    # ── Step 0.5: Artist Style Embedding ─────────────────────────────
    style_embedding: Optional[List[float]] = None
    try:
        from app.style_embedding import get_artist_embedding
        logger.info("🎨 Step 0.5: Loading Artist Style Embedding for '%s' …", name)
        style_embedding = get_artist_embedding(name)
        if style_embedding:
            logger.info("✅ Style embedding loaded (dim=%d).", len(style_embedding))
    except ImportError:
        logger.info("ℹ️ style_embedding not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Style embedding failed: %s — skipping.", exc)

    # ── Step 0.8: Artist Persona Engine ──────────────────────────────
    persona_profile: Optional[Dict[str, Any]] = None
    try:
        from app.persona_engine import build_persona_profile
        logger.info("🗣️ Step 0.8: Extracting Artist Persona for '%s' …", name)
        persona_profile = build_persona_profile(name)
        if persona_profile:
            logger.info("✅ Persona extracted: %s (%s)", persona_profile.get("archetype"), persona_profile.get("tone"))
    except ImportError:
        logger.info("ℹ️ persona_engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Persona engine failed: %s — skipping.", exc)

    # ── Step 0.9: Neural Flow Engine ────────────────────────────────
    neural_flow_profile: Optional[Dict[str, Any]] = None
    try:
        from app.neural_flow_engine import build_flow_profile as build_neural_flow_profile
        logger.info("🌊 Step 0.9: Building Neural Flow Profile for '%s' …", name)
        neural_flow_profile = build_neural_flow_profile(name)
        logger.info(
            "✅ Neural flow profile: avg_syl=%.1f, pause=%.0f%%, pattern=%s",
            neural_flow_profile["avg_syllables"],
            neural_flow_profile["pause_ratio"] * 100,
            neural_flow_profile["dominant_pattern"]
        )
    except ImportError:
        logger.info("ℹ️ neural_flow_engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Neural flow engine failed: %s — skipping.", exc)

    # ── Step 1.0: Beat Emphasis Engine ───────────────────────────────
    beat_emphasis_profile: Optional[Dict[str, Any]] = None
    try:
        from app.beat_emphasis_engine import build_emphasis_profile
        logger.info("🥁 Step 1.0: Building Beat Emphasis Profile for '%s' …", name)
        beat_emphasis_profile = build_emphasis_profile(name)
        logger.info(
            "✅ Beat emphasis: pattern=%s, accents=%s",
            beat_emphasis_profile["dominant_pattern"],
            beat_emphasis_profile["accent_positions"]
        )
    except ImportError:
        logger.info("ℹ️ beat_emphasis_engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Beat emphasis engine failed: %s — skipping.", exc)

    # ── Step 1.1: Delivery Simulation Engine ───────────────────────────
    delivery_profile: Optional[Dict[str, Any]] = None
    try:
        from app.delivery_engine import build_delivery_profile
        logger.info("🎤 Step 1.1: Building Delivery Profile for '%s' …", name)
        delivery_profile = build_delivery_profile(name)
        logger.info(
            "✅ Delivery profile: pause=%.0f%%, breath=%d hece, style=%s",
            delivery_profile["pause_ratio"] * 100,
            delivery_profile["breath_interval"],
            delivery_profile["delivery_style"]
        )
    except ImportError:
        logger.info("ℹ️ delivery_engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Delivery engine failed: %s — skipping.", exc)

    # ── Step 1.2: Stage Energy Engine ───────────────────────────────
    stage_energy_profile: Optional[Dict[str, Any]] = None
    try:
        from app.stage_energy_engine import build_stage_energy_profile
        logger.info("⚡ Step 1.2: Building Stage Energy Profile …")
        stage_energy_profile = build_stage_energy_profile()
        logger.info("✅ Stage Energy Profile ready.")
    except ImportError:
        logger.info("ℹ️ stage_energy_engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Stage energy engine failed: %s — skipping.", exc)

    # ── Step 1.3: Audience Hook Engine ───────────────────────────────
    hook_profile: Optional[Dict[str, Any]] = None
    try:
        from app.audience_hook_engine import build_hook_profile
        logger.info("🎯 Step 1.3: Analyzing Audience Hook Profile for '%s' …", name)
        hook_profile = build_hook_profile(name)
        logger.info(
            "✅ Hook profile: pattern=%s, score=%.2f",
            hook_profile.get("pattern", "?"),
            hook_profile.get("hook_score", 0.0)
        )
    except ImportError:
        logger.info("ℹ️ audience_hook_engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Audience hook engine failed: %s — skipping.", exc)

    # ── Step 1: Vector retrieval ─────────────────────────────────────
    semantic_examples: Optional[List[str]] = None
    try:
        from app.vector_store import build_artist_index, search_multi_query

        logger.info("🔎 Step 1: Vector retrieval for '%s' …", name)
        idx_ok = build_artist_index(name)
        if idx_ok and themes:
            semantic_examples = search_multi_query(
                queries=themes,
                artist_name=name,
                k_per_query=10,
                total_k=30,
                style_embedding=style_embedding,
            )
            logger.info(
                "✅ Semantic retrieval: %d lines found for themes: %s",
                len(semantic_examples), ", ".join(themes[:4]),
            )
        elif idx_ok:
            # No themes — single query with artist name
            from app.vector_store import search_similar_lines
            semantic_examples = search_similar_lines(name, name, k=20, style_embedding=style_embedding)
            logger.info("✅ Semantic retrieval (generic): %d lines", len(semantic_examples))
        else:
            logger.info("ℹ️ No corpus index — will use random fallback.")
    except ImportError:
        logger.info("ℹ️ sentence-transformers not installed — skipping vector retrieval.")
    except Exception as exc:
        logger.warning("⚠️ Vector retrieval failed: %s — will use fallback.", exc)

    # ── Step 1.5: Flow pattern extractor v2 ────────────────────────
    flow_pattern_profile: Optional[Dict[str, Any]] = None
    try:
        from app.flow_pattern_extractor import build_flow_pattern_profile
        logger.info("🌊 Step 1.5: Flow Pattern Extractor for '%s' …", name)
        flow_pattern_profile = build_flow_pattern_profile(name)
        logger.info(
            "✅ Flow Pattern Extractor: break_style=%s, punchlines=%s",
            flow_pattern_profile["break_style"],
            flow_pattern_profile["punchline_positions"],
        )
    except ImportError:
        logger.info("ℹ️ Flow pattern extractor not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Flow pattern extractor failed: %s — skipping.", exc)

    # ── Step 2: Flow clustering ────────────────────────────────────
    flow_cluster_profile: Optional[Dict[str, Any]] = None
    try:
        from app.flow_cluster import build_flow_profile

        logger.info("🎯 Step 2: Flow clustering for '%s' …", name)
        flow_cluster_profile = build_flow_profile(name)
        logger.info(
            "✅ Flow cluster: dominant=%s (%.0f%%), secondary=%s, short_ratio=%.0f%%",
            flow_cluster_profile["dominant_flow"],
            flow_cluster_profile.get("flow_distribution", {}).get(
                flow_cluster_profile["dominant_flow"], 0) * 100,
            flow_cluster_profile["secondary_flow"],
            flow_cluster_profile["short_line_ratio"] * 100,
        )
    except ImportError:
        logger.info("ℹ️ sklearn not installed — skipping flow clustering.")
    except Exception as exc:
        logger.warning("⚠️ Flow clustering failed: %s — skipping.", exc)

    # ── Step 2.5: Bar Structure Engine ───────────────────────────────
    bar_structure: Optional[Dict[str, int]] = None
    try:
        from app.bar_structure_engine import build_bar_structure
        logger.info("📐 Step 2.5: Generating Bar Structure …")
        bar_structure = build_bar_structure()
        logger.info("✅ Bar structure ready: %d total lines", bar_structure["total_bars"])
    except ImportError:
        logger.info("ℹ️ Bar structure engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Bar structure engine failed: %s — skipping.", exc)

    # ── Step 2.7: Emotion Curve Engine ───────────────────────────────
    emotion_curve: Optional[Dict[str, str]] = None
    try:
        from app.emotion_curve_engine import build_emotion_curve
        logger.info("🎭 Step 2.7: Generating Emotion Curve …")
        theme_val = themes[0] if themes else "anlatım"
        emotion_curve = build_emotion_curve(theme=theme_val, emotion_level=emotion_level)
        logger.info("✅ Emotion curve ready.")
    except ImportError:
        logger.info("ℹ️ Emotion curve engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Emotion curve engine failed: %s — skipping.", exc)

    # ── Step 2.8: Punchline Engine ───────────────────────────────────
    punchline_slots: Optional[List[int]] = None
    try:
        from app.punchline_engine import detect_punchline_slots
        logger.info("🥊 Step 2.8: Generating Punchline Plan …")
        max_bars = bar_structure.get("verse1_bars", 12) if bar_structure else 12
        punchline_slots = detect_punchline_slots(max_bars)
        logger.info("✅ Punchline slots ready: %s", punchline_slots)
    except ImportError:
        logger.info("ℹ️ Punchline engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Punchline engine failed: %s — skipping.", exc)

    # ── Step 2.9: Multi Rhyme Generator Engine ───────────────────────
    multi_rhyme_bank: Optional[Dict[str, List[str]]] = None
    try:
        from app.multi_rhyme_engine import build_rhyme_bank
        logger.info("🎤 Step 2.9: Generating Multi Rhyme Bank Context …")
        multi_rhyme_bank = build_rhyme_bank(name)
        logger.info("✅ Multi rhyme bank initialized with %d patterns.", len(multi_rhyme_bank) if multi_rhyme_bank else 0)
    except ImportError:
        logger.info("ℹ️ Multi Rhyme Engine not found — skipping.")
    except Exception as exc:
        logger.warning("⚠️ Multi Rhyme Engine failed: %s — skipping.", exc)

    # ── Step 3: Prompt build ─────────────────────────────────────────
    logger.info("🏗️ Step 3: Building prompt …")
    prompt = build_prompt(
        artist_profile=artist_profile,
        genre=genre,
        era=era,
        themes=themes,
        emotion_level=emotion_level,
        flow_profile=flow_profile,
        flow_pattern_profile=flow_pattern_profile,
        flow_cluster_profile=flow_cluster_profile,
        semantic_examples=semantic_examples,
        style_embedding=style_embedding,
        bar_structure=bar_structure,
        emotion_curve=emotion_curve,
        punchline_slots=punchline_slots,
        multi_rhyme_bank=multi_rhyme_bank,
        persona_profile=persona_profile,
        neural_flow_profile=neural_flow_profile,
        beat_emphasis_profile=beat_emphasis_profile,
        delivery_profile=delivery_profile,
        stage_energy_profile=stage_energy_profile,
        hook_profile=hook_profile,
        bpm=bpm,
    )
    logger.info("✅ Prompt ready (%d chars)", len(prompt))

    # ── Steps 4-7: Generation pipeline ───────────────────────────────
    mechanics = artist_profile.get("dna", {}).get("mechanics", {})
    return generate_text(
        prompt=prompt,
        artist_name=name,
        genre=genre,
        bpm=bpm,
        boost=boost,
        mechanics=mechanics,
        bar_structure=bar_structure,
    )


# ── Public API: Async wrapper (FastAPI) ──────────────────────────────────

async def generate(
    messages: list,
    *,
    temperature: float = 0.85,
) -> LLMResult:
    """
    Async-compatible generation function for the FastAPI /remix endpoint.

    Accepts the OpenAI-style message list built by ``build_messages``.
    """
    client = _get_client()

    last_error: Optional[Exception] = None
    backoff = _RETRY_BACKOFF

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=_MODEL,
                messages=messages,
                temperature=temperature,
                top_p=0.95,
                frequency_penalty=0.6,
                presence_penalty=0.3,
                max_tokens=2500,
            )

            text = response.choices[0].message.content
            if not text or not text.strip():
                raise RuntimeError("GPT-4.1 returned empty text.")

            prompt_tokens = 0
            completion_tokens = 0
            if response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

            return LLMResult(
                text=text.strip(),
                model=_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        except Exception as exc:
            last_error = exc
            logger.warning("Attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc)
            if attempt < _MAX_RETRIES:
                time.sleep(backoff)
                backoff *= 2

    raise RuntimeError(
        f"All {_MAX_RETRIES} attempts failed. Last error: {last_error}"
    )


# ── Public API: Health check (FastAPI startup) ───────────────────────────

async def healthcheck() -> bool:
    """
    Quick connectivity check against the OpenAI API.
    Returns True if the API is reachable.
    """
    try:
        client = _get_client()
        # Minimal API call to verify connectivity
        client.models.list()
        return True
    except Exception as exc:
        logger.warning("Health check failed: %s", exc)
        return False
