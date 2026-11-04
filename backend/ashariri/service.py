"""Builds the twin from settings and exposes the two things callers need: ingest and ask."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

from .config import Settings
from .embeddings import Embedder, make_embedder
from .graph import Twin
from .knowledge import load_knowledge
from .llm import LLM, make_llm
from .persona import Persona
from .store import Store, make_store


@dataclass
class Service:
    settings: Settings
    llm: LLM
    store: Store
    embedder: Embedder
    persona: Persona

    def __post_init__(self) -> None:
        self.graph = Twin(self.llm, self.store, self.embedder, self.persona, self.settings).build()

    @classmethod
    def from_settings(cls, settings: Settings, llm: LLM | None = None, store: Store | None = None) -> Service:
        return cls(
            settings=settings,
            llm=llm or make_llm(settings),
            store=store or make_store(settings),
            embedder=make_embedder(settings),
            persona=Persona.load(settings.persona_path),
        )

    def ingest(self) -> int:
        """Rebuild the knowledge index from the markdown corpus. Returns the number of passages."""
        chunks = load_knowledge(self.settings.knowledge_dir)
        for chunk, vec in zip(chunks, self.embedder.embed([f"{c.title}. {c.text}" for c in chunks]), strict=True):
            chunk.embedding = vec
        self.store.reset_knowledge()
        self.store.add_chunks(chunks)
        return len(chunks)

    def ensure_ingested(self) -> None:
        if self.store.count_chunks() == 0:
            self.ingest()

    async def ask(
        self, question: str, session_id: str, history: list[dict] | None = None, remember: bool = True
    ) -> AsyncIterator[dict]:
        """Run the graph and yield its events, ending with a ``final`` event."""
        started = time.perf_counter()
        state = {"session_id": session_id, "question": question, "history": history or [], "remember": remember}
        final: dict = {}
        async for mode, chunk in self.graph.astream(state, stream_mode=["custom", "values"]):
            if mode == "custom":
                yield chunk
            else:
                final = chunk
        yield {
            "type": "final",
            "answer": final.get("answer", ""),
            "outcome": final.get("outcome", "answered"),
            "intent": final.get("route", {}).get("intent"),
            "revisions": final.get("revisions", 0),
            "ms": round((time.perf_counter() - started) * 1000),
        }
