from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration, read from the environment (prefix ``ASHARIRI_``) or ``.env``."""

    model_config = SettingsConfigDict(env_prefix="ASHARIRI_", env_file=".env", extra="ignore")

    # "anthropic" talks to Claude; "scripted" is a deterministic offline model for tests and demos.
    llm: str = "anthropic"
    model: str = "claude-opus-5-5"
    scripted_delay: float = 0.0
    # Effort per role: routing and judging are short, structured calls; replies get more room.
    router_effort: str = "low"
    judge_effort: str = "low"
    reply_effort: str = "medium"

    # "sqlite" needs no infrastructure; "postgres" uses pgvector (see docker-compose.yml).
    store: str = "sqlite"
    sqlite_path: Path = ROOT / "data" / "ashariri.db"
    postgres_dsn: str = "postgresql://ashariri:ashariri@localhost:5432/ashariri"

    # "fastembed" runs a small local embedding model (bge-small, CPU); "hash" is dependency-free and
    # deterministic, used by the unit tests.
    embedder: str = "fastembed"
    embedding_dim: int = 384

    knowledge_dir: Path = ROOT / "knowledge"
    # Point these at your own files (see "Make it yours" in the README); the defaults are a fictional example.
    persona_path: Path = ROOT / "persona" / "example.yaml"
    retrieve_k: int = 6
    max_revisions: int = 1
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
