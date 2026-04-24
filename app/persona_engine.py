"""
Artist Persona Engine - Extracts and builds a character profile for an artist.

This module determines the artist's persona (archetype, tone, themes) based
on word frequency analysis from their lyric corpus. The extracted profile
is then injected into the LLM prompt to heavily influence the voice and
emotional perspective of the generated lyrics.
"""

import string
import logging
from collections import Counter
from typing import Dict, Any

logger = logging.getLogger(__name__)


def extract_artist_persona(artist_name: str) -> Dict[str, Any]:
    """
    Extracts persona features by performing word frequency analysis
    on the artist's corpus.
    """
    try:
        from app.flow_analyzer import get_corpus_for_artist
        lines = get_corpus_for_artist(artist_name)
    except ImportError:
        logger.warning("Could not import get_corpus_for_artist; using empty lines.")
        lines = []

    words = []
    stopwords = {
        "bir", "ve", "bu", "de", "da", "di", "mi", "ile", "için", "çok", "gibi", 
        "ama", "ne", "var", "yok", "sen", "ben", "o", "biz", "siz", "onlar", 
        "beni", "seni", "bana", "sana", "daha", "her", "kadar", "olan", "ki", 
        "en", "şu", "benim", "senin", "içinde", "hiç", "neden", "nasıl", "niye",
        "göre", "böyle", "şimdi", "yine", "sanki", "sonra", "öyle", "oldu"
    }

    for line in lines:
        cleaned = line.translate(str.maketrans('', '', string.punctuation)).lower()
        for w in cleaned.split():
            if len(w) > 3 and w not in stopwords:
                words.append(w)

    counts = Counter(words)
    top_words = [w for w, c in counts.most_common(5)]
    themes_list = top_words if top_words else ["sokak", "hayat", "mücadele"]

    # Basic heuristic to define archetype and tone from top words
    archetype = "street philosopher"
    tone = "ambitious and gritty"
    attitude = "resilient"

    # Some basic checks to dynamically change persona
    romantic_words = {"aşk", "kalp", "sev", "gece", "acı", "yara"}
    ego_words = {"para", "kral", "boss", "lider", "iş", "ben", "zirve"}
    
    if any(w in romantic_words for w in themes_list):
        archetype = "romantic antihero"
        tone = "bitter and sarcastic"
        attitude = "cold confidence"
    elif any(w in ego_words for w in themes_list):
        archetype = "unstoppable boss"
        tone = "arrogant and dominant"
        attitude = "relentless ambition"

    return {
        "archetype": archetype,
        "tone": tone,
        "themes": themes_list,
        "attitude": attitude
    }


def build_persona_profile(artist_name: str) -> Dict[str, Any]:
    """
    Builds the final persona profile to be used in the prompt builder.
    Combines extracted persona metrics with standard delivery profiles.
    """
    persona = extract_artist_persona(artist_name)
    
    archetype = persona.get("archetype", "romantic antihero")
    
    if archetype == "romantic antihero":
        voice = "first person"
        energy = "calm but intense"
        dominant_emotion = "bittersweet anger"
        delivery = "controlled but emotional"
    elif archetype == "unstoppable boss":
        voice = "first person"
        energy = "high and aggressive"
        dominant_emotion = "supreme confidence"
        delivery = "punchy and authoritative"
    else:
        voice = "first person observer"
        energy = "steady flow"
        dominant_emotion = "streetwise reflection"
        delivery = "narrative and rhythmic"

    return {
        "archetype": archetype,
        "tone": persona.get("tone", "cold ego with emotional scars"),
        "themes": ", ".join(persona.get("themes", [])),
        "attitude": persona.get("attitude", ""),
        "voice": voice,
        "energy": energy,
        "dominant_emotion": dominant_emotion,
        "delivery": delivery
    }
