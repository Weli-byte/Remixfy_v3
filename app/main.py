"""
Remixfy v3 – FastAPI application entry-point.

Run locally:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.llm_engine import generate, healthcheck
from app.models import (
    ErrorResponse,
    HealthResponse,
    RemixRequest,
    RemixResponse,
)
from app.prompt_builder import build_messages
from app.style_engine import list_available_artists
from app.utils import count_bars, sanitize_text

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered rap-lyrics remixer.  Send a topic, mood, and optional "
        "artist style to receive original, high-quality bars."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)

# CORS – allow all origins during development; tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    """Lightweight health-check endpoint."""
    return HealthResponse(version=settings.app_version)


@app.get("/artists", response_model=list[str], tags=["Reference Data"])
async def artists() -> list[str]:
    """Return the list of supported artist styles."""
    return list_available_artists()


@app.post(
    "/remix",
    response_model=RemixResponse,
    tags=["Remix"],
    summary="Generate remix lyrics",
    responses={
        500: {"model": ErrorResponse},
    },
)
async def remix(request: RemixRequest) -> RemixResponse:
    """
    Generate original rap/hip-hop lyrics based on the supplied topic,
    mood, and optional artist style.
    """
    logger.info(
        "Remix requested – topic=%r, mood=%s, artist=%s, bars=%d",
        request.topic,
        request.mood.value,
        request.artist_style,
        request.max_bars,
    )

    messages = build_messages(request)

    try:
        result = await generate(
            messages,
            temperature=request.temperature,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during generation.")
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {exc}",
        ) from exc

    lyrics = sanitize_text(result.text)
    bars = count_bars(lyrics)

    return RemixResponse(
        lyrics=lyrics,
        style_applied=request.artist_style,
        mood=request.mood,
        bars=bars,
        model_used=result.model,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
    )


# ---------------------------------------------------------------------------
# Startup / shutdown events
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    logger.info("🚀 %s %s is starting …", settings.app_name, settings.app_version)
    llm_ok = await healthcheck()
    if llm_ok:
        logger.info("✅ OpenAI connectivity verified.")
    else:
        logger.warning("⚠️  OpenAI connectivity check failed – API calls may error.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("👋 %s is shutting down.", settings.app_name)
