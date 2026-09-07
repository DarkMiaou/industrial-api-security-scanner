"""Central redaction helpers for logs, evidence and response excerpts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


REDACTED = "[REDACTED]"
_SENSITIVE_NAMES = {
    "authorization",
    "cookie",
    "setcookie",
    "token",
    "accesstoken",
    "refreshtoken",
    "authtoken",
    "password",
    "passwd",
    "secret",
    "secretkey",
    "apikey",
    "xapikey",
    "key",
}
_BEARER_PATTERN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")
_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(\b(?:access[_-]?token|refresh[_-]?token|auth[_-]?token|password|passwd|"
    r"secret(?:[_-]?key)?|api[_-]?key)\b[\"']?\s*[:=]\s*[\"']?)([^\s,\"'}]+)"
)


def _normalized_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def is_sensitive_key(key: object) -> bool:
    raw_key = str(key).lower()
    normalized = _normalized_key(raw_key)
    fragments = set(filter(None, re.split(r"[^a-z0-9]+", raw_key)))
    return normalized in _SENSITIVE_NAMES or normalized.endswith(
        ("token", "password", "passwd", "secret", "secretkey", "apikey")
    ) or bool(fragments & {"authorization", "cookie", "token", "password", "secret", "key"})


def redact_text(value: str) -> str:
    """Redact common credentials embedded in otherwise free-form text."""
    value = _BEARER_PATTERN.sub(rf"\1{REDACTED}", value)
    return _ASSIGNMENT_PATTERN.sub(rf"\1{REDACTED}", value)


def redact(value: Any) -> Any:
    """Return a JSON-compatible recursively redacted copy."""
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if is_sensitive_key(key) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def response_excerpt(body: str, max_characters: int = 500) -> str:
    """Redact a response body before limiting the stored excerpt."""
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        safe_body = redact_text(body)
    else:
        safe_body = json.dumps(redact(parsed), ensure_ascii=False, separators=(",", ":"))
    return safe_body[:max_characters]
