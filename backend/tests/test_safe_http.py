from unittest.mock import patch

import pytest
import requests

from core.request_budget import RequestBudget, RequestBudgetExceeded
from core.safe_http import ResponseTooLarge, SafeScannerClient
from core.target_policy import TargetKey, TargetPolicy


def _response(
    body: bytes = b'{"status":"ok"}',
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.headers.update(headers or {})
    response.encoding = "utf-8"
    response._content = body
    response._content_consumed = True
    return response


def _client(
    *,
    budget: RequestBudget | None = None,
    max_response_bytes: int = 1_048_576,
) -> SafeScannerClient:
    return SafeScannerClient(
        target=TargetPolicy.resolve(TargetKey.OT_GATEWAY_DEMO),
        budget=budget or RequestBudget(),
        max_response_bytes=max_response_bytes,
    )


def test_request_forces_origin_timeouts_streaming_and_redirect_policy() -> None:
    client = _client()

    with patch.object(client.session, "request", return_value=_response()) as request:
        response = client.request(
            "GET",
            "/health",
            timeout=999,
            allow_redirects=True,
            stream=False,
            proxies={"http": "http://example.com:3128"},
        )

    assert response.json() == {"status": "ok"}
    request.assert_called_once_with(
        method="GET",
        url="http://ot-gateway-demo:8081/health",
        timeout=(3, 5),
        allow_redirects=False,
        stream=True,
    )
    assert client.session.trust_env is False


def test_redirect_response_is_returned_without_being_followed() -> None:
    client = _client()
    redirect = _response(status_code=302, headers={"Location": "https://example.com"})

    with patch.object(client.session, "request", return_value=redirect):
        response = client.request("GET", "/redirect")

    assert response.status_code == 302
    assert response.history == []


@pytest.mark.parametrize(
    "response",
    [
        _response(b"small", headers={"Content-Length": "1001"}),
        _response(b"x" * 1001),
    ],
)
def test_oversized_response_is_stopped(response: requests.Response) -> None:
    client = _client(max_response_bytes=1000)

    with (
        patch.object(client.session, "request", return_value=response),
        pytest.raises(ResponseTooLarge),
    ):
        client.request("GET", "/large")


def test_the_next_request_is_never_emitted_after_budget_exhaustion() -> None:
    budget = RequestBudget(limit=2)
    client = _client(budget=budget)

    with patch.object(client.session, "request", return_value=_response()) as request:
        client.request("GET", "/one")
        client.request("GET", "/two")
        with pytest.raises(RequestBudgetExceeded):
            client.request("GET", "/three")

    assert request.call_count == 2
    assert budget.count == 2
