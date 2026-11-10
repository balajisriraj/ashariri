from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class Persona(BaseModel):
    name: str
    short_name: str
    role: str
    public_email: str = ""  # optional: without one, replies point people to a direct message
    voice: list[str]
    beliefs: list[str]
    boundaries: list[str]
    confidential_terms: list[str] = []
    # Shown by the UI. Defaults keep older persona files working.
    avatar: str = "/avatar.svg"
    tagline: str = ""
    greeting: str = "Ask about my work, what I'm building and how I think."
    suggestions: list[str] = []

    @classmethod
    def load(cls, path: Path) -> Persona:
        persona = cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        # The real internal names stay out of git: a local list, next to the persona, adds to the placeholders.
        local = path.parent / "confidential.local.yaml"
        if local.exists():
            persona.confidential_terms += [
                t
                for t in yaml.safe_load(local.read_text(encoding="utf-8")) or []
                if t not in persona.confidential_terms
            ]
        return persona

    @property
    def contact(self) -> str:
        return f"email me at {self.public_email}" if self.public_email else "message me directly"

    def public(self) -> dict:
        """What the UI may show. Never includes the boundaries or the confidential terms."""
        return {
            "name": self.name,
            "short_name": self.short_name,
            "role": self.role,
            "avatar": self.avatar,
            "tagline": self.tagline or f"{self.short_name}'s digital twin",
            "greeting": self.greeting,
            "suggestions": self.suggestions,
        }

    def brief(self) -> str:
        bullet = "\n".join
        return (
            f"You are {self.name}'s digital twin, speaking as {self.short_name} ({self.role}).\n\n"
            f"How you speak:\n{bullet('- ' + v for v in self.voice)}\n\n"
            f"What you believe:\n{bullet('- ' + b for b in self.beliefs)}\n\n"
            f"Hard boundaries:\n{bullet('- ' + b for b in self.boundaries)}\n"
            f"- Contact: point people to {self.contact}."
        )
