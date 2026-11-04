"""Single-file storage: sqlite-vec for vectors, FTS5 for keywords. Needs no running service."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import sqlite_vec

from ..embeddings import tokens
from ..knowledge import Chunk
from .base import Hit, Memory, fuse


class SQLiteStore:
    def __init__(self, path: Path | str, dim: int) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)
        self.lock = threading.Lock()
        self.dim = dim
        self._migrate()

    def _migrate(self) -> None:
        with self.lock, self.db:
            self.db.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS chunks (
                  rowid INTEGER PRIMARY KEY, id TEXT UNIQUE, source TEXT, title TEXT,
                  url TEXT, kind TEXT, text TEXT);
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(embedding float[{self.dim}]);
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(title, text, content='chunks',
                  content_rowid='rowid',
                  tokenize='porter unicode61');
                CREATE TABLE IF NOT EXISTS memories (
                  rowid INTEGER PRIMARY KEY, session_id TEXT, kind TEXT, text TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS memories_session ON memories(session_id);
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(embedding float[{self.dim}]);
                """
            )

    # ── knowledge ──
    def reset_knowledge(self) -> None:
        with self.lock, self.db:
            self.db.execute("DELETE FROM chunks_vec")
            self.db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
            self.db.execute("DELETE FROM chunks")

    def add_chunks(self, chunks: list[Chunk]) -> None:
        with self.lock, self.db:
            for c in chunks:
                cur = self.db.execute(
                    "INSERT INTO chunks(id, source, title, url, kind, text) VALUES (?,?,?,?,?,?)",
                    (c.id, c.source, c.title, c.url, c.kind, c.text),
                )
                rowid = cur.lastrowid
                self.db.execute(
                    "INSERT INTO chunks_vec(rowid, embedding) VALUES (?, ?)",
                    (rowid, sqlite_vec.serialize_float32(c.embedding)),
                )
                self.db.execute("INSERT INTO chunks_fts(rowid, title, text) VALUES (?,?,?)", (rowid, c.title, c.text))

    def count_chunks(self) -> int:
        return self.db.execute("SELECT count(*) FROM chunks").fetchone()[0]

    def sources(self) -> list[dict]:
        rows = self.db.execute(
            "SELECT source, min(title), url, kind, count(*) FROM chunks GROUP BY source ORDER BY source"
        ).fetchall()
        return [{"source": s, "title": t.split(" - ")[0], "url": u, "kind": k, "chunks": n} for s, t, u, k, n in rows]

    def _chunk(self, row: tuple) -> Chunk:
        _, cid, source, title, url, kind, text = row
        return Chunk(id=cid, source=source, title=title, url=url, kind=kind, text=text)

    def search(self, query: str, query_vec: list[float], k: int) -> list[Hit]:
        pool = max(k * 4, 20)
        vec_rows = self.db.execute(
            "SELECT rowid FROM chunks_vec WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (sqlite_vec.serialize_float32(query_vec), pool),
        ).fetchall()
        terms = tokens(query)
        kw_rows = []
        if terms:
            match = " OR ".join(f'"{t}"' for t in terms)
            kw_rows = self.db.execute(
                "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?",
                (match, pool),
            ).fetchall()
        rowids = {r[0] for r in vec_rows} | {r[0] for r in kw_rows}
        if not rowids:
            return []
        marks = ",".join("?" * len(rowids))
        rows = self.db.execute(f"SELECT * FROM chunks WHERE rowid IN ({marks})", tuple(rowids)).fetchall()
        by_rowid = {r[0]: self._chunk(r) for r in rows}
        by_id = {c.id: c for c in by_rowid.values()}
        return fuse([by_rowid[r[0]].id for r in vec_rows], [by_rowid[r[0]].id for r in kw_rows], by_id, k)

    # ── memory ──
    def add_memory(self, session_id: str, kind: str, text: str, vec: list[float]) -> None:
        with self.lock, self.db:
            cur = self.db.execute(
                "INSERT INTO memories(session_id, kind, text) VALUES (?,?,?)", (session_id, kind, text)
            )
            self.db.execute(
                "INSERT INTO memories_vec(rowid, embedding) VALUES (?, ?)",
                (cur.lastrowid, sqlite_vec.serialize_float32(vec)),
            )

    def _memory(self, row: tuple) -> Memory:
        rowid, session_id, kind, text, created = row
        return Memory(id=rowid, session_id=session_id, kind=kind, text=text, created_at=created)

    def recall(self, session_id: str, query_vec: list[float], k: int) -> list[Memory]:
        # Facts about the visitor always come back; episodes are ranked by relevance.
        facts = self.db.execute(
            "SELECT * FROM memories WHERE session_id = ? AND kind = 'fact' ORDER BY rowid", (session_id,)
        ).fetchall()
        ranked = self.db.execute(
            """SELECT m.* FROM memories_vec v JOIN memories m ON m.rowid = v.rowid
               WHERE v.embedding MATCH ? AND k = ? AND m.session_id = ? AND m.kind = 'episode'
               ORDER BY v.distance""",
            (sqlite_vec.serialize_float32(query_vec), 50, session_id),
        ).fetchall()
        return [self._memory(r) for r in facts] + [self._memory(r) for r in ranked[:k]]

    def memories(self, session_id: str) -> list[Memory]:
        rows = self.db.execute("SELECT * FROM memories WHERE session_id = ? ORDER BY rowid", (session_id,))
        return [self._memory(r) for r in rows.fetchall()]

    def forget(self, session_id: str) -> int:
        with self.lock, self.db:
            ids = [r[0] for r in self.db.execute("SELECT rowid FROM memories WHERE session_id = ?", (session_id,))]
            for rowid in ids:
                self.db.execute("DELETE FROM memories_vec WHERE rowid = ?", (rowid,))
            self.db.execute("DELETE FROM memories WHERE session_id = ?", (session_id,))
        return len(ids)
