import pytest

from ashariri.config import Settings
from ashariri.llm import ScriptedLLM
from ashariri.service import Service
from ashariri.store.sqlite_store import SQLiteStore


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(llm="scripted", embedder="hash", store="sqlite", sqlite_path=tmp_path / "test.db")


@pytest.fixture
def service(settings) -> Service:
    svc = Service.from_settings(settings, llm=ScriptedLLM(), store=SQLiteStore(":memory:", settings.embedding_dim))
    svc.ingest()
    return svc


async def collect(service: Service, question: str, session: str = "test-session", **kw) -> list[dict]:
    return [e async for e in service.ask(question, session, **kw)]
