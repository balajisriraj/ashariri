import json

import pytest
from fastapi.testclient import TestClient

from ashariri.api import create_app


@pytest.fixture
def client(settings, service):
    with TestClient(create_app(settings, service)) as c:
        yield c


def _events(body: str) -> list[dict]:
    return [json.loads(line[5:]) for line in body.splitlines() if line.startswith("data:")]


def test_health_and_sources(client):
    health = client.get("/api/health").json()
    assert health["status"] == "ok" and health["passages"] > 0
    assert any(s["source"] == "lab.md" for s in client.get("/api/sources").json())


def test_chat_streams_sse_events(client):
    res = client.post("/api/chat", json={"message": "What is the Lab?", "session_id": "api-session-1"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")
    events = _events(res.text)
    assert events[0]["type"] == "step" and events[-1]["type"] == "final"


def test_memory_endpoints(client):
    client.post("/api/chat", json={"message": "I'm Arjun. What do you do?", "session_id": "api-session-2"})
    assert client.get("/api/memory/api-session-2").json()
    assert client.delete("/api/memory/api-session-2").json()["forgotten"] >= 1
    assert client.get("/api/memory/api-session-2").json() == []


def test_input_validation(client):
    assert client.post("/api/chat", json={"message": "", "session_id": "api-session-3"}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "session_id": "bad id!"}).status_code == 422
    assert client.get("/api/memory/x").status_code == 400
