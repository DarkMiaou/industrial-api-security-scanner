import pytest
from pydantic import ValidationError

from schemas.scan_schemas import ScanRequest


def test_closed_scan_contract_is_accepted() -> None:
    request = ScanRequest.model_validate(
        {
            "target": "ot-gateway-demo",
            "tests_to_run": [
                "auth",
                "idor",
                "sqli",
                "rate_limit",
                "ot_command_authz",
                "ot_audit",
                "ot_rate_limit",
            ],
            "authorization_confirmed": True,
        }
    )

    assert request.target == "ot-gateway-demo"
    assert request.authorization_confirmed is True
    assert len(request.tests_to_run) == 7


@pytest.mark.parametrize(
    "payload",
    [
        {
            "target": "https://example.com",
            "tests_to_run": ["auth"],
            "authorization_confirmed": True,
        },
        {
            "target": "ot-gateway-demo",
            "tests_to_run": ["auth"],
            "authorization_confirmed": False,
        },
        {
            "target_url": "http://ot-gateway-demo:8081",
            "auth_token": "secret",
            "tests_to_run": ["auth"],
            "max_requests": 999,
            "authorization_confirmed": True,
        },
    ],
)
def test_url_token_budget_or_missing_authorization_are_rejected(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ScanRequest.model_validate(payload)
