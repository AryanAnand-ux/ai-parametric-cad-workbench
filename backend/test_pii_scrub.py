"""Unit tests for PII scrubber in llm_service."""
from services.llm_service import scrub_pii


def test_scrub_pii_redacts_email():
    text = "Contact me at engineer@example.com for the bracket"
    out = scrub_pii(text)
    assert "engineer@example.com" not in out
    assert "[REDACTED:EMAIL]" in out


def test_scrub_pii_redacts_phone():
    text = "Call +1-555-123-4567 about the 40mm box"
    out = scrub_pii(text)
    assert "555-123-4567" not in out
    assert "[REDACTED:PHONE]" in out
    assert "40mm" in out


def test_scrub_pii_redacts_secrets():
    for secret in ("sk-abcdef1234567890", "ghp_abcdefgh12345678", "Bearer mytoken123456"):
        out = scrub_pii(f"key={secret}")
        assert secret not in out
        assert "[REDACTED:SECRET]" in out
