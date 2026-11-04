"""Loads the twin's knowledge: markdown files with a small YAML front matter block."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)


@dataclass
class Chunk:
    id: str
    source: str
    title: str
    text: str
    url: str = ""
    kind: str = "note"
    embedding: list[float] = field(default_factory=list, repr=False)


def _split(body: str, target: int = 700) -> list[tuple[str, str]]:
    """Split on headings, then pack paragraphs into windows of roughly ``target`` characters."""
    sections: list[tuple[str, str]] = []
    heading = ""
    buffer: list[str] = []
    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            if buffer:
                sections.append((heading, "\n\n".join(buffer)))
                buffer = []
            first, _, rest = block.partition("\n")
            heading = first.lstrip("#").strip()
            block = rest.strip()
            if not block:
                continue
        if buffer and sum(len(b) for b in buffer) + len(block) > target:
            sections.append((heading, "\n\n".join(buffer)))
            buffer = []
        buffer.append(block)
    if buffer:
        sections.append((heading, "\n\n".join(buffer)))
    return sections


def load_knowledge(directory: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(directory.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta: dict = {}
        match = FRONT_MATTER.match(raw)
        if match:
            meta = yaml.safe_load(match.group(1)) or {}
            raw = raw[match.end() :]
        title = str(meta.get("title", path.stem.replace("-", " ").title()))
        for index, (heading, text) in enumerate(_split(raw)):
            label = f"{title} - {heading}" if heading else title
            digest = hashlib.sha1(f"{path.name}:{index}:{text}".encode()).hexdigest()[:12]
            chunks.append(
                Chunk(
                    id=f"{path.stem}-{index}-{digest}",
                    source=path.name,
                    title=label,
                    text=text,
                    url=str(meta.get("url", "")),
                    kind=str(meta.get("kind", "note")),
                )
            )
    return chunks
