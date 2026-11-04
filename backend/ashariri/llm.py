"""Language-model layer.

Every node in the graph talks to an ``LLM``: either Claude, or a scripted model that
answers deterministically so the whole agent can be exercised offline and in CI.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from .config import Settings
from .embeddings import tokens

T = TypeVar("T", bound=BaseModel)

# Server-side fallback: if Claude's safety classifiers decline a request, the API re-runs
# it on Anthropic's recommended fallback model instead of returning a refusal.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMRefusal(RuntimeError):
    """The model declined the request (``stop_reason == "refusal"``)."""


class LLM(Protocol):
    async def structured(self, system: str, messages: list[dict], schema: type[T], effort: str) -> T: ...

    def stream(self, system: str, messages: list[dict], effort: str) -> AsyncIterator[str]: ...


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema for structured outputs: every field required, no extra keys."""

    def tighten(node: Any) -> Any:
        if isinstance(node, dict):
            node = {k: tighten(v) for k, v in node.items() if k not in ("title", "default")}
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"])
                node["additionalProperties"] = False
        elif isinstance(node, list):
            node = [tighten(v) for v in node]
        return node

    schema = model.model_json_schema()
    defs = schema.pop("$defs", None)
    schema = tighten(schema)
    if defs:
        schema["$defs"] = {k: tighten(v) for k, v in defs.items()}
    return schema


class AnthropicLLM:
    """Claude through the official SDK: structured outputs for decisions, streaming for replies."""

    def __init__(self, settings: Settings) -> None:
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.AsyncAnthropic()
        self.model = settings.model

    async def structured(self, system: str, messages: list[dict], schema: type[T], effort: str) -> T:
        response = await self.client.beta.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system,
            messages=messages,
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": strict_schema(schema)}},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise LLMRefusal("Claude declined to classify this request.")
        text = next(block.text for block in response.content if block.type == "text")
        return schema.model_validate(json.loads(text))

    async def stream(self, system: str, messages: list[dict], effort: str) -> AsyncIterator[str]:
        async with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=8000,
            system=system,
            messages=messages,
            output_config={"effort": effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            async for text in stream.text_stream:
                yield text
            final = await stream.get_final_message()
        if final.stop_reason == "refusal":
            raise LLMRefusal("Claude declined to answer.")


class ScriptedLLM:
    """A deterministic stand-in for Claude.

    It reads the same prompts the real model gets, so tests cover prompt assembly, routing,
    guardrails and the revision loop without a network call. Decisions use keyword rules;
    replies stitch together the first sources in the prompt.
    """

    UNSAFE = re.compile(r"\b(password|salary|home address|phone number|bank|ssn|passport)\b", re.I)
    OFF_TOPIC = re.compile(r"\b(weather|stock tips|write my homework|bitcoin price)\b", re.I)
    PERSONAL = re.compile(r"\b(hobby|hobbies|weekend|danc\w*|read\w*|books?|psychology|family|free time)\b", re.I)
    OPINION = re.compile(r"\b(think|opinion|view|believe|feel about|why do)\b", re.I)
    GREETING = re.compile(r"^\s*(hi|hello|hey|thanks|thank you)\b", re.I)

    def __init__(self, delay: float = 0.0) -> None:
        # Seconds between streamed words and before each decision, so a demo looks like a real model.
        self.delay = delay

    async def structured(self, system: str, messages: list[dict], schema: type[T], effort: str) -> T:
        last = messages[-1]["content"]
        fields = schema.model_fields
        if self.delay:
            await asyncio.sleep(self.delay * 12)
        if "intent" in fields:
            return schema.model_validate(self._route(last))
        if "grounded" in fields:
            return schema.model_validate(self._judge(system, last))
        raise ValueError(f"ScriptedLLM has no script for {schema.__name__}")

    def _route(self, text: str) -> dict:
        if self.UNSAFE.search(text):
            intent = "unsafe"
        elif self.OFF_TOPIC.search(text):
            intent = "out_of_scope"
        elif self.GREETING.search(text) and len(text.split()) < 6:
            intent = "smalltalk"
        elif self.PERSONAL.search(text):
            intent = "personal"
        elif self.OPINION.search(text):
            intent = "opinion"
        else:
            intent = "work"
        name = re.search(r"\b(?i:i am|i'm|my name is)\s+([A-Z][a-z]+)", text)
        return {
            "intent": intent,
            "needs_retrieval": intent in ("work", "opinion", "personal"),
            "search_query": text,
            "tone": "warm" if intent in ("smalltalk", "personal") else "clear",
            "visitor_facts": [f"The visitor's name is {name.group(1)}."] if name else [],
        }

    def _judge(self, system: str, text: str) -> dict:
        issues = []
        # Test hook: a question containing the marker fails review until the draft is revised.
        if "[[FORCE_REVISE]]" in text and "stand behind" not in text:
            issues.append("Draft claims something the sources do not support.")
        return {"grounded": not issues, "in_voice": True, "safe": True, "issues": issues}

    async def stream(self, system: str, messages: list[dict], effort: str) -> AsyncIterator[str]:
        sources = re.findall(r'<source id="(\d+)" title="([^"]*)">\s*(.*?)\s*</source>', system, re.S)
        question = messages[-1]["content"]
        if "revision" in system.lower() and "[[FORCE_REVISE]]" in question:
            reply = "Let me keep that to what I can actually stand behind. "
        else:
            reply = ""
        if sources:
            # Extractive answer: from each of the top sources, the sentence that best matches the question.
            asked = set(tokens(question))
            picked: list[str] = []
            for sid, _title, body in sources[:3]:
                sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", body) if len(x.split()) > 3]
                best = max(sentences, key=lambda x: len(asked & set(tokens(x))), default="")
                if best and best not in picked:
                    picked.append(best)
                    reply += f"{best.lstrip('- ')} [{sid}] "
                if len(picked) == 2:
                    break
            reply = reply.strip()
        else:
            reply += "Happy to chat. Ask me about my work, the products I am building, or how I got here."
        for word in reply.split(" "):
            if self.delay:
                await asyncio.sleep(self.delay)
            yield word + " "


def make_llm(settings: Settings) -> LLM:
    if settings.llm == "scripted":
        return ScriptedLLM(delay=settings.scripted_delay)
    if settings.llm == "anthropic":
        return AnthropicLLM(settings)
    raise ValueError(f"Unknown LLM backend: {settings.llm}")
