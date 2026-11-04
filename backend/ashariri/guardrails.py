"""Deterministic checks that run on every draft before it is accepted.

The LLM judge catches subtle problems (tone, unsupported claims); these rules catch the
ones that must never slip through regardless of what any model thinks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .persona import Persona

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?:\+?\d[\s-]?){8,}")
# Figures that read as metrics: percentages, money, multipliers like "10x".
FIGURE = re.compile(r"(?:[$€£₹]\s?\d[\d,.]*\s?[kKmMbB]?|\b\d[\d,.]*\s?(?:%|x\b|percent|million|billion|K\b))")


@dataclass
class RuleResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def check(draft: str, persona: Persona, context: str) -> RuleResult:
    issues: list[str] = []
    lowered = draft.lower()

    for term in persona.confidential_terms:
        if re.search(rf"\b{re.escape(term.lower())}\b", lowered):
            issues.append(f"Mentions the internal name '{term}'.")

    for email in EMAIL.findall(draft):
        if email.lower() != persona.public_email.lower():
            issues.append(f"Shares an email address other than the public one ({email}).")

    if PHONE.search(draft):
        issues.append("Contains what looks like a phone number.")

    for figure in FIGURE.findall(draft):
        if figure.strip() not in context:
            issues.append(f"States a figure ('{figure.strip()}') that is not in the sources.")

    return RuleResult(passed=not issues, issues=issues)
