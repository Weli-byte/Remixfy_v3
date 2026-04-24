"""
Generate style_fragments for each artist based on their DNA.
8 original Turkish lines per artist, reflecting cadence/tone/imagery.
"""

import json
import random
from pathlib import Path

random.seed(2026)

SRC = Path("data/artists.json")

# ── Line templates per genre ─────────────────────────────────────────────
# {img} = typical_imagery item, {theme} = theme_bias item
# Templates designed to feel like authentic artist lines, not descriptions.

_RAP_TEMPLATES = [
    # Ego / dominance
    "{img} arasında büyüdüm ben farklı geldim",
    "Her adımda iz bıraktım {img} şahit",
    "Kimse durduramaz beni {theme} kanımda akar",
    "{theme} için yandım ama küle dönmedim",
    "Gözlerim {img} gördü ellerim çelik oldu",
    "Bu yolda tek başıma yürüdüm {theme} rehberim",
    "{img} geride kaldı şimdi zirvedeyim",
    "Sözlerim kurşun gibi {img} delip geçer",
    "Her gece {img} içinde kayboldum ama döndüm",
    "{theme} benim hikayem duvarlardan oku",
    "Sessiz fırtına gibi geldim {img} titredi",
    "Beton üstünde doğdum {theme} ruhuma işledi",
    "{img} aydınlatamaz bu karanlık benim",
    "Herkes kaçarken ben {img} yürüdüm dümdüz",
    "Söylediklerim gerçek {theme} yalanları değil",
    "Mikrofon elime geçince {img} sallandı",
    "{theme} öğretti bana güvenmemeyi kimseye",
    "Yıkıntılardan yükseldim {img} temelim oldu",
    "Alev alev yandım ama {theme} söndüremedi",
    "Gecenin çocuğuyum {img} tanıkım benim",
    "{img} sessizliğinde kükreyen bir ses var",
    "Her düşüşte kalktım {theme} beni ayağa dikti",
    "Soğuk bakışlarımın arkasında {theme} yatar",
    "Kafamdaki fırtına {img} kadar karanlık",
    # Vulnerability cracks
    "Bazen yoruluyorum ama {theme} bırakmama izin vermez",
    "İçimdeki çocuk hâlâ {img} arıyor",
    "Güçlü görünüyorum ama {theme} içimi kemiriyor",
    "{img} hatırlatıyor bana nereden geldiğimi",
    "Gülümsememin arkasında {theme} saklı",
    "Herkes gitti ben {img} kaldım tek başıma",
]

_POP_TEMPLATES = [
    "Seninle dans ettim {img} altında unutulmaz",
    "{theme} kalbimde yankılanıyor her gece",
    "Gözlerinde {img} gördüm kayboldum bir an",
    "Bu şarkı seninle {theme} dolu her notası",
    "{img} gibi parlıyorsun benim gökyüzümde",
    "Dudaklarında {theme} tadı kaldı hâlâ",
    "Rüyamda {img} yanında uyandım yine",
    "Kalbim {theme} atıyor senin ritminle",
    "Her bakışında {img} açılıyor önümde",
    "{theme} demek seni sevmek demek anlıyor musun",
    "Geceyi aydınlatan {img} senin gülüşün",
    "Uzaklaşsan da {theme} peşinden gelir benim",
    "{img} kadar güzelsin ama daha yakınsın",
    "Seninle {theme} bir anlam kazandı hayatım",
    "Bu melodide {img} var her notada sen",
    "Kırık kalbimi {theme} sarmıyor artık",
]

_ARABESK_TEMPLATES = [
    "Yüreğim {img} gibi yanıyor durmadan",
    "{theme} içinde boğuldum çıkamadım bir türlü",
    "Gözlerimden {img} akıyor her gece",
    "Bu acıyı kimse anlamaz {theme} benim kaderim",
    "{img} hatırası yüreğimde sızlıyor",
    "Sensiz geçen geceler {theme} dolu bitmez",
    "{img} gibi soldum sarardım sensizlikten",
    "Felek bana {theme} çektirdi durmadan",
    "Gözyaşlarım {img} oldu döküldü sessizce",
    "{theme} yarasını sardım ama kanamaya devam",
    "Bu gurbet {img} kadar soğuk ve acımasız",
    "Yalnızlığım {theme} gibi bitmek bilmiyor",
    "{img} ardında kalan sevdam unutulmaz",
    "Ah çeksem de {theme} dinmiyor içimdeki",
    "Kaderim {img} gibi karanlık ve derin",
    "Sevda ateşi {theme} gibi yakıyor beni",
]

_ROCK_TEMPLATES = [
    "{img} arasında bağırdım kimse duymadı",
    "İsyan bayrakları {theme} için dalgalanıyor",
    "Bu sahne {img} gibi yanıyor alev alev",
    "{theme} içinde koştum durmadım hiç",
    "Zincirlerimi kırdım {img} geride kaldı",
    "Gürültünün içinde {theme} yankılanıyor",
    "{img} gibi patlıyorum kontrol yok artık",
    "Özgürlük {theme} kadar yakın ama uzak",
    "Her akor {img} kadar sert vuruyor",
    "{theme} için savaştım yıkıntılardan çıktım",
    "Bu gece {img} altında kükreyeceğim",
    "Sesim {theme} kadar güçlü durdurun beni",
    "{img} yıkılsa da ayaktayım hâlâ",
    "Ateşin ortasında {theme} beni korudu",
    "Çığlığım {img} delip geçiyor duvarları",
    "Fırtına gibi geldim {theme} peşimde",
]

_ALT_TEMPLATES = [
    "{img} arasında kayboldum zaman durdu",
    "Sessizliğin içinde {theme} fısıldıyor",
    "{img} gibi bulanık her şey belirsiz",
    "Aynalarda {theme} yansıması kırık görünüyor",
    "Bu labirentte {img} tek rehberim oldu",
    "{theme} katmanları arasında süzülüyorum",
    "{img} ötesinde bir gerçeklik var belki",
    "Hafızam {theme} gibi parçalanmış dağınık",
    "Titreşimler {img} arasında dolaşıyor sessizce",
    "{theme} sınırlarında duruyorum kararsız",
    "Prizmadan geçen {img} renklere dönüşüyor",
    "Soyut düşünceler {theme} gibi akıyor durmadan",
    "{img} içinde bir yankı arıyorum",
    "Zaman kıvrımlarında {theme} sürükleniyor",
    "Bulanık fotoğraflar {img} gibi soluk unutulmuş",
    "Kristal sessizlikte {theme} çınlıyor kulağımda",
]

_TEMPLATES: dict[str, list[str]] = {
    "rap": _RAP_TEMPLATES,
    "pop": _POP_TEMPLATES,
    "arabesk": _ARABESK_TEMPLATES,
    "rock": _ROCK_TEMPLATES,
    "alternative": _ALT_TEMPLATES,
}


def _generate_fragments(artist: dict) -> list[str]:
    """Generate 8 unique style fragment lines for an artist."""
    genre = artist.get("genre", "rap")
    dna = artist.get("dna", {})

    imagery = dna.get("typical_imagery", ["gölgeler"])
    themes = dna.get("theme_bias", ["hayat"])

    templates = _TEMPLATES.get(genre, _TEMPLATES["rap"])
    random.shuffle(templates)

    fragments: list[str] = []
    used: set[str] = set()

    for tmpl in templates:
        if len(fragments) >= 8:
            break

        img = random.choice(imagery)
        theme = random.choice(themes)

        line = tmpl.replace("{img}", img).replace("{theme}", theme)

        # Ensure uniqueness
        if line not in used:
            used.add(line)
            fragments.append(line)

    # Pad if templates ran short
    while len(fragments) < 8:
        img = random.choice(imagery)
        theme = random.choice(themes)
        fallback = f"{img} içinde {theme} yankılanıyor sessizce"
        if fallback not in used:
            used.add(fallback)
            fragments.append(fallback)
        else:
            fragments.append(f"{theme} ruhuma işledi {img} tanığım")

    return fragments[:8]


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} artists.")

    for artist in data:
        fragments = _generate_fragments(artist)
        artist["dna"]["style_fragments"] = fragments

    SRC.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"✅ Added style_fragments to {len(data)} artists.")

    # Sample
    for genre in ["rap", "pop", "arabesk", "rock", "alternative"]:
        for a in data:
            if a["genre"] == genre:
                print(f"\n── {a['name']} ({genre}) ──")
                for i, f in enumerate(a["dna"]["style_fragments"], 1):
                    print(f"  {i}. {f}")
                break


if __name__ == "__main__":
    main()
