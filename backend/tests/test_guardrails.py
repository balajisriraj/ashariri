from ashariri.config import Settings
from ashariri.guardrails import check
from ashariri.persona import Persona

persona = Persona.load(Settings().persona_path)


def test_clean_reply_passes():
    assert check("I build AI products people adopt.", persona, "").passed


def test_confidential_terms_are_blocked():
    result = check("I built Project Atlas last year.", persona, "")
    assert not result.passed and "Project Atlas" in result.issues[0]


def test_only_the_public_email_is_allowed():
    assert check(f"Email {persona.public_email}.", persona, "").passed
    assert not check("Email me at someone@company.com.", persona, "").passed


def test_phone_numbers_are_blocked():
    assert not check("Call +65 9123 4567.", persona, "").passed


def test_figures_must_come_from_sources():
    assert not check("It cut costs by 40%.", persona, "No numbers here.").passed
    assert check("Developers were 19% slower.", persona, "measured 19% slower").passed
