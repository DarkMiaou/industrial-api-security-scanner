from core.redaction import REDACTED, redact, redact_text, response_excerpt


def test_nested_sensitive_values_are_redacted_case_insensitively() -> None:
    source = {
        "Authorization": "Bearer platform-secret",
        "headers": {
            "Cookie": "session=abc",
            "Set-Cookie": "session=def",
            "X-API-Key": "api-key-value",
        },
        "payload": {
            "password": "p4ssword",
            "access_token": "jwt-value",
            "nested": [{"reset_key": "reset-secret"}],
        },
        "correlation_id": "safe-correlation-value",
    }

    result = redact(source)

    assert result["Authorization"] == REDACTED
    assert result["headers"]["Cookie"] == REDACTED
    assert result["headers"]["Set-Cookie"] == REDACTED
    assert result["headers"]["X-API-Key"] == REDACTED
    assert result["payload"]["password"] == REDACTED
    assert result["payload"]["access_token"] == REDACTED
    assert result["payload"]["nested"][0]["reset_key"] == REDACTED
    assert result["correlation_id"] == "safe-correlation-value"
    assert source["payload"]["password"] == "p4ssword"


def test_free_text_bearer_and_assignments_are_redacted() -> None:
    result = redact_text("Authorization: Bearer abc.def.ghi password=hunter2")

    assert "abc.def.ghi" not in result
    assert "hunter2" not in result
    assert result.count(REDACTED) == 2


def test_json_response_is_redacted_before_excerpt_is_truncated() -> None:
    body = '{"token":"never-store-me","message":"' + ("x" * 700) + '"}'

    result = response_excerpt(body, max_characters=500)

    assert len(result) == 500
    assert "never-store-me" not in result
    assert REDACTED in result

