from ashariri.embeddings import HashEmbedder, cosine
from ashariri.knowledge import Chunk, load_knowledge
from ashariri.store.base import fuse
from ashariri.store.sqlite_store import SQLiteStore


def _store(texts: dict[str, str]) -> tuple[SQLiteStore, HashEmbedder]:
    emb = HashEmbedder(64)
    store = SQLiteStore(":memory:", 64)
    chunks = [Chunk(id=k, source=f"{k}.md", title=k, text=v) for k, v in texts.items()]
    for c, v in zip(chunks, emb.embed([c.text for c in chunks]), strict=True):
        c.embedding = v
    store.add_chunks(chunks)
    return store, emb


def test_hash_embedder_is_deterministic_and_normalised():
    a, b = HashEmbedder().embed(["agents need memory", "agents need memory"])
    assert a == b
    assert abs(cosine(a, a) - 1) < 1e-9


def test_keyword_search_stems_words():
    store, emb = _store({"edu": "MSc Analytics from NTU University.", "port": "Cranes and vessels at the port."})
    hits = store.search("universities", emb.embed(["universities"])[0], 2)
    assert hits[0].chunk.id == "edu"
    assert hits[0].keyword_rank == 1


def test_hybrid_search_reports_both_ranks():
    store, emb = _store({"a": "vessel tracking red sea", "b": "reading list of books", "c": "crane productivity"})
    hits = store.search("vessel tracking", emb.embed(["vessel tracking"])[0], 3)
    assert hits[0].chunk.id == "a"
    assert hits[0].vector_rank == 1 and hits[0].keyword_rank == 1


def test_fuse_prefers_agreement():
    by_id = {k: Chunk(id=k, source="", title="", text="") for k in "abc"}
    hits = fuse(["a", "b", "c"], ["b", "a"], by_id, 3)
    assert {hits[0].chunk.id, hits[1].chunk.id} == {"a", "b"}
    assert hits[2].chunk.id == "c"


def test_reset_knowledge_clears_everything():
    store, _ = _store({"a": "one", "b": "two"})
    store.reset_knowledge()
    assert store.count_chunks() == 0


def test_memory_is_scoped_to_session_and_forgettable():
    store, emb = _store({})
    store.add_memory("s1", "fact", "The visitor's name is Priya.", emb.embed(["Priya"])[0])
    store.add_memory("s1", "episode", "They asked about vessels", emb.embed(["vessels"])[0])
    store.add_memory("s2", "fact", "Someone else", emb.embed(["else"])[0])
    recalled = [m.text for m in store.recall("s1", emb.embed(["vessels"])[0], 3)]
    assert "The visitor's name is Priya." in recalled
    assert "Someone else" not in recalled
    assert store.forget("s1") == 2
    assert store.memories("s1") == []
    assert len(store.memories("s2")) == 1


def test_knowledge_loader_splits_on_headings(tmp_path):
    (tmp_path / "x.md").write_text('---\ntitle: "X"\nurl: "https://e.g"\n---\n\n# One\nFirst.\n\n# Two\nSecond.\n')
    chunks = load_knowledge(tmp_path)
    assert [c.title for c in chunks] == ["X - One", "X - Two"]
    assert [c.text for c in chunks] == ["First.", "Second."]
    assert chunks[0].url == "https://e.g"
