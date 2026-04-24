"""
Centralised application configuration loaded from environment / .env file.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All runtime settings are read from environment variables (or a `.env`
    file placed in the project root).  Pydantic-settings validates types and
    provides sensible defaults where appropriate.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "Remixfy v3"
    app_version: str = "3.0.0"
    debug: bool = False

    # ── OpenAI ───────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-5"
    openai_max_tokens: int = 1400
    openai_timeout: int = 60

    # ── Server ───────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Data paths ───────────────────────────────────────────────────────
    artists_json_path: str = "data/artists.json"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()
