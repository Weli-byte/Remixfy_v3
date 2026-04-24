"""
Transform artists.json: replace style_profile → dna object.
Generates realistic, genre/era/style-aware DNA for each artist.
"""

import json
import random
from pathlib import Path

random.seed(42)

SRC = Path("data/artists.json")

# ── Imagery pools by genre ───────────────────────────────────────────────

IMAGERY = {
    "rap": [
        "beton duvarlar", "gece sokakları", "duman bulutları", "asfalt çatlakları",
        "kırık aynalar", "kurşun izleri", "neon ışıklar", "siyah örtüler",
        "demir kapılar", "karanlık koridorlar", "gölgede bekleyenler", "yanan sigaralar",
        "mikrofon sahnesi", "kayıp gençlik", "parçalanmış rüyalar", "soğuk bakışlar",
        "altın zincirler", "hız yapan arabalar", "grafiti duvarlar", "titreyen eller",
        "boş caddeler", "kanlı eldivenler", "çelik kasalar", "yıkık binalar",
        "alev topları", "gece vardiyası", "uçurum kenarı", "sisli köprüler",
    ],
    "pop": [
        "yaz geceleri", "deniz kenarı", "güneş batışı", "dans pistleri",
        "ışıl ışıl kıyafetler", "gece kulübü", "yıldızlı gökyüzü", "bahar çiçekleri",
        "neon tabelalar", "parfüm kokusu", "cam maskeler", "kırık kalpler",
        "sonsuz otoyollar", "güneş gözlükleri", "sahil kasabaları", "gül yaprakları",
        "ay ışığı", "rüya trenleri", "şampanya köpükleri", "bulut koltuklar",
    ],
    "arabesk": [
        "yağmurlu pencereler", "eski fotoğraflar", "solmuş güller", "meyhane masaları",
        "tren garları", "gözyaşı izleri", "yanık mektuplar", "gurbet trenleri",
        "kapanmayan yaralar", "boş yataklar", "sonbahar yaprakları", "sis içinde yollar",
        "kırık plaklar", "duman izleri", "terkedilmiş evler", "siyah beyaz filmler",
        "son vapur", "vuslat hayali", "yıkık düğün salonları", "karlı akşamlar",
    ],
    "rock": [
        "yanan sahneler", "patlayan amfiler", "zincirler", "gece otoyolları",
        "yıldırım çarpması", "isyan bayrakları", "kırılan gitarlar", "motosiklet farları",
        "terkedilmiş fabrikalar", "duvar yazıları", "kıvılcım yağmuru", "çığlık dolu stadyumlar",
        "volkan patlaması", "deprem sonrası", "dikenli teller", "pas tutan raylar",
        "yangın merdivenleri", "gece kaçışları", "barikat arkası", "çatı katları",
    ],
    "alternative": [
        "paralel evrenler", "kırık prizmalar", "sis haritaları", "dijital yansımalar",
        "boşlukta süzülme", "ayna labirentleri", "soyut tablolar", "sessiz çığlıklar",
        "nebula desenleri", "zaman kıvrımları", "hologram hatıralar", "kristal mağaralar",
        "su altı şehirleri", "bulanık fotoğraflar", "ters dönmüş ağaçlar", "cam fanuslar",
        "gece kelebekleri", "titreşen telgraflar", "donmuş göller", "ışık huzmeleri",
    ],
}

# ── Theme pools by genre ─────────────────────────────────────────────────

THEMES = {
    "rap": [
        "sokak hayatı", "para hırsı", "ihanet", "güç mücadelesi", "sadakat",
        "mahalle bağı", "hayatta kalma", "ego", "aile", "özgürlük",
        "başarı", "intikam", "yalnızlık", "isyan", "kimlik",
        "savaş", "hapis", "kardeşlik", "statü", "kaçış",
    ],
    "pop": [
        "aşk", "kırık kalp", "yaz aşkı", "özlem", "dans",
        "gece hayatı", "güzellik", "umut", "kaçış", "tutku",
        "rüya", "yeni başlangıç", "parti", "özgürlük", "nostalji",
    ],
    "arabesk": [
        "ayrılık acısı", "kader", "hasret", "gurbet", "yalnızlık",
        "ihanet", "vefasızlık", "gözyaşı", "çile", "ömür",
        "sevda", "yürek yangını", "kavuşma", "felek", "sitem",
    ],
    "rock": [
        "isyan", "özgürlük", "sistem eleştirisi", "kaos", "yalnızlık",
        "adrenalin", "yıkım", "aşk", "öfke", "umut",
        "savaş", "yolculuk", "bağımsızlık", "değişim", "güç",
    ],
    "alternative": [
        "varoluş", "zaman", "hafıza", "yabancılaşma", "kimlik",
        "doğa", "teknoloji", "rüya", "kayıp", "sessizlik",
        "paralel yaşamlar", "yansıma", "dönüşüm", "sınır", "soyutluk",
    ],
}

# ── Hook style by structural tendency ────────────────────────────────────

HOOK_STYLES = {
    "short hook": [
        "Kısa ve sert, 4-5 kelimelik vurucu slogan tarzı hook.",
        "Minimal ama etkileyici, tekrara uygun keskin hook.",
        "Anlık patlamalı hook, akılda anında kalır.",
    ],
    "long verse": [
        "Verse-driven yapı, hook minimalist ama anlam yüklü.",
        "Verse'ün derinliği öne çıkar, hook atmosfer yaratır.",
        "Anlatı odaklı, hook kısa bir nefes molası gibi.",
    ],
    "repetitive chorus": [
        "Tekrarlı melodik hook, kulağa yapışır, kitle etkileşimli.",
        "Döngüsel nakarat, her tekrarda duygusal yoğunluk artar.",
        "Hipnotik tekrar, ritmik ve söylenebilir hook yapısı.",
    ],
}

# ── Cadence patterns by flow ─────────────────────────────────────────────

def _cadence(flow: str) -> str:
    fl = flow.lower()
    if any(k in fl for k in ("drill", "dark")):
        return "Staccato drill kadansı. Kısa kesik heceler, sert vuruşlar, ağır tempo. Her bar'da belirgin duraklar. Kelimeler bıçak gibi keser."
    if "trap" in fl:
        return "Trap kadansı. Uzatılmış heceler, ad-lib boşlukları, 808 hissi. Yarım tempo ile hızlı geçişler arasında salınım."
    if "melodic" in fl or "melodik" in fl or "laid-back" in fl:
        return "Melodik akış. Şarkı söyler gibi rap, tonal geçişler, sesli harf uyumu. Rahat ama kontrollü tempo."
    if "fast" in fl or "ultra-fast" in fl or "choppy" in fl:
        return "Hızlı choppy kadans. Yoğun hece akışı, nefes kontrolü kritik. Kelimeler üst üste yığılır."
    if "poetic" in fl or "philosophical" in fl:
        return "Şiirsel kadans. Ölçülü akış, stratejik duraklamalar, edebi ritim. Her kelime tartılmış."
    if "aggressive" in fl or "hard-hitting" in fl:
        return "Agresif kadans. Sert vurgular, yüksek enerji, bas-ağırlıklı delivery. Punchline'lar çekiç gibi iner."
    if "storytelling" in fl:
        return "Anlatıcı kadans. Sakin tempoda hikaye akışı, dinleyiciyi sahneye çeker. Tempo hikayeyle birlikte yükselir."
    return "Dengeli kadans. Net heceler, orta tempo, vurgu geçişleri doğal."


# ── Word texture by rhyme complexity ─────────────────────────────────────

def _word_texture(complexity: str, genre: str) -> str:
    if complexity == "high":
        if genre == "rap":
            return "Yoğun kelime dokusu. Çok heceli sözcükler, argo+edebi karışım, slang katmanları. Her satır bilgi yüklü."
        return "Zengin kelime dokusu. Katmanlı ifadeler, sembolik söz dağarcığı, yoğun anlatım."
    if complexity == "low":
        return "Sade kelime dokusu. Kısa direkt sözcükler, günlük dil, minimal süsleme."
    # medium
    if genre == "rap":
        return "Orta yoğunlukta kelime dokusu. Argo ve günlük dil dengesi, arada edebi atıflar."
    return "Orta yoğunlukta kelime dokusu. Erişilebilir ama sığ değil, duygusal derinlik var."


# ── Signature energy ─────────────────────────────────────────────────────

def _signature_energy(flow: str, tone: str, genre: str, era: str) -> str:
    fl = flow.lower()
    base = ""

    if "drill" in fl or "dark" in fl:
        base = "Karanlık ve tehditkâr bir enerji. Sahnede buz gibi soğuk, her kelime hesaplı."
    elif "trap" in fl:
        base = "Sokaklardan gelen ağır enerji. Flex ve hakimiyet, her bar statü göstergesi."
    elif "melodic" in fl or "melodik" in fl:
        base = "Melodik ve duygusal enerji. Sert içeriği yumuşak melodiyle sarıyor."
    elif "fast" in fl or "choppy" in fl:
        base = "Patlayıcı enerji. Hız ve teknik ustalık bir arada, nefes kesici delivery."
    elif "poetic" in fl or "philosophical" in fl:
        base = "Derin düşünce enerjisi. Her satır felsefi ağırlık taşıyor, dinleyiciyi zorluyor."
    elif "aggressive" in fl:
        base = "Yıkıcı enerji. Sahneyi parçalayan agresyon, hiç frene basmadan."
    else:
        base = "Dengeli ama etkili enerji. Kontrollü güç, doğru anlarda patlayan yoğunluk."

    tone_suffix = f" Duygusal renk: {tone}." if tone else ""
    era_suffix = ""
    if era == "new":
        era_suffix = " Yeni nesil estetiğiyle harmanlıyor."
    elif era == "old":
        era_suffix = " Klasik okul disipliniyle şekilleniyor."

    return base + tone_suffix + era_suffix


# ── Ego/vulnerability ratio ─────────────────────────────────────────────

def _ego_ratio(tone: str, genre: str) -> str:
    tl = tone.lower()
    if any(k in tl for k in ("aggressive", "threatening", "fierce", "cold")):
        return "85/15"
    if any(k in tl for k in ("melancholic", "vulnerable", "emotional", "introspective")):
        return "30/70"
    if any(k in tl for k in ("confident", "hype")):
        return "75/25"
    if any(k in tl for k in ("chill", "laid-back", "rebellious")):
        return "60/40"
    if genre == "arabesk":
        return "20/80"
    if genre == "rock":
        return "65/35"
    return "55/45"


# ── Main transform ──────────────────────────────────────────────────────

def transform() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} artists.")

    for artist in data:
        sp = artist.get("style_profile", {})
        genre = artist.get("genre", "rap")
        era = artist.get("era", "new")

        flow = sp.get("flow_description", "")
        tone = sp.get("emotional_tone", "")
        complexity = sp.get("rhyme_complexity", "medium")
        tendency = sp.get("structural_tendency", "short hook")
        old_themes = sp.get("common_themes", [])

        # Build theme_bias: use old themes + pad from genre pool
        genre_pool = THEMES.get(genre, THEMES["rap"])
        bias = list(old_themes)
        for t in genre_pool:
            if t not in bias:
                bias.append(t)
            if len(bias) >= 5:
                break
        bias = bias[:5]

        # Build typical_imagery: pick 5 from genre pool
        img_pool = IMAGERY.get(genre, IMAGERY["rap"])
        imagery = random.sample(img_pool, min(5, len(img_pool)))

        # Hook style
        hooks = HOOK_STYLES.get(tendency, HOOK_STYLES["short hook"])
        hook = random.choice(hooks)

        # Build dna
        dna = {
            "signature_energy": _signature_energy(flow, tone, genre, era),
            "cadence_pattern": _cadence(flow),
            "word_texture": _word_texture(complexity, genre),
            "theme_bias": bias,
            "ego_vulnerability_ratio": _ego_ratio(tone, genre),
            "hook_style": hook,
            "typical_imagery": imagery,
            "style_imprint_lines": [],
        }

        # Replace
        artist.pop("style_profile", None)
        artist["dna"] = dna

    # Write
    SRC.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"✅ Transformed {len(data)} artists → dna structure.")

    # Verify
    sample = data[0]
    print(f"\nSample: {sample['name']}")
    print(json.dumps(sample["dna"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    transform()
