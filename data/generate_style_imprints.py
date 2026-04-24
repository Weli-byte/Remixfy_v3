import json
import logging
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup simple logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add parent directory to sys.path to import app.llm_engine
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.llm_engine import call_llm

SRC = Path(__file__).resolve().parent / "artists.json"

def generate_lines_for_artist(artist: dict) -> dict:
    name = artist.get("name", "Unknown")
    genre = artist.get("genre", "rap")
    dna = artist.get("dna", {})

    prompt = f"""SEN BİR PROFESYONEL SÖZ YAZARISIN.
Aşağıda özellikleri detaylandırılmış sanatçı için, bu sanatçının DNA'sını ve türünü bütünüyle yansıtan TAM OLARAK 12 ADET KISA, ORİJİNAL SATIR (style imprint lines) ÜRET.

Sanatçı: {name}
Tür: {genre}
Enerji (Signature): {dna.get('signature_energy', '')}
Kadans/Ritim: {dna.get('cadence_pattern', '')}
Sözcük Dokusu: {dna.get('word_texture', '')}
Ana Temalar: {', '.join(dna.get('theme_bias', []))}
Tipik İmgeler: {', '.join(dna.get('typical_imagery', []))}
Hakimiyet / Kırılganlık Dengesi: {dna.get('ego_vulnerability_ratio', '')}

KURALLAR:
1. SADECE VE SADECE yepyeni, %100 orijinal sözler yaz. Telif hakkı olan hiçbir şarkıdan ALINTI YAPMA.
2. Tam olarak 12 adet farklı, birbirini tekrar etmeyen satır üret. 
3. Her satır MAKSİMUM 6 ile 8 KELİME arasında olmalıdır. Uzun cümleler YASAK.
4. Sanatçıların birbirinden AYIRT EDİLMESİ kritik. Sanatçının kendine has Kadans/Ritim özelliğine odaklan. Ritmik kimlik, imgelerden daha ön planda olmalı.
5. Sokak (street) jargonunu jenerik şekilde kullanmaktan KESİNLİKLE kaçın.
6. "beton, asfalt, zincir", "mikrofon" gibi aşırı klişe rap terimlerinden ve tekrarlayan imgelerden UZAK DUR. 
7. Sözleri liste olarak sun. Madde işareti, tire, numara veya açıklama KULLANMA. Sadece satırları yaz.
"""

    try:
        response_text = call_llm(prompt)
    except Exception as e:
        logger.error(f"Error generating for {name}: {e}")
        return artist

    lines = []
    for line in response_text.splitlines():
        clean_line = line.strip().strip('-*•1234567890. ')
        if clean_line:
            lines.append(clean_line)
    
    dna["style_imprint_lines"] = lines[:12]
    return artist

def main():
    if not SRC.exists():
        logger.error(f"Cannot find {SRC}. Make sure artists.json exists.")
        return

    data = json.loads(SRC.read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(data)} artists.")

    # Process all artists with missing or empty style_imprint_lines
    artists_to_process = []
    for artist in data:
        if not artist.get("dna", {}).get("style_imprint_lines"):
            artists_to_process.append(artist)
            
    if not artists_to_process:
        logger.info("All artists already have style imprint lines.")
        return
        
    logger.info(f"Generating imprint lines for {len(artists_to_process)} artists...")
    
    # Process efficiently in parallel (batch per artist). Maximum 5 concurrent calls.
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(generate_lines_for_artist, artist): artist for artist in artists_to_process}
        
        count = 0
        for future in as_completed(futures):
            count += 1
            updated_artist = future.result()
            
            # Update the original dataset
            for i, a in enumerate(data):
                if a.get("name") == updated_artist.get("name"):
                    data[i] = updated_artist
                    break
            
            logger.info(f"[{count}/{len(artists_to_process)}] Completed: {updated_artist.get('name')}")
            
            # Save checkpoints
            if count % 10 == 0:
                SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                logger.info(f"Saved partial progress: {count} artists updated.")

    # Final save
    SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Generation complete. Full dataset saved.")

if __name__ == "__main__":
    main()
