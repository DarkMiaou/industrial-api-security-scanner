"""Base scanner with the mandatory IASS-OT HTTP safety envelope."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import requests

from config import settings
from core.redaction import redact, response_excerpt
from core.request_budget import RequestBudget
from core.safe_http import SafeScannerClient
from core.target_policy import ResolvedTarget
from schemas.test_result_schemas import TestResultCreate


class BaseScanner(ABC):
    """Common bounded HTTP and evidence behavior for every scanner engine."""

    def __init__(
        self,
        target: ResolvedTarget,
        budget: RequestBudget | None = None,
    ) -> None:
        if not isinstance(target, ResolvedTarget):
            raise TypeError("Scanners require a server-resolved target")

        self.target = target
        self.budget = budget or RequestBudget(settings.SCANNER_REQUEST_BUDGET)
        self.client = SafeScannerClient(
            target=target,
            budget=self.budget,
            connect_timeout=settings.SCANNER_CONNECTION_TIMEOUT,
            read_timeout=settings.SCANNER_READ_TIMEOUT,
            max_response_bytes=settings.SCANNER_MAX_RESPONSE_BYTES,
            user_agent=f"{settings.APP_NAME}/{settings.VERSION}",
        )

    @property
    def request_count(self) -> int:
        """Number of outbound attempts consumed by the shared scan budget."""
        return self.budget.count

    def make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> requests.Response:
        """Delegate to the only network path authorized for scanners."""
        return self.client.request(method, endpoint, **kwargs)

    def authenticate_gateway(
        self,
        username: str,
        password: str,
    ) -> tuple[str, dict[str, Any]]:
        """Obtain one demo gateway token while returning only redacted evidence."""
        credentials = {"username": username, "password": password}
        response = self.make_request("POST", "/auth/token", json=credentials)
        evidence = self.collect_evidence(response, payload=credentials)
        if response.status_code != 200:
            raise RuntimeError(
                f"Gateway authentication failed for {username}: HTTP {response.status_code}"
            )

        try:
            token = response.json()["access_token"]
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Gateway authentication returned no token for {username}"
            ) from exc
        if not isinstance(token, str) or not token:
            raise RuntimeError(
                f"Gateway authentication returned an invalid token for {username}"
            )
        return token, evidence

    def reset_gateway(self) -> dict[str, Any]:
        """Restore the deterministic station state without exposing the demo key."""
        response = self.make_request(
            "POST",
            "/demo/reset",
            headers={"X-Demo-Key": settings.OT_DEMO_RESET_KEY},
        )
        evidence = self.collect_evidence(response)
        if response.status_code != 200:
            raise RuntimeError(f"Gateway reset failed: HTTP {response.status_code}")
        return evidence

    def collect_evidence(
        self,
        response: requests.Response,
        payload: Any | None = None,
        **additional_data: Any,
    ) -> dict[str, Any]:
        """Create a size-bounded, recursively redacted evidence object."""
        evidence: dict[str, Any] = {
            "status_code": response.status_code,
            "response_time_ms": round(
                getattr(response, "request_time", 0.0) * 1000,
                2,
            ),
            "response_length": len(response.content),
            "response_excerpt": response_excerpt(
                response.text,
                settings.SCANNER_EVIDENCE_EXCERPT_CHARS,
            ),
            "headers": redact(dict(response.headers)),
        }
        if payload is not None:
            evidence["payload"] = redact(payload)
        evidence.update(redact(additional_data))
        return evidence

    @abstractmethod
    def scan(self) -> TestResultCreate:
        """Execute one security control."""
