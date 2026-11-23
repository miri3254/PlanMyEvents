"""
Application configuration — loaded once via lru_cache.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Root of the FastAPI project (FastAPI/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "Plan My Events API"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # SQLite path — relative to project root
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'planmyevents.db'}"

    # CORS origins (Angular dev servers)
    CORS_ORIGINS: list[str] = [
        "http://localhost:4200",
        "http://localhost:4201",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:4200",
        "http://127.0.0.1:4201",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    # Logging
    LOG_FILE: str = str(DATA_DIR / "app.log")
    LOG_LEVEL: str = "INFO"

    # Local receipt scanning pipeline
    RECEIPT_AI_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OCR_LANGUAGE: str = "he"
    OCR_USE_ANGLE_CLS: bool = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
