"""
Fix English theme_bias entries → Turkish translations.
Then regenerate style_fragments with Turkish-only content.
"""

import json
from pathlib import Path

SRC = Path("data/artists.json")

TRANSLATIONS = {
    "resistance": "direniş",
    "street life": "sokak hayatı",
    "Turkish identity": "Türk kimliği",
    "existentialism": "varoluş",
    "loneliness": "yalnızlık",
    "philosophy": "felsefe",
    "rebellion": "isyan",
    "luxury": "lüks",
    "swagger": "özgüven",
    "love": "aşk",
    "desire": "arzu",
    "celebration": "kutlama",
    "pop culture": "pop kültürü",
    "romance": "romantizm",
    "heartbreak": "kalp kırıklığı",
    "nostalgia": "nostalji",
    "dance": "dans",
    "party": "parti",
    "summer love": "yaz aşkı",
    "beauty": "güzellik",
    "empowerment": "güçlenme",
    "independence": "bağımsızlık",
    "self-expression": "kendini ifade",
    "fun": "eğlence",
    "freedom": "özgürlük",
    "youth": "gençlik",
    "nightlife": "gece hayatı",
    "passion": "tutku",
    "wanderlust": "gezginlik",
    "hope": "umut",
    "sorrow": "keder",
    "fate": "kader",
    "longing": "hasret",
    "separation": "ayrılık",
    "unrequited love": "karşılıksız aşk",
    "poverty": "yoksulluk",
    "migration": "göç",
    "betrayal": "ihanet",
    "pain": "acı",
    "patience": "sabır",
    "suffering": "çile",
    "devotion": "bağlılık",
    "loyalty": "sadakat",
    "loss": "kayıp",
    "anger": "öfke",
    "struggle": "mücadele",
    "social critique": "toplumsal eleştiri",
    "war": "savaş",
    "chaos": "kaos",
    "energy": "enerji",
    "speed": "hız",
    "urban decay": "kentsel çürüme",
    "protest": "protesto",
    "alienation": "yabancılaşma",
    "time": "zaman",
    "memory": "hafıza",
    "identity": "kimlik",
    "nature": "doğa",
    "technology": "teknoloji",
    "dreams": "rüyalar",
    "silence": "sessizlik",
    "parallel lives": "paralel yaşamlar",
    "reflection": "yansıma",
    "transformation": "dönüşüm",
    "boundaries": "sınırlar",
    "abstraction": "soyutluk",
    "psychedelia": "psikedeli",
    "Istanbul underground": "İstanbul yeraltı",
    "cultural fusion": "kültürel sentez",
    "ethnic roots": "etnik kökler",
    "Turkish folklore": "Türk halk müziği",
    "mysticism": "mistisizm",
    "children": "çocuklar",
    "social commentary": "toplumsal yorum",
    "cultural pride": "kültürel gurur",
    "Anatolian spirit": "Anadolu ruhu",
    "spiritual journey": "ruhani yolculuk",
    "inner peace": "iç huzur",
    "connection": "bağlantı",
    "growth": "büyüme",
    "self-discovery": "kendini keşif",
    "street hustle": "sokak koşturmacası",
    "ambition": "hırs",
    "survival": "hayatta kalma",
    "wealth": "zenginlik",
    "power": "güç",
    "determination": "kararlılık",
    "respect": "saygı",
    "fame": "şöhret",
    "flex": "şov",
    "truth": "gerçek",
    "justice": "adalet",
    "ego": "ego",
    "trust": "güven",
    "adrenaline": "adrenalin",
    "darkness": "karanlık",
    "intensity": "yoğunluk",
    "euphoria": "coşku",
    "vulnerability": "kırılganlık",
    "obsession": "takıntı",
    "dominance": "hakimiyet",
    "territory": "bölge",
    "street warfare": "sokak savaşı",
    "survival instinct": "hayatta kalma içgüdüsü",
    "material success": "maddi başarı",
    "urban life": "şehir hayatı",
    "melodic pain": "melodik acı",
    "emotional depth": "duygusal derinlik",
    "musical innovation": "müzikal yenilik",
    "authenticity": "otantiklik",
    "poetic expression": "şiirsel ifade",
    "cultural commentary": "kültürel yorum",
    "raw emotion": "ham duygu",
    "street credibility": "sokak güvenilirliği",
    "personal growth": "kişisel gelişim",
    "inner conflict": "iç çatışma",
    "night life": "gece yaşamı",
    "social awareness": "toplumsal farkındalık",
    "self-reflection": "öz yansıma",
    "modern love": "modern aşk",
    "breaking rules": "kuralları yıkmak",
    "dark humor": "kara mizah",
    "street wisdom": "sokak bilgeliği",
    "defiance": "meydan okuma",
    "solitude": "yalnızlık",
    "melancholy": "melankoli",
    "urban poetry": "kentsel şiir",
}


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    fixed = 0

    for artist in data:
        dna = artist.get("dna", {})
        bias = dna.get("theme_bias", [])
        new_bias = []
        for theme in bias:
            t_lower = theme.lower().strip()
            if t_lower in TRANSLATIONS:
                new_bias.append(TRANSLATIONS[t_lower])
                fixed += 1
            elif any(c.isascii() and c.isalpha() for c in theme) and not any(
                c in "çğıöşüÇĞİÖŞÜ" for c in theme
            ):
                # Likely English, try lookup
                new_bias.append(TRANSLATIONS.get(t_lower, theme))
            else:
                new_bias.append(theme)
        dna["theme_bias"] = new_bias

    SRC.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"✅ Fixed {fixed} English theme entries across {len(data)} artists.")


if __name__ == "__main__":
    main()
