"""HTTP API. The chat endpoint streams the agent's events as Server-Sent Events."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .config import Settings, get_settings
from .llm import LLMRefusal
from .service import Service

log = logging.getLogger("ashariri")


class Turn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    history: list[Turn] = Field(default_factory=list, max_length=20)
    remember: bool = True


SESSION = r"^[A-Za-z0-9_-]{8,64}$"


def create_app(settings: Settings | None = None, service: Service | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = service or Service.from_settings(settings)
        app.state.service.ensure_ingested()
        yield

    app = FastAPI(title="Ashariri", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    def svc(request: Request) -> Service:
        return request.app.state.service

    @app.get("/api/health")
    async def health(request: Request) -> dict:
        s = svc(request)
        return {
            "status": "ok",
            "llm": settings.llm,
            "model": settings.model if settings.llm == "anthropic" else "scripted",
            "store": settings.store,
            "embedder": settings.embedder,
            "passages": s.store.count_chunks(),
        }

    @app.get("/api/sources")
    async def sources(request: Request) -> list[dict]:
        return svc(request).store.sources()

    @app.get("/api/memory/{session_id}")
    async def memory(session_id: str, request: Request) -> list[dict]:
        _check_session(session_id)
        return [
            {"id": m.id, "kind": m.kind, "text": m.text, "created_at": m.created_at}
            for m in svc(request).store.memories(session_id)
        ]

    @app.delete("/api/memory/{session_id}")
    async def forget(session_id: str, request: Request) -> dict:
        _check_session(session_id)
        return {"forgotten": svc(request).store.forget(session_id)}

    @app.post("/api/chat")
    async def chat(body: ChatRequest, request: Request) -> EventSourceResponse:
        service = svc(request)

        async def events():
            try:
                async for event in service.ask(
                    body.message, body.session_id, [t.model_dump() for t in body.history], body.remember
                ):
                    if await request.is_disconnected():
                        return
                    yield {"event": event["type"], "data": json.dumps(event)}
            except LLMRefusal:
                yield {
                    "event": "error",
                    "data": json.dumps({"type": "error", "message": "I can't help with that one."}),
                }
            except Exception:
                log.exception("chat failed")
                yield {
                    "event": "error",
                    "data": json.dumps({"type": "error", "message": "Something went wrong on my side. Try again?"}),
                }

        return EventSourceResponse(events())

    return app


def _check_session(session_id: str) -> None:
    import re

    if not re.match(SESSION, session_id):
        raise HTTPException(status_code=400, detail="Invalid session id.")
