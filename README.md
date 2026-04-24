# 🎤 Remixfy v3

> AI-powered rap & hip-hop lyrics remixer built with **FastAPI** and **OpenAI**.

---

## ✨ Features

- **Topic-driven generation** – provide any theme and get original bars.
- **Mood control** – choose from *dark, hype, chill, emotional, aggressive,* or *melodic*.
- **Artist style transfer** – optionally channel the style of 10+ catalogue artists.
- **Multi-language** – generate in English or Turkish.
- **Token tracking** – every response includes prompt/completion token counts.
- **Interactive docs** – Swagger UI at `/docs`, ReDoc at `/redoc`.

---

## 📁 Project Structure

```
Remixfy_v3/
│
├── app/
│   ├── main.py            # FastAPI app, routes, lifecycle
│   ├── config.py           # Pydantic-settings configuration
│   ├── llm_engine.py       # Async OpenAI wrapper
│   ├── style_engine.py     # Artist catalogue & style resolution
│   ├── prompt_builder.py   # Chat-message construction
│   ├── models.py           # Request / response Pydantic models
│   └── utils.py            # Shared helpers
│
├── data/
│   └── artists.json        # Seed artist catalogue
│
├── .env.example            # Environment variable template
├── requirements.txt        # Pinned dependencies
└── README.md               # ← you are here
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone <repo-url> && cd Remixfy_v3
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 3. Run

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** to explore the API.

---

## 🔌 API Endpoints

| Method | Path       | Description                        |
|--------|------------|------------------------------------|
| GET    | `/health`  | Health-check (returns version)     |
| GET    | `/artists` | List available artist styles       |
| POST   | `/remix`   | Generate remix lyrics              |

### Example `/remix` request

```json
{
  "topic": "late nights in the studio",
  "mood": "dark",
  "artist_style": "Eminem",
  "language": "en",
  "max_bars": 16,
  "temperature": 0.9
}
```

---

## 🧰 Tech Stack

| Component        | Technology            |
|------------------|-----------------------|
| Web framework    | FastAPI 0.109         |
| Data validation  | Pydantic v2           |
| LLM provider     | OpenAI (gpt-4o-mini)  |
| Async HTTP       | httpx                 |
| Config           | pydantic-settings     |
| Runtime          | Python 3.11+          |

---

## 📜 License

MIT © Remixfy
