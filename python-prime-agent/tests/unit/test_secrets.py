from __future__ import annotations

from prime_agent_py.providers.credentials import mask_secret, redact_text


def test_redact_does_not_log_keys() -> None:
    text = "Authorization: Bearer sk-secret-value-1234 api_key=abcd1234"
    redacted = redact_text(text, extra_secrets=["sk-secret-value-1234"])
    assert "sk-secret-value-1234" not in redacted
    assert "abcd1234" not in redacted
    assert mask_secret("abcdefghij") == "ab…ij"
