"""
Style Imprint – generates a detailed stylistic fingerprint from an
artist profile for use in prompt enrichment and lyric generation.
"""

from __future__ import annotations

from typing import Any


# ── Signature word banks by genre ────────────────────────────────────────

_SIGNATURE_WORDS: dict[str, list[str]] = {
    "rap": [
        "sokak", "beton", "gece", "duman", "iz", "yara", "kurşun",
        "gölge", "alev", "kül", "demir", "çelik", "kan", "ter",
        "fırtına", "yıkım", "kasvet", "hırs", "nefes", "asfalt",
    ],
    "pop": [
        "aşk", "rüya", "ışık", "gül", "deniz", "yıldız", "gökyüzü",
        "umut", "bahar", "mevsim", "dans", "gülümseme", "kalp", "dokunuş",
        "melodi", "renk", "bulut", "güneş", "ay", "şarkı",
    ],
    "arabesk": [
        "acı", "gözyaşı", "kader", "hasret", "gurbet", "yalnızlık",
        "feryat", "dert", "çile", "ayrılık", "hüzün", "sitem",
        "vefasız", "gurbetçi", "ah", "yürek", "sevda", "yanmak",
        "ağlamak", "küskün",
    ],
    "rock": [
        "isyan", "fırtına", "yangın", "çığlık", "özgürlük", "kaos",
        "yıldırım", "uçurum", "patlama", "zincir", "volkan", "kükreyiş",
        "adrenalin", "gürültü", "kıvılcım", "savaş", "yıkıntı", "titreşim",
        "darbe", "kaya",
    ],
    "alternative": [
        "sis", "ayna", "boşluk", "fragman", "parçacık", "labirent",
        "paralel", "yankı", "gölgeler", "prizma", "sessizlik", "spiral",
        "yansıma", "soyut", "bulanık", "katman", "titreşim", "dalga",
        "nebula", "eşik",
    ],
}

# ── Slang banks by era ───────────────────────────────────────────────────

_SLANG_BANKS: dict[str, dict[str, list[str]]] = {
    "rap": {
        "old": [
            "abi", "lan", "moruk", "kanka", "efsane", "adam",
            "olay", "iş", "sahne", "kafiye",
        ],
        "middle": [
            "bro", "kral", "flow", "beat", "mic", "sahne",
            "rap game", "punchline", "freestyle", "underground",
        ],
        "new": [
            "gang", "drill", "ses", "trap", "vibe", "flex",
            "mood", "hype", "skrt", "aye", "boom", "gang gang",
            "bi' saniye", "tmm", "yak", "patla",
        ],
    },
    "pop": {
        "old": ["canım", "hayatım", "sevgilim", "bir tanem"],
        "middle": ["aşkım", "bebeğim", "tatlım", "gel"],
        "new": ["babe", "baby", "aşkitom", "hadi", "yaz bitti"],
    },
    "arabesk": {
        "old": ["efendim", "sultanım", "aman", "of", "eyvah"],
        "middle": ["yar", "gül yüzlüm", "hey", "vah", "yazık"],
        "new": ["be", "ulan", "kaderim", "halim", "n'olur"],
    },
    "rock": {
        "old": ["hey", "kardeş", "yoldaş", "hadi", "dur"],
        "middle": ["lan", "bak", "dinle", "kalk", "yeter"],
        "new": ["bas", "patlat", "yak", "geç", "sus"],
    },
    "alternative": {
        "old": ["belki", "sanki", "bir yerde", "bir zamanlar"],
        "middle": ["galiba", "herhalde", "öyle mi", "ya da"],
        "new": ["bence", "aslında", "tam olarak", "işte", "yani"],
    },
}

# ── Hook patterns by genre & structural tendency ─────────────────────────

_HOOK_PATTERNS: dict[str, dict[str, str]] = {
    "rap": {
        "short hook": "Kısa, sert, tekrar edilebilir — 4-6 kelimelik vurucu slogan.",
        "long verse": "Verse-driven yapı — hook minimalist, anlam verse'te yüklü.",
        "repetitive chorus": "Akılda kalan tekrarlı nakarat — melodik ve ritmik.",
    },
    "pop": {
        "short hook": "Ultra-catchy kısa hook — hemen akılda kalır.",
        "long verse": "Verse anlatımı güçlü — nakarat duygusal doruk.",
        "repetitive chorus": "Tekrar tekrar söylenen ana melodi — şarkının kalbi.",
    },
    "arabesk": {
        "short hook": "Acıyı özetleyen tek cümle — bıçak gibi keser.",
        "long verse": "Uzun dertli anlatım — nakarat feryat noktası.",
        "repetitive chorus": "Aynı acıyı tekrar tekrar hissettiren döngü.",
    },
    "rock": {
        "short hook": "Kısa patlayıcı hook — kalabalık bağırır.",
        "long verse": "Verse-driven yoğunluk — hook enerjik patlama.",
        "repetitive chorus": "Stadyum nakaratı — herkes söyler.",
    },
    "alternative": {
        "short hook": "Minimalist soyut hook — anlam katmanları gizli.",
        "long verse": "Verse derinlikli — hook atmosfer yaratır.",
        "repetitive chorus": "Hipnotik tekrar — trance etkisi.",
    },
}

# ── Metaphor styles by emotional tone keywords ──────────────────────────

_METAPHOR_MAP: dict[str, str] = {
    "dark": "Karanlık ve kasvetli metaforlar — gece, gölge, duman, kül, uçurum.",
    "aggressive": "Savaş ve şiddet metaforları — kurşun, bıçak, patlama, yangın.",
    "cold": "Buzlu ve mesafeli metaforlar — buz, çelik, boşluk, sessizlik.",
    "menacing": "Tehdit dolu metaforlar — yılan, tuzak, av, karanlık sokak.",
    "melancholic": "Hüzün ve kayıp metaforları — yağmur, sonbahar, solmuş çiçek.",
    "emotional": "Duygusal ve samimi metaforlar — yürek, gözyaşı, sarılmak.",
    "chill": "Rahat ve minimal metaforlar — dalga, rüzgar, gün batımı.",
    "hype": "Enerji ve güç metaforları — roket, patlama, zirve, alev.",
    "introspective": "İçe dönük metaforlar — ayna, rüya, labirent, hafıza.",
    "rebellious": "İsyan metaforları — zincir kırmak, duvar yıkmak, ateş yakmak.",
    "passionate": "Tutku metaforları — volkan, fırtına, yangın, coşku.",
    "poetic": "Lirik ve edebi metaforlar — mehtap, mürekkep, ipek, şiir.",
    "confident": "Güç ve hakimiyet metaforları — taht, taç, zirve, aslan.",
    "vulnerable": "Kırılganlık metaforları — cam, yaprak, sis, titreme.",
    "fierce": "Yırtıcı metaforlar — pençe, çığlık, kasırga, yıkım.",
    "threatening": "Tehdit metaforları — gölgede bekleyen, bıçak sırtı, sessiz fırtına.",
}

# ── Cadence types by flow description keywords ──────────────────────────

_CADENCE_MAP: dict[str, str] = {
    "drill": "Staccato drill kadansı — kısa kesik heceler, sert vuruşlar.",
    "trap": "Trap kadansı — uzatılmış heceler, ad-lib'li akış, 808 hissi.",
    "boom-bap": "Boom-bap kadansı — net heceler, klasik ritim, düz akış.",
    "melodic": "Melodik kadans — şarkı söyler gibi rap, tonal geçişler.",
    "aggressive": "Agresif kadans — hızlı nefes kontrolü, sert vurgular.",
    "storytelling": "Anlatıcı kadans — sakin tempoda hikaye akışı.",
    "fast": "Hızlı kadans — choppy delivery, yoğun hece akışı.",
    "laid-back": "Rahat kadans — gevşek akış, minimal vurgu, cool tarz.",
    "dark": "Karanlık kadans — ağır tempo, boğuk tonlama, baskıcı hava.",
    "emotional": "Duygusal kadans — kırılgan tonlama, nefes araları, his dolu.",
    "punk": "Punk kadansı — hızlı, kaotik, kuralsız enerji.",
    "poetic": "Şiirsel kadans — ölçülü akış, duraklamalar, edebi ritim.",
}

# ── Rhyme density by complexity ──────────────────────────────────────────

_RHYME_DENSITY: dict[str, str] = {
    "low": "Basit kafiye — satır sonu uyaklar, temel çiftler. Akıcı ama karmaşık değil.",
    "medium": "Orta kafiye yoğunluğu — satır sonu + yarım uyak + ara sıra iç kafiye.",
    "high": (
        "Yoğun kafiye mimarisi — iç kafiye, çok heceli kalıplar, asonans "
        "zincirleri, satır atlamalı çiftler. Her satırda en az bir iç uyak."
    ),
}


# ── Public API ───────────────────────────────────────────────────────────

def get_style_imprint(artist_profile: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a detailed stylistic imprint from an artist profile.

    Parameters
    ----------
    artist_profile : dict
        Full artist dict with keys: name, genre, era, style_profile.

    Returns
    -------
    dict
        Keys: signature_words, slang_bank, hook_pattern, metaphor_style,
              cadence_type, rhyme_density.
    """
    genre = artist_profile.get("genre", "rap").lower()
    era = artist_profile.get("era", "new").lower()
    sp = artist_profile.get("style_profile", {})

    # Signature words
    signature_words = _SIGNATURE_WORDS.get(genre, _SIGNATURE_WORDS["rap"])

    # Slang bank
    genre_slang = _SLANG_BANKS.get(genre, _SLANG_BANKS["rap"])
    slang_bank = genre_slang.get(era, genre_slang.get("new", []))

    # Hook pattern
    tendency = sp.get("structural_tendency", "short hook").lower()
    genre_hooks = _HOOK_PATTERNS.get(genre, _HOOK_PATTERNS["rap"])
    hook_pattern = genre_hooks.get(tendency, list(genre_hooks.values())[0])

    # Metaphor style — match against emotional_tone keywords
    emotional_tone = sp.get("emotional_tone", "").lower()
    metaphor_parts: list[str] = []
    for keyword, description in _METAPHOR_MAP.items():
        if keyword in emotional_tone:
            metaphor_parts.append(description)
    metaphor_style = "  ".join(metaphor_parts) if metaphor_parts else (
        "Genel metafor yaklaşımı — güçlü imgeler, somut benzetmeler."
    )

    # Cadence type — match against flow_description keywords
    flow = sp.get("flow_description", "").lower()
    cadence_parts: list[str] = []
    for keyword, description in _CADENCE_MAP.items():
        if keyword in flow:
            cadence_parts.append(description)
    cadence_type = "  ".join(cadence_parts) if cadence_parts else (
        "Standart kadans — dengeli tempo, net heceler."
    )

    # Rhyme density
    complexity = sp.get("rhyme_complexity", "medium").lower()
    rhyme_density = _RHYME_DENSITY.get(complexity, _RHYME_DENSITY["medium"])

    return {
        "signature_words": signature_words,
        "slang_bank": slang_bank,
        "hook_pattern": hook_pattern,
        "metaphor_style": metaphor_style,
        "cadence_type": cadence_type,
        "rhyme_density": rhyme_density,
    }
