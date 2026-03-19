from __future__ import annotations

from dataclasses import dataclass
import os


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    api_host: str
    api_port: int
    cors_origin: str
    ollama_model: str
    ollama_base_url: str | None
    agent1_use_llm: bool
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_default_category: str


def load_settings() -> Settings:
    return Settings(
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=_as_int(os.getenv("API_PORT"), 8000),
        cors_origin=os.getenv("CORS_ORIGIN", "http://localhost:3000"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL"),
        agent1_use_llm=_as_bool(os.getenv("AGENT1_USE_LLM"), True),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=_as_int(os.getenv("DB_PORT"), 3306),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_name=os.getenv("DB_NAME", "ricettario"),
        db_default_category=os.getenv("DB_DEFAULT_CATEGORY", "Importazione PDF"),
    )
