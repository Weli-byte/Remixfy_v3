<![CDATA[<div align="center">

# Remixfy v3

**A multi-layered AI engine that generates structurally valid, rhyme-dense, beat-aligned rap lyrics with per-artist style fidelity.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai&logoColor=white)](https://openai.com)

</div>

---

## Overview

Remixfy v3 is not a prompt wrapper. It is a **hybrid rule-based + neural generation system** that orchestrates **25+ specialized modules** in a deterministic pipeline — from corpus-driven style analysis to post-generation rhyme validation with closed-loop retry.

- **289 artists** across 5 genres, each with empirically computed style DNA
- **Semantic retrieval** (sentence-transformers + kNN) for theme-aware reference injection
- **6 independent validators** that enforce structure, rhyme, rhythm, and beat alignment
- **Automatic retry** with constraint-specific LLM feedback on validation failure

---

## Core Idea

> The LLM is one component, not the system.  
> Raw generation is validated, scored, and refined by deterministic engines that understand music structure.

---

## System Architecture

```
User Input (artist, genre, themes, BPM, emotion)
    │
    ▼
┌─────────────────────────────────────────┐
│  PRE-GENERATION (15 analysis engines)   │
│                                         │
│  Style Embedding → Persona Engine       │
│  Neural Flow → Beat Emphasis            │
│  Delivery Simulation → Stage Energy     │
│  Audience Hook → BPM Profile            │
│  Flow Clustering (KMeans, k=4)          │
│  Semantic Retrieval (MiniLM + kNN)      │
│  Emotion Curve → Punchline Planner      │
│  Multi Rhyme Bank → Bar Structure       │
└──────────────┬──────────────────────────┘
               ▼
┌──────────────────────────┐
│  PROMPT BUILDER (≤8K ch) │  ← All profiles + constraints + retrieved lines
└──────────────┬───────────┘
               ▼
┌──────────────────────────┐
│  GPT-4.1 GENERATION      │  ← temp=0.85, freq_penalty=0.6
└──────────────┬───────────┘
               ▼
┌─────────────────────────────────────────┐
│  POST-GENERATION (6 validators)         │
│                                         │
│  Structure → Phonetic Rhyme → Neural    │
│  Rhyme → Rhyme Quality → Syllable       │
│  Rhythm → Beat Grid Alignment           │
│                                         │
│  ✗ Failed? → Retry with targeted prompt │
│  ✓ Passed? → Hook injection → Output    │
└─────────────────────────────────────────┘
```

---

## Key Components

### Style & Persona
- **Style Embedding Engine** — Mean corpus embedding (384-dim, MiniLM) per artist; biases retrieval 60/40 topic/style
- **Persona Engine** — Word-frequency analysis → archetype classification (romantic antihero / unstoppable boss / street philosopher)
- **Delivery Simulation** — Pause ratio, breath intervals, delivery style (rapid fire / controlled / lyrical)

### Flow Analysis
- **Flow Cluster Engine** — KMeans (scikit-learn) clusters corpus lines into 4 flow types: short, question-driven, aggressive, narrative
- **Neural Flow Engine** — Syllable-level profiling: avg syllables, pause ratio, dominant bar pattern (e.g., `4-3-4`)
- **Flow Pattern Extractor** — Break style detection, punchline position identification from line-length distributions

### Generation Control
- **Semantic Vector Store** — `all-MiniLM-L6-v2` embeddings + `NearestNeighbors` (cosine); multi-query deduplication
- **Emotion Curve Engine** — Maps intensity (1–10) to per-section emotional roles (narration → explosion → peak)
- **Stage Energy Engine** — Numeric energy scores per section: Verse1=4, Chorus=8, Bridge=3, Final=10

---

## Rhyme & Flow System

Three-layer post-generation rhyme stack:

| Layer | Engine | Method |
|-------|--------|--------|
| 1 | Phonetic Rhyme Validator | Last-3-char matching, ≥40% density required |
| 2 | Neural Rhyme Engine | Phonetic similarity beyond character matching |
| 3 | Rhyme Quality Engine | Density + internal rhyme detection |

Pre-generation: **Multi Rhyme Engine** mines the corpus for recurring 4-char suffix patterns (≥3 occurrences) and injects them as rhyme suggestions.

Each failed layer triggers a **targeted retry** — the LLM receives specific feedback ("rhyme density was 28%, increase to ≥40%") rather than a generic re-prompt.

---

## BPM & Rhythm

| BPM | Style | Syllables/Line |
|:---:|-------|:--------------:|
| <95 | Boom-bap | 12–16 |
| 95–109 | Old-school | 11–14 |
| 110–124 | Trap | 10–13 |
| 125–139 | Fast trap | 9–12 |
| 140+ | Double-time | 8–11 |

- **Syllable Analyzer** validates ≥40% of lines fall within BPM-derived range
- **Beat Grid Engine** checks alignment against 4/4 time signature grid
- **Beat Emphasis Engine** maps kick (beat 1) and snare (beat 3) positions to word-stress patterns

---

## Example Output

Artist: **Blok3** · BPM: 130 · Emotion: 8/10 · Themes: sokak hayatı, mücadele

```
[VERSE 1]
Gebze sokaklarında yürürüm karanlıkta
Gözlerim kara, yüreğim ateşle sarılıkta
Her adımda bir savaş, her nefeste bir çığlık
Düşmanlar pusudan çıkar, biz dimdik ayakta
Çelik gibi irade, kırılmaz bu bağ asla
Her düşüşte kalkarız, güçleniriz fazla
Mahalle çocuğuyuz, tanırız bu caddeyi
Karanlıkta parlayan yıldızlar biz anlasana
Sırtımda kader yükü, omzumda ağır çelik
Yenilmek yok durmak yok bu savaşta biz reislik
Sokağın kanunları sert acımasız ve keskin
Ama biz daha sertiz daha kararlı gerçeksin

[CHORUS]
Sokaklar konuşur biz susarız dinleriz
Gebze'nin çocukları asla yenilmeyiz
Ateşten geçtik güçlendik yeniden
Sokaklar konuşur biz yıkılmayız hiç
Düşsek de kalkarız her gece her gündüz
Gebze sokaklarında bitmez bizim sözümüz
Çelik yürek taş bilek kırılmaz sesimiz
Sokaklar konuşur biz susarız dinleriz
```

*Visible rhyme pairs: karanlıkta/sarılıkta · asla/fazla · keskin/gerçeksin · dinleriz/yenilmeyiz*

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI + Uvicorn |
| LLM | OpenAI GPT-4.1 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Clustering | scikit-learn (KMeans) |
| Retrieval | scikit-learn (NearestNeighbors, cosine) |
| Validation | Pydantic v2 |
| Data | 289 artist profiles + lyric corpora |

---

## How to Run

```bash
# Setup
git clone https://github.com/your-username/Remixfy_v3.git && cd Remixfy_v3
pip install -r requirements.txt
cp .env.example .env   # Set OPENAI_API_KEY

# Generate artist database
python data/generate_artists.py

# CLI mode (interactive)
python cli_app.py

# API server
uvicorn app.main:app --reload
# → POST /remix, GET /artists, GET /health
```

---

## Why This Project Matters

Most "AI lyric generators" are single-prompt LLM calls with no structural awareness. They produce text that *reads like* lyrics but fails on musical fundamentals: inconsistent rhyme, drifting syllable counts, no beat alignment, no emotional arc.

Remixfy treats lyrics as a **constrained optimization problem** — the output must simultaneously satisfy structural, phonetic, rhythmic, and stylistic constraints. This is closer to how music is actually composed: within rules, not without them.

---

## Limitations

- **Rhyme detection is heuristic** — character-level matching works well for Turkish but misses slant rhymes and assonance
- **Beat alignment is approximate** — syllable counting via vowel detection, not a phonological model
- **LLM dependency** — generation requires OpenAI API; 1–5s latency per attempt, retries add cost

---

## Vision

Lyrics are layer one. The architecture is designed to extend toward **flow timing** (syllable-to-beat mapping), **beat generation** (BPM-aware instrumentals), and **vocal synthesis** (style-conditioned TTS). Each layer inherits constraints from the previous — word choice drives timing, timing drives beat selection, beats drive vocal phrasing.

The goal: an AI system that understands music as structure, not just text.

---

<div align="center">

**Remixfy v3** · 2024–2026

</div>
]]>
