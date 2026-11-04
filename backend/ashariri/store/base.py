"""Storage contract shared by the SQLite and Postgres backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..knowledge import Chunk

# Reciprocal rank fusion constant: dampens the advantage of the very top ranks so that
# a passage ranked well by both searches beats one ranked first by only one of them.
RRF_K = 60


@dataclass
class Hit:
    chunk: Chunk
    score: float
    vector_rank: int | None = None
    keyword_rank: int | None = None


@dataclass
class Memory:
    id: int
    session_id: str
    kind: str  # "episode" (what was discussed) or "fact" (what the visitor told us)
    text: str
    created_at: str


class Store(Protocol):
    def reset_knowledge(self) -> None: ...

    def add_chunks(self, chunks: list[Chunk]) -> None: ...

    def count_chunks(self) -> int: ...

    def sources(self) -> list[dict]: ...

    def search(self, query: str, query_vec: list[float], k: int) -> list[Hit]: ...

    def add_memory(self, session_id: str, kind: str, text: str, vec: list[float]) -> None: ...

    def recall(self, session_id: str, query_vec: list[float], k: int) -> list[Memory]: ...

    def memories(self, session_id: str) -> list[Memory]: ...

    def forget(self, session_id: str) -> int: ...


def fuse(vector_ids: list[str], keyword_ids: list[str], by_id: dict[str, Chunk], k: int) -> list[Hit]:
    """Combine two ranked id lists with reciprocal rank fusion."""
    scores: dict[str, Hit] = {}
    for rank, cid in enumerate(vector_ids, 1):
        hit = scores.setdefault(cid, Hit(by_id[cid], 0.0))
        hit.score += 1 / (RRF_K + rank)
        hit.vector_rank = rank
    for rank, cid in enumerate(keyword_ids, 1):
        hit = scores.setdefault(cid, Hit(by_id[cid], 0.0))
        hit.score += 1 / (RRF_K + rank)
        hit.keyword_rank = rank
    return sorted(scores.values(), key=lambda h: h.score, reverse=True)[:k]
