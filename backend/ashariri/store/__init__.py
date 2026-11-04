from ..config import Settings
from .base import Hit, Memory, Store


def make_store(settings: Settings) -> Store:
    if settings.store == "sqlite":
        from .sqlite_store import SQLiteStore

        return SQLiteStore(settings.sqlite_path, settings.embedding_dim)
    if settings.store == "postgres":
        from .postgres_store import PostgresStore

        return PostgresStore(settings.postgres_dsn, settings.embedding_dim)
    raise ValueError(f"Unknown store: {settings.store}")


__all__ = ["Hit", "Memory", "Store", "make_store"]
