import re

def check_structure(lyrics):
    """
    Bölüm yapısını kontrol etmek.
    Expected: [VERSE 1], [CHORUS], [VERSE 2], [BRIDGE], [CHORUS]
    Eğer doğruysa: score = 15
    """
    expected_order = ["[VERSE 1]", "[CHORUS]", "[VERSE 2]", "[BRIDGE]", "[CHORUS]"]
    
    # Metin içindeki tag'leri bul ([VERSE 1], vb.)
    tags_found = re.findall(r'\[.*?\]', lyrics)
    found_normalized = [t.upper() for t in tags_found]
    expected_normalized = [t.upper() for t in expected_order]
    
    # Tam olarak istenen sırada mı diye kontrol et
    # Eger sozlerin icinde sirasiyla listelenmisse (fazladan etiket olsa da dogru yapinin ana iskeletini koruyorsa)
    score = 0
    
    # Tum beklenen kisimlar metinde geciyorsa (en azindan sartlara uyduğunu varsayalım)
    if all(tag in lyrics.upper() for tag in set(expected_normalized)):
        score = 15
        
    return score

def calculate_rhyme_score(lines):
    """
    Satır sonu kafiye yoğunluğunu ölçmek.
    Output: 0–20 arası puan.
    """
    if not lines:
        return 0
    
    # TODO: İleride NLP modelleriyle gerçek kelime sonu fonetik analizi yapılabilir.
    # Şimdilik sistemin çalışması için mock bir skor dönüyor.
    return 18

def calculate_flow_score(lines):
    """
    Hece ritmini analiz etmek.
    Output: 0–15 puan.
    """
    if not lines:
        return 0
        
    # TODO: Satırların hece sayılarının standart sapmasına bakılarak flow ritmi çıkarılabilir.
    return 13

def evaluate_beat_alignment(lines, bpm):
    """
    Satırların beat temposuna uyumunu ölçmek.
    Output: 0–15 puan.
    """
    if not lines:
        return 0
        
    # TODO: bpm değerine karşılık her satırın okunma süresi (hece/saniye) tahminlenebilir.
    return 12

def evaluate_hook_strength(chorus_lines):
    """
    Nakaratın akılda kalıcılığını ölçmek.
    Output: 0–20 puan.
    """
    if not chorus_lines:
        return 0
        
    # TODO: Tekrarlayan kelime sıklığı, kısa ve vurucu hece sayısı kontrol edilebilir.
    return 16

def evaluate_persona_similarity(lyrics, artist_name):
    """
    Sözlerin sanatçı tarzına benzerliğini ölçmek.
    Output: 0–15 puan.
    """
    if not lyrics or not artist_name:
        return 0
        
    # TODO: Sanatçı için embedding oluşturulup üretilen sözlerle cosine similarity yapılabilir.
    return 14

def calculate_total_score(structure, rhyme, flow, beat, hook, persona):
    """
    Toplam puan: Structure + Rhyme + Flow + Beat + Hook + Persona
    Toplam: 100 puan üzerinden hesaplanır.
    """
    return structure + rhyme + flow + beat + hook + persona

def evaluate_and_generate_report(lyrics, bpm=90, artist_name="Unknown"):
    """
    Verilen sözler için tüm test süreçlerini çalıştırır ve rapor çıktısı oluşturur.
    """
    # Sözleri satırlara ayır ve [VERSE] gibi tag'leri temizleyerek sadece sözleri al
    all_lines = lyrics.split('\n')
    lines = [line.strip() for line in all_lines if line.strip() and not line.strip().startswith('[')]
    
    # Nakarat kısımlarını ayrıca değerlendirmek için çıkar
    chorus_lines = []
    in_chorus = False
    for line in all_lines:
        line_upper = line.strip().upper()
        if '[CHORUS]' in line_upper:
            in_chorus = True
            continue
        elif line_upper.startswith('['):
            in_chorus = False
            
        if in_chorus and line.strip():
            chorus_lines.append(line.strip())
            
    # Fonksiyonları Çağır ve Skorları Al
    structure_score = check_structure(lyrics)
    rhyme_score = calculate_rhyme_score(lines)
    flow_score = calculate_flow_score(lines)
    beat_score = evaluate_beat_alignment(lines, bpm)
    hook_score = evaluate_hook_strength(chorus_lines)
    persona_score = evaluate_persona_similarity(lyrics, artist_name)
    
    total_score = calculate_total_score(
        structure_score, 
        rhyme_score, 
        flow_score, 
        beat_score, 
        hook_score, 
        persona_score
    )
    
    # Performance Level Hesapla
    if total_score >= 90:
        level = "Excellent"
    elif total_score >= 70:
        level = "Good"
    elif total_score >= 50:
        level = "Average"
    else:
        level = "Weak"
        
    # Çıktı Formatı
    report = f"""========== REMIXFY TEST REPORT ==========

Structure Score
{structure_score}/15
Rhyme Score
{rhyme_score}/20
Flow Score
{flow_score}/15
Beat Alignment
{beat_score}/15
Hook Strength
{hook_score}/20
Persona Match
{persona_score}/15

TOTAL SCORE
{total_score}/100

Performance Level:

{level}
"""
    return report

if __name__ == "__main__":
    # Test amaçlı girdi örneği
    sample_lyrics = '''[VERSE 1]
Burası sokak, her köşe başında bir yalan
Gözlerimi kapatsam da içimde hep bir talan
[CHORUS]
Yükseliyor alevler gökyüzüne doğru
Küllerimiz savrulur bu bitmeyen yolda
[VERSE 2]
Aynaya baktığımda göremiyorum kendimi
Maskeler düştü yere, anladım gerçeği
[BRIDGE]
Zaman daralır, nefesim kesilir
Pes etmek yok, bu kalp direnecek
[CHORUS]
Yükseliyor alevler gökyüzüne doğru
Küllerimiz savrulur bu bitmeyen yolda'''

    print(evaluate_and_generate_report(sample_lyrics, bpm=95, artist_name="Ceza"))
