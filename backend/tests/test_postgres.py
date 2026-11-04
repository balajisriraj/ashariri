"""Runs the same store contract against Postgres + pgvector when a database is available (CI does this)."""

import os

import pytest

from ashariri.embeddings import HashEmbedder
from ashariri.knowledge import Chunk

DSN = os.environ.get("ASHARIRI_TEST_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="set ASHARIRI_TEST_POSTGRES_DSN to run against pgvector")


@pytest.fixture
def store():
    from ashariri.store.postgres_store import PostgresStore

    s = PostgresStore(DSN, 64)
    s.reset_knowledge()
    s.forget("pg-session")
    return s


def test_hybrid_search_and_memory(store):
    emb = HashEmbedder(64)
    texts = {"edu": "MSc Analytics from NTU University.", "port": "Cranes and vessels at the port."}
    chunks = [Chunk(id=k, source=f"{k}.md", title=k, text=v) for k, v in texts.items()]
    for c, v in zip(chunks, emb.embed(list(texts.values())), strict=True):
        c.embedding = v
    store.add_chunks(chunks)
    assert store.count_chunks() == 2
    hits = store.search("universities", emb.embed(["universities"])[0], 2)
    assert hits[0].chunk.id == "edu" and hits[0].keyword_rank == 1

    store.add_memory("pg-session", "fact", "The visitor's name is Priya.", emb.embed(["Priya"])[0])
    assert [m.text for m in store.recall("pg-session", emb.embed(["hi"])[0], 3)] == ["The visitor's name is Priya."]
    assert store.forget("pg-session") == 1
