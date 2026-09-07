"""Bounded HTTP client used by all scanner engines."""

from __future__ import annotations

from time import monotonic
from typing import Any

import requests

from core.request_budget import RequestBudget
from core.target_policy import ResolvedTarget


class ResponseTooLarge(requests.RequestException):
    """Raised when a target response exceeds the configured safety cap."""


class SafeScannerClient:
    def __init__(
        self,
        target: ResolvedTarget,
        budget: RequestBudget,
        *,
        connect_timeout: float = 3,
        read_timeout: float = 5,
        max_response_bytes: int = 1_048_576,
        user_agent: str = "IASS-OT/1.0",
        session: requests.Session | None = None,
    ) -> None:
        self.target = target
        self.budget = budget
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_response_bytes = max_response_bytes
        self.session = session or requests.Session()
        self.session.trust_env = False
        self.session.headers.update(
            {"User-Agent": user_agent, "Accept": "application/json"}
        )

    def request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        """Emit one bounded request, without redirects or implicit retries."""
        url = self.target.url_for(endpoint)
        kwargs.pop("timeout", None)
        kwargs.pop("allow_redirects", None)
        kwargs.pop("stream", None)
        kwargs.pop("proxies", None)

        self.budget.reserve()
        started_at = monotonic()
        response = self.session.request(
            method=method,
            url=url,
            timeout=(self.connect_timeout, self.read_timeout),
            allow_redirects=False,
            stream=True,
            **kwargs,
        )
        response.request_time = monotonic() - started_at  # type: ignore[attr-defined]
        self._read_bounded_body(response)
        return response

    def _read_bounded_body(self, response: requests.Response) -> None:
        content_length = response.headers.get("Content-Length")
        if (
            content_length
            and content_length.isdigit()
            and int(content_length) > self.max_response_bytes
        ):
            response.close()
            raise ResponseTooLarge(f"Response exceeds {self.max_response_bytes} bytes")

        content = bytearray()
        try:
            for chunk in response.iter_content(chunk_size=65_536):
                if not chunk:
                    continue
                content.extend(chunk)
                if len(content) > self.max_response_bytes:
                    raise ResponseTooLarge(
                        f"Response exceeds {self.max_response_bytes} bytes"
                    )
            response._content = bytes(content)
            response._content_consumed = True
        finally:
            response.close()
