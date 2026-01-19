"""Unit tests for parser_helper module."""

from types import SimpleNamespace
import core.parsers.parser_helper as ph


def test_get_parser_for_known_email(monkeypatch):
    """Test that the correct parser is returned for a known email address."""
    fake_bank = "FAKEBANK"
    fake_emails = {fake_bank: ["alerts@fake.com", "no-reply@fakebank.com"]}
    fake_parser = SimpleNamespace(name="fake_parser")
    fake_parsers = {fake_bank: fake_parser}

    monkeypatch.setattr(ph, "bank_emails", fake_emails)
    monkeypatch.setattr(ph, "PARSERS", fake_parsers)

    parser = ph.ParserHelper.get_parser_for_email("Alerts <alerts@fake.com>")
    assert parser is fake_parser


def test_no_match_returns_none(monkeypatch):
    """Test that None is returned when no parser matches the email address."""
    monkeypatch.setattr(ph, "bank_emails", {"B": ["a@b.com"]})
    monkeypatch.setattr(ph, "PARSERS", {})

    assert ph.ParserHelper.get_parser_for_email("someone@else.com") is None
