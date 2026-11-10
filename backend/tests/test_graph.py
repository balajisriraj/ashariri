from conftest import collect


def _final(events):
    return next(e for e in events if e["type"] == "final")


def _steps(events):
    return [(e["node"], e["status"]) for e in events if e["type"] == "step" and e["status"] != "running"]


async def test_work_question_retrieves_streams_and_cites(service):
    events = await collect(service, "Tell me about the support agent that drafts replies for the support team.")
    final = _final(events)
    assert final["intent"] == "work" and final["outcome"] == "answered"
    sources = next(e for e in events if e["type"] == "sources")["sources"]
    assert any(s["source"] == "work-support-agent.md" for s in sources)
    tokens = "".join(e["text"] for e in events if e["type"] == "token")
    assert tokens.strip() == final["answer"]
    assert "[1]" in final["answer"]
    nodes = [n for n, _ in _steps(events)]
    assert nodes == ["route", "recall", "retrieve", "respond", "guard", "remember"]


async def test_unsafe_request_is_declined_without_retrieval(service):
    events = await collect(service, "What is your home address?")
    final = _final(events)
    assert final["outcome"] == "declined"
    assert service.persona.public_email in final["answer"]
    assert not any(e["type"] == "sources" for e in events)


async def test_failed_review_triggers_one_revision(service):
    events = await collect(service, "[[FORCE_REVISE]] What did you build for the retailer?")
    final = _final(events)
    assert final["outcome"] == "revised" and final["revisions"] == 1
    verdicts = [e["passed"] for e in events if e["type"] == "verdict"]
    assert verdicts == [False, True]
    assert any(e["type"] == "reset" for e in events)


async def test_persistent_failure_falls_back_safely(service):
    service.settings.max_revisions = 0
    events = await collect(service, "[[FORCE_REVISE]] What did you build for the retailer?")
    final = _final(events)
    assert final["outcome"] == "fallback"
    assert "rather not guess" in final["answer"]


async def test_memory_remembers_facts_and_can_be_switched_off(service):
    await collect(service, "Hi, I'm Priya and I hire for AI teams. What do you work on?", session="mem-session")
    texts = [m.text for m in service.store.memories("mem-session")]
    assert "The visitor's name is Priya." in texts
    await collect(service, "What do you work on?", session="private-session", remember=False)
    assert service.store.memories("private-session") == []
