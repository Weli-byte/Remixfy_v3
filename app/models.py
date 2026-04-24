"""
Pydantic models for request/response validation.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Mood(str, Enum):
    """Supported mood categories for remix generation."""
    DARK = "dark"
    HYPE = "hype"
    CHILL = "chill"
    EMOTIONAL = "emotional"
    AGGRESSIVE = "aggressive"
    MELODIC = "melodic"


class Language(str, Enum):
    """Supported output languages."""
    EN = "en"
    TR = "tr"


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class RemixRequest(BaseModel):
    """Payload accepted by the /remix endpoint."""

    topic: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="The main topic or theme for the remix.",
        examples=["street life in Istanbul"],
    )
    mood: Mood = Field(
        default=Mood.DARK,
        description="Desired mood of the generated lyrics.",
    )
    artist_style: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Name of an artist whose style should influence the output.",
        examples=["Eminem"],
    )
    language: Language = Field(
        default=Language.EN,
        description="Language of the generated lyrics.",
    )
    max_bars: int = Field(
        default=16,
        ge=4,
        le=64,
        description="Number of bars (lines) to generate.",
    )
    temperature: float = Field(
        default=0.9,
        ge=0.0,
        le=2.0,
        description="Sampling temperature forwarded to the LLM.",
    )


class HealthResponse(BaseModel):
    """Response model for the health-check endpoint."""
    status: str = "ok"
    version: str


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class RemixResponse(BaseModel):
    """Payload returned by the /remix endpoint."""

    lyrics: str = Field(
        ...,
        description="The generated remix lyrics.",
    )
    style_applied: Optional[str] = Field(
        default=None,
        description="The artist style that was applied, if any.",
    )
    mood: Mood = Field(
        ...,
        description="The mood used during generation.",
    )
    bars: int = Field(
        ...,
        description="Number of bars that were generated.",
    )
    model_used: str = Field(
        ...,
        description="Identifier of the LLM model used.",
    )
    prompt_tokens: int = Field(
        default=0,
        description="Number of prompt tokens consumed.",
    )
    completion_tokens: int = Field(
        default=0,
        description="Number of completion tokens consumed.",
    )


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    detail: str
