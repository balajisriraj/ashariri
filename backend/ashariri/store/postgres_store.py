"""Production storage: Postgres with pgvector for vectors and a tsvector column for keywords."""

from __future__ import annotations

from ..embeddings import tokens
from ..knowledge import Chunk
from .base import Hit, Memory, fuse


class PostgresStore:
    def __init__(self, dsn: str, dim: int) -> None:
        import psycopg
        from pgvector.psycopg import register_vector

        self.db = psycopg.connect(dsn, autocommit=True)
        self.db.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(self.db)
        self.dim = dim
        self._migrate()

    def _migrate(self) -> None:
        self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chunks (
              id TEXT PRIMARY KEY, source TEXT, title TEXT, url TEXT, kind TEXT, text TEXT,
              embedding vector({self.dim}),
              search tsvector GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || text)) STORED);
            CREATE INDEX IF NOT EXISTS chunks_search ON chunks USING gin(search);
            CREATE INDEX IF NOT EXISTS chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
            CREATE TABLE IF NOT EXISTS memories (
              id BIGSERIAL PRIMARY KEY, session_id TEXT, kind TEXT, text TEXT,
              embedding vector({self.dim}), created_at TIMESTAMPTZ DEFAULT now());
            CREATE INDEX IF NOT EXISTS memories_session ON memories(session_id);
            """
        )

    def reset_knowledge(self) -> None:
        self.db.execute("TRUNCATE chunks")

    def add_chunks(self, chunks: list[Chunk]) -> None:
        import numpy as np

        with self.db.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks(id, source, title, url, kind, text, embedding) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                [(c.id, c.source, c.title, c.url, c.kind, c.text, np.array(c.embedding)) for c in chunks],
            )

    def count_chunks(self) -> int:
        return self.db.execute("SELECT count(*) FROM chunks").fetchone()[0]

    def sources(self) -> list[dict]:
        rows = self.db.execute(
            "SELECT source, min(title), min(url), min(kind), count(*) FROM chunks GROUP BY source ORDER BY source"
        ).fetchall()
        return [{"source": s, "title": t.split(" - ")[0], "url": u, "kind": k, "chunks": n} for s, t, u, k, n in rows]

    def search(self, query: str, query_vec: list[float], k: int) -> list[Hit]:
        import numpy as np

        pool = max(k * 4, 20)
        cols = "id, source, title, url, kind, text"
        vec_rows = self.db.execute(
            f"SELECT {cols} FROM chunks ORDER BY embedding <=> %s LIMIT %s", (np.array(query_vec), pool)
        ).fetchall()
        terms = tokens(query)
        kw_rows = []
        if terms:
            kw_rows = self.db.execute(
                f"""SELECT {cols} FROM chunks, to_tsquery('english', %s) q
                    WHERE search @@ q ORDER BY ts_rank(search, q) DESC LIMIT %s""",
                (" | ".join(terms), pool),
            ).fetchall()
        by_id = {
            r[0]: Chunk(id=r[0], source=r[1], title=r[2], url=r[3], kind=r[4], text=r[5]) for r in vec_rows + kw_rows
        }
        return fuse([r[0] for r in vec_rows], [r[0] for r in kw_rows], by_id, k)

    def add_memory(self, session_id: str, kind: str, text: str, vec: list[float]) -> None:
        import numpy as np

        self.db.execute(
            "INSERT INTO memories(session_id, kind, text, embedding) VALUES (%s,%s,%s,%s)",
            (session_id, kind, text, np.array(vec)),
        )

    def _memories(self, rows: list) -> list[Memory]:
        return [Memory(id=r[0], session_id=r[1], kind=r[2], text=r[3], created_at=str(r[4])) for r in rows]

    def recall(self, session_id: str, query_vec: list[float], k: int) -> list[Memory]:
        import numpy as np

        cols = "id, session_id, kind, text, created_at"
        facts = self.db.execute(
            f"SELECT {cols} FROM memories WHERE session_id = %s AND kind = 'fact' ORDER BY id", (session_id,)
        ).fetchall()
        episodes = self.db.execute(
            f"""SELECT {cols} FROM memories WHERE session_id = %s AND kind = 'episode'
                ORDER BY embedding <=> %s LIMIT %s""",
            (session_id, np.array(query_vec), k),
        ).fetchall()
        return self._memories(facts) + self._memories(episodes)

    def memories(self, session_id: str) -> list[Memory]:
        rows = self.db.execute(
            "SELECT id, session_id, kind, text, created_at FROM memories WHERE session_id = %s ORDER BY id",
            (session_id,),
        ).fetchall()
        return self._memories(rows)

    def forget(self, session_id: str) -> int:
        return self.db.execute("DELETE FROM memories WHERE session_id = %s", (session_id,)).rowcount
