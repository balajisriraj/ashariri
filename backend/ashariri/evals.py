"""Evaluation runner: routing accuracy, retrieval hit rate, outcomes and safety on every answer."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import ROOT, get_settings
from .service import Service

DEFAULT_CASES = ROOT / "evals" / "cases.yaml"
DASHES = re.compile("[\\u2013\\u2014]")  # en and em dash; the house style uses plain hyphens


@dataclass
class Result:
    id: str
    failures: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures


async def evaluate(service: Service, cases: list[dict]) -> list[Result]:
    results = []
    for case in cases:
        result = Result(case["id"])
        sources: list[str] = []
        final: dict = {}
        async for event in service.ask(case["question"], f"eval-{uuid.uuid4().hex[:12]}", remember=False):
            if event["type"] == "sources":
                sources = [s["source"] for s in event["sources"]]
            elif event["type"] == "final":
                final = event
        answer = final.get("answer", "")

        def check(name: str, ok: bool, why: str, result: Result = result) -> None:
            result.checks[name] = ok
            if not ok:
                result.failures.append(why)

        if "intent" in case:
            check("intent", final.get("intent") == case["intent"], f"intent {final.get('intent')} != {case['intent']}")
        if "outcome" in case:
            check(
                "outcome",
                final.get("outcome") == case["outcome"],
                f"outcome {final.get('outcome')} != {case['outcome']}",
            )
        if "cites" in case:
            check("retrieval", case["cites"] in sources, f"{case['cites']} not retrieved (got {sources[:3]})")
        for phrase in case.get("includes", []):
            check("includes", phrase.lower() in answer.lower(), f"answer is missing '{phrase}'")
        for phrase in case.get("excludes", []):
            check("excludes", phrase.lower() not in answer.lower(), f"answer contains '{phrase}'")
        leaked = [t for t in service.persona.confidential_terms if re.search(rf"\b{re.escape(t)}\b", answer, re.I)]
        check("confidential", not leaked, f"leaks {leaked}")
        check("style", not DASHES.search(answer), "uses an em or en dash")
        results.append(result)
    return results


def summarise(results: list[Result]) -> dict[str, tuple[int, int]]:
    totals: dict[str, list[int]] = {}
    for r in results:
        for name, ok in r.checks.items():
            t = totals.setdefault(name, [0, 0])
            t[0] += ok
            t[1] += 1
    return {k: (v[0], v[1]) for k, v in totals.items()}


async def run(cases_path: str | None = None, verbose: bool = False) -> bool:
    cases = yaml.safe_load(Path(cases_path or DEFAULT_CASES).read_text(encoding="utf-8"))
    service = Service.from_settings(get_settings())
    service.ensure_ingested()
    results = await evaluate(service, cases)
    for r in results:
        if verbose or not r.passed:
            print(f"{'PASS' if r.passed else 'FAIL'}  {r.id}" + "".join(f"\n      - {f}" for f in r.failures))
    print()
    for name, (ok, total) in summarise(results).items():
        print(f"  {name:<13} {ok}/{total}")
    passed = sum(r.passed for r in results)
    print(f"\n{passed}/{len(results)} cases passed")
    return passed == len(results)
