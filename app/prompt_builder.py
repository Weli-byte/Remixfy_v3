"""
Prompt Builder – ARTIST DNA LOCK v3 + Artist Style Engine + Vector Retrieval

Integrates flow profile, flow cluster profile, semantic corpus retrieval,
and structural rules.
Song: 44 lines (12+8+12+4+8). Prompt < 8000 chars.

Reference lyrics are now selected via semantic similarity (vector search)
rather than random sampling, resulting in far more relevant examples.
"""

from __future__ import annotations

import json
import random
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.flow_analyzer import analyze_flow_patterns

logger = logging.getLogger(__name__)

_ARTISTS_PATH = Path(__file__).resolve().parent.parent / "data" / "artists.json"


# ── Retrieval (legacy – random fallback) ─────────────────────────────────

def get_lyrics_examples(artist_name: str, k: int = 15) -> List[str]:
    """
    Pull random sample lines from the artist's lyrics_corpus.

    .. deprecated::
        Use ``get_semantic_examples`` instead for theme-aware retrieval.
        This function is kept for backward compatibility and as a fallback
        when the vector store is unavailable.
    """
    try:
        with open(_ARTISTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    for a in data:
        if a["name"].lower() == artist_name.lower():
            corpus = a.get("lyrics_corpus", [])
            if not corpus:
                return []
            return random.sample(corpus, min(k, len(corpus)))
    return []


# ── Retrieval (new – semantic search) ────────────────────────────────────

def get_semantic_examples(
    artist_name: str,
    themes: List[str],
    k: int = 30,
) -> List[str]:
    """
    Retrieve the *k* most semantically similar corpus lines to *themes*.

    Falls back to random sampling if the vector store is unavailable
    (e.g. sentence-transformers not installed).
    """
    try:
        from app.vector_store import search_multi_query, build_artist_index

        # Ensure index exists (idempotent — no-op if already built)
        ok = build_artist_index(artist_name)
        if not ok:
            logger.info("Vector index empty for '%s' — falling back to random.", artist_name)
            return get_lyrics_examples(artist_name, k=min(k, 15))

        # Build query from themes
        theme_query = ", ".join(themes) if themes else artist_name
        results = search_multi_query(
            queries=themes if themes else [artist_name],
            artist_name=artist_name,
            k_per_query=max(10, k // max(len(themes), 1)),
            total_k=k,
        )

        if results:
            logger.info(
                "🔎 Semantic retrieval for '%s': %d lines (themes: %s)",
                artist_name, len(results), theme_query[:60],
            )
            return results

        # If search returned nothing, fall back
        return get_lyrics_examples(artist_name, k=min(k, 15))

    except ImportError:
        logger.warning(
            "sentence-transformers not installed — falling back to random retrieval."
        )
        return get_lyrics_examples(artist_name, k=min(k, 15))
    except Exception as exc:
        logger.warning("Semantic retrieval failed (%s) — falling back to random.", exc)
        return get_lyrics_examples(artist_name, k=min(k, 15))


# ── Flow profile formatter ──────────────────────────────────────────────

def _format_flow_block(flow: Dict[str, Any], flow_pattern: Optional[Dict[str, Any]] = None) -> str:
    """Format flow analysis results as a prompt section."""
    if not flow or flow.get("avg_words", 0) == 0:
        return ""

    lines = [
        "\nFLOW PROFİLİ (sanatçının yazım ritmi — buna yakın yaz):",
        f"- Ortalama kelime/satır: {flow['avg_words']}",
        f"- Kısa satır oranı (≤5 kelime): %{int(flow['short_ratio'] * 100)}",
        f"- Soru oranı: %{int(flow['question_ratio'] * 100)}",
        f"- Baskın ritim: {flow['pause_style']}",
    ]

    if flow.get("rhyme_endings"):
        lines.append(f"- Sık kafiye sonekleri: {', '.join(flow['rhyme_endings'][:4])}")

    if flow_pattern:
        lines.append(f"- Satır kırılım stili (break_style): {flow_pattern.get('break_style', 'balanced')}")
        punch = flow_pattern.get('punchline_positions', [4, 8])
        lines.append(f"- Punchline konumları: {punch}")
        punch_str = " veya ".join(map(str, punch))
        lines.append(f"Talimat: Punchline'ları genellikle satır {punch_str} civarında konumlandır.")

    lines.append("Satır uzunluklarını ve ritmi bu flow profiline yakın yaz.")

    return "\n".join(lines)


# ── Flow cluster profile formatter ──────────────────────────────────────

_FLOW_DESCRIPTIONS: Dict[str, str] = {
    "FLOW_A": "Kısa, konuşma tarzı satırlar (≤4 kelime). Hızlı ritim, kesik delivery.",
    "FLOW_B": "Soru cümleleriyle örülü satırlar. Dinleyiciyi içine çeker.",
    "FLOW_C": "Agresif, noktalama yoğun satırlar. Sert vurgular, punchline ağırlıklı.",
    "FLOW_D": "Uzun anlatımcı satırlar (≥8 kelime). Hikaye akışı, detaylı tasvir.",
}


def _format_flow_cluster_block(cluster_profile: Dict[str, Any]) -> str:
    """Format flow cluster profile as a prompt section."""
    if not cluster_profile or not cluster_profile.get("dominant_flow"):
        return ""

    dom = cluster_profile["dominant_flow"]
    sec = cluster_profile["secondary_flow"]
    dist = cluster_profile.get("flow_distribution", {})

    lines = [
        "\nFLOW CLUSTER PROFİLİ (corpus’tan çıkarılan flow tipleri):",
        f"- Dominant Flow: {dom} → {_FLOW_DESCRIPTIONS.get(dom, '')}",
        f"- Secondary Flow: {sec} → {_FLOW_DESCRIPTIONS.get(sec, '')}",
    ]

    if dist:
        dist_str = ", ".join(f"{k}: %{int(v*100)}" for k, v in dist.items())
        lines.append(f"- Dağılım: {dist_str}")

    lines.append("Şarkıyı bu flow tiplerine uygun yaz. "
                 f"Ağırlıklı olarak {dom} tarzı satırlar kullan.")

    return "\n".join(lines)


# ── Prompt Builder ───────────────────────────────────────────────────────

def build_prompt(
    artist_profile: Dict[str, Any],
    genre: str,
    era: str,
    themes: List[str],
    emotion_level: int,
    *,
    bpm: int = 120,
    flow_profile: Optional[Dict[str, Any]] = None,
    flow_pattern_profile: Optional[Dict[str, Any]] = None,
    flow_cluster_profile: Optional[Dict[str, Any]] = None,
    semantic_examples: Optional[List[str]] = None,
    style_embedding: Optional[List[float]] = None,
    bar_structure: Optional[Dict[str, int]] = None,
    emotion_curve: Optional[Dict[str, str]] = None,
    punchline_slots: Optional[List[int]] = None,
    multi_rhyme_bank: Optional[Dict[str, List[str]]] = None,
    persona_profile: Optional[Dict[str, Any]] = None,
    neural_flow_profile: Optional[Dict[str, Any]] = None,
    beat_emphasis_profile: Optional[Dict[str, Any]] = None,
    delivery_profile: Optional[Dict[str, Any]] = None,
    stage_energy_profile: Optional[Dict[str, Any]] = None,
    hook_profile: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build the system prompt for lyric generation.

    If *flow_profile* is not provided, it will be computed automatically
    by calling ``analyze_flow_patterns(artist_name)``.

    If *semantic_examples* is provided, they replace random retrieval.
    If not provided, semantic retrieval is attempted automatically.
    """
    name = artist_profile.get("name", "?")
    dna = artist_profile.get("dna", {})
    mechanics = dna.get("mechanics", {})

    # ── 0. Auto-compute flow profile if not supplied ─────────────────
    if flow_profile is None:
        logger.info("Flow profile not supplied – computing for '%s' …", name)
        flow_profile = analyze_flow_patterns(name)
        flow_profile["bpm"] = bpm

    if flow_pattern_profile is None:
        try:
            from app.flow_pattern_extractor import build_flow_pattern_profile
            flow_pattern_profile = build_flow_pattern_profile(name)
        except ImportError:
            pass

    if bar_structure is None:
        try:
            from app.bar_structure_engine import build_bar_structure
            bar_structure = build_bar_structure()
        except ImportError:
            # Fallback
            bar_structure = {
                "verse1_bars": 12, "chorus_bars": 8, "verse2_bars": 12,
                "bridge_bars": 4, "final_chorus_bars": 8, "total_bars": 44
            }

    if emotion_curve is None:
        try:
            from app.emotion_curve_engine import build_emotion_curve
            theme_val = themes[0] if themes else "anlatım"
            emotion_curve = build_emotion_curve(theme=theme_val, emotion_level=emotion_level)
        except ImportError:
            emotion_curve = {
                "verse1": "anlatım",
                "chorus": "duygu",
                "verse2": "ego",
                "bridge": "geçiş",
                "final_chorus": "zirve"
            }

    if punchline_slots is None:
        try:
            from app.punchline_engine import detect_punchline_slots
            # Predict slots using the primary verse length as maximum reference
            max_len = bar_structure.get("verse1_bars", 12) if bar_structure else 12
            punchline_slots = detect_punchline_slots(max_len)
        except ImportError:
            punchline_slots = [4, 8]

    if persona_profile is None:
        try:
            from app.persona_engine import build_persona_profile
            persona_profile = build_persona_profile(name)
        except ImportError:
            persona_profile = {}

    if neural_flow_profile is None:
        try:
            from app.neural_flow_engine import build_flow_profile
            neural_flow_profile = build_flow_profile(name)
        except ImportError:
            neural_flow_profile = {}

    if beat_emphasis_profile is None:
        try:
            from app.beat_emphasis_engine import build_emphasis_profile
            beat_emphasis_profile = build_emphasis_profile(name)
        except ImportError:
            beat_emphasis_profile = {}

    if delivery_profile is None:
        try:
            from app.delivery_engine import build_delivery_profile
            delivery_profile = build_delivery_profile(name)
        except ImportError:
            delivery_profile = {}

    if stage_energy_profile is None:
        try:
            from app.stage_energy_engine import build_stage_energy_profile
            stage_energy_profile = build_stage_energy_profile()
        except ImportError:
            stage_energy_profile = {}

    if hook_profile is None:
        try:
            from app.audience_hook_engine import build_hook_profile
            hook_profile = build_hook_profile(name)
        except ImportError:
            hook_profile = {}

    # ── 1. Core instructions (ALWAYS first — never truncated) ────────
    parts: List[str] = [
        "Sen profesyonel bir söz yazarısın.",
        "",
        "KRİTİK KURALLAR:",
        f'- "{name}" adını yazma. Kopya / çalıntı söz YASAK. Sadece Türkçe.',
        "- Açıklama, yorum, giriş cümlesi, markdown YAZMA.",
        "- Sadece şarkı sözlerini üret, başka HİÇBİR ŞEY yazma.",
        "",
        "YAPI (ZORUNLU):",
        "Şarkıyı bu bar yapısına göre yaz.",
        f"- [VERSE 1]  → ardından tam {bar_structure['verse1_bars']} satır söz",
        f"- [CHORUS]   → ardından tam {bar_structure['chorus_bars']} satır söz",
        f"- [VERSE 2]  → ardından tam {bar_structure['verse2_bars']} satır söz",
        f"- [BRIDGE]   → ardından tam {bar_structure['bridge_bars']} satır söz",
        f"- [CHORUS]   → ardından tam {bar_structure['final_chorus_bars']} satır söz (ilk CHORUS ile AYNI olacak)",
        f"- Toplam tam {bar_structure['total_bars']} satır söz + 5 etiket. Eksik veya fazla YASAK.",
        "- Çıktın SADECE [VERSE 1] etiketi ile başlamalı.",
        "",
        "SATIR UZUNLUĞU (ZORUNLU):",
        "- Her satır en az 6 kelime, en fazla 11 kelime içermeli.",
        "- Bu kuralın dışına ÇIKMA.",
        "",
        "KAFİYE KURALLARI:",
        "- Rap kafiyesi kullan. Satır sonlarında çok heceli (multi-syllable) kafiye tekrarları kullan.",
        "- Ardışık satırlarda kafiye yap (AABB veya ABAB).",
        "- Kafiye yoğunluğu yüksek olmalı.",
        "- Çoklu kafiye (multi rhyme) ve iç kafiye kullan.",
        "",
        "CHORUS KURALLARI:",
        "- CHORUS tekrar içermeli. 2 satır aynı olabilir.",
        "- Akılda kalıcı, kısa ve vurucu kalıplar kullan.",
        "- İkinci [CHORUS] birinci [CHORUS] ile BİREBİR AYNI olmalı.",
        "",
        "RİTİM KURALLARI:",
        "- Rap ritmini koru. Satırların hece sayıları birbirine yakın olsun.",
        "- Ritim tutarlılığı için satır uzunluklarını dengele.",
        "- Beat temposuna uygun rap ritmi kullan.",
        "- Satırların hece sayısı beat vuruşlarına uyumlu olsun.",
        "- Her satır yaklaşık bir ölçü sürmeli.",
        "",
        f"TÜR: {genre}  |  DÖNEM: {era}  |  DUYGU_SEVİYESİ: {emotion_level}/10",
    ]

    # ── 1b. BPM profile ──────────────────────────────────────────────
    try:
        from app.bpm_profile import get_bpm_profile, get_prompt_bpm_block
        parts.append("\n" + get_prompt_bpm_block(bpm))
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("BPM profile failed: %s", exc)

    # ── 1c. Persona profile ──────────────────────────────────────────
    if persona_profile:
        parts.append("\nSANATÇI PERSONASI")
        if "archetype" in persona_profile:
            parts.append(f"Archetype: {persona_profile['archetype']}")
        if "tone" in persona_profile:
            parts.append(f"Tone: {persona_profile['tone']}")
        if "themes" in persona_profile and persona_profile['themes']:
            parts.append(f"Themes: {persona_profile['themes']}")
        parts.append("Talimat: Şarkıyı bu karakter perspektifinden yaz.")

    # ── 1d. Neural Flow Profile ───────────────────────────────────
    if neural_flow_profile:
        try:
            from app.neural_flow_engine import format_flow_profile_block
            parts.append("\n" + format_flow_profile_block(neural_flow_profile))
        except ImportError:
            pass

    # ── 1e. Beat Emphasis Profile ─────────────────────────────────
    if beat_emphasis_profile:
        try:
            from app.beat_emphasis_engine import format_emphasis_block
            parts.append("\n" + format_emphasis_block(beat_emphasis_profile))
        except ImportError:
            pass

    # ── 1f. Delivery Profile ───────────────────────────────────────
    if delivery_profile:
        try:
            from app.delivery_engine import format_delivery_block
            parts.append("\n" + format_delivery_block(delivery_profile))
        except ImportError:
            pass

    # ── 1g. Stage Energy Profile ──────────────────────────────────
    if stage_energy_profile:
        try:
            from app.stage_energy_engine import format_stage_energy_block
            parts.append("\n" + format_stage_energy_block(stage_energy_profile))
        except ImportError:
            pass

    # ── 1h. Audience Hook Engine ──────────────────────────────────
    if hook_profile:
        pattern = hook_profile.get("pattern", "short slogan")
        hook_score = hook_profile.get("hook_score", 0.65)
        parts.append("\nHOOK TASARIM KURALLARI:")
        parts.append(f"Hedef nakarat tipi: {pattern}")
        parts.append(f"Hook Güç Skoru Hedefi: {int(hook_score * 100)}%")
        parts.append("- Nakarat akılda kalıcı olmalı.")
        parts.append("- Kısa slogan kalıpları kullan.")
        parts.append("- Bazı nakaratları tekrar et.")
        parts.append("- Dinleyicinin kolay söyleyebileceği hook yaz.")

    # ── 2. Flow profile ──────────────────────────────────────────────
    if flow_profile:
        flow_block = _format_flow_block(flow_profile, flow_pattern=flow_pattern_profile)
        if flow_block:
            parts.append(flow_block)

    # ── 2b. Flow cluster profile ───────────────────────────────────────
    if flow_cluster_profile is None:
        try:
            from app.flow_cluster import build_flow_profile
            flow_cluster_profile = build_flow_profile(name)
        except ImportError:
            pass
        except Exception as exc:
            logger.warning("Flow cluster profile failed: %s", exc)

    if flow_cluster_profile:
        cluster_block = _format_flow_cluster_block(flow_cluster_profile)
        if cluster_block:
            parts.append(cluster_block)

    # ── 2c. Emotion Curve ────────────────────────────────────────────
    if emotion_curve:
        try:
            from app.emotion_curve_engine import format_emotion_curve
            parts.append("\n" + format_emotion_curve(emotion_curve))
        except ImportError:
            pass

    # ── 2d. Punchline Engine ─────────────────────────────────────────
    if punchline_slots:
        try:
            from app.punchline_engine import format_punchline_slots
            parts.append("\n" + format_punchline_slots(punchline_slots))
        except ImportError:
            pass

    if mechanics:
        mech_lines = [f"- {mk}: {mv}" for mk, mv in mechanics.items() if mv]
        if mech_lines:
            parts.append("\nMEKANİKLER (STYLE MECHANICS):")
            parts.extend(mech_lines)

    # ── 3.8. Multi Rhyme Engine ──────────────────────────────────────
    if multi_rhyme_bank:
        import random
        # Pick a random robust pattern
        valid_patterns = [k for k, v in multi_rhyme_bank.items() if len(v) >= 4]
        if valid_patterns:
            chosen = random.choice(valid_patterns)
            # Take up to 5 examples
            suggestions = multi_rhyme_bank[chosen][:5]
            parts.append("\nMULTI RHYME ÖRNEKLERİ:")
            parts.extend(suggestions)
            parts.append("\nAma model aynı satırları kopyalamamalı.")

    # ── 3.5. Style Embedding Engine ──────────────────────────────────
    if style_embedding:
        parts.append("\nSTYLE EMBEDDING ENGINE:")
        parts.append("Talimat: Sanatçının stil vektörüne yakın bir dil kullan.")

    # ── 4. Themes ────────────────────────────────────────────────────
    if themes:
        parts.append(f"\nTEMALAR: {', '.join(themes[:4])}")

    # ── 5. Reference lyrics (semantic or random) ─────────────────────
    if semantic_examples is None:
        # Auto-retrieve semantically similar lines
        examples = get_semantic_examples(name, themes, k=40)
    else:
        examples = semantic_examples

    if examples:
        parts.append(
            "\nREFERANS SATIRLAR "
            "(sanatçının gerçek şarkılarından anlamsal olarak en yakın örnekler):"
        )
        parts.append(
            "Bu satırların kelime seçimlerini, ritmini ve dize kırılımlarını "
            "taklit et. Ama ASLA aynı cümleleri tekrar etme."
        )
        parts.extend(examples)

    # ── 6. Final trigger ─────────────────────────────────────────────
    parts.extend(["", "Şimdi üret:"])

    prompt = "\n".join(parts)

    if len(prompt) > 8000:
        logger.warning("Prompt truncated: %d → 8000 chars", len(prompt))

    return prompt[:8000] if len(prompt) > 8000 else prompt


# ── Legacy alias (backward compatibility for main.py / FastAPI) ──────────

def build_messages(request: Any) -> list:
    """
    Build an OpenAI-compatible message list from a RemixRequest.

    This keeps the FastAPI /remix endpoint working without changes.
    """
    from app.style_engine import get_artist_profile

    artist_name = getattr(request, "artist_style", None) or "Ezhel"
    profile = get_artist_profile(artist_name)

    if profile is None:
        profile = {
            "name": artist_name,
            "genre": "rap",
            "era": "new",
            "dna": {},
        }

    mood_str = request.mood.value if hasattr(request.mood, "value") else str(request.mood)
    themes = [request.topic, mood_str]

    prompt_text = build_prompt(
        artist_profile=profile,
        genre=profile.get("genre", "rap"),
        era=profile.get("era", "new"),
        themes=themes,
        emotion_level=7,
    )

    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": "Generate the lyrics now."},
    ]