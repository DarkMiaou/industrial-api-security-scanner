from conftest import bearer, token_for
from fastapi.testclient import TestClient


def test_hardened_command_creates_complete_correlated_audit_event(
    hardened_client: TestClient,
) -> None:
    supervisor = token_for(hardened_client, "supervisor")
    admin = token_for(hardened_client, "admin")
    correlation_id = "audit-test-001"

    command = hardened_client.post(
        "/pumps/pump-001/start",
        headers={**bearer(supervisor), "X-Correlation-ID": correlation_id},
    )
    assert command.status_code == 200

    audit = hardened_client.get(
        "/audit/events",
        params={"correlation_id": correlation_id},
        headers=bearer(admin),
    )
    assert audit.status_code == 200
    assert audit.json()["events"] == [
        {
            "actor": "supervisor",
            "action": "pump.start",
            "resource": "pump-001",
            "result": "allowed",
            "timestamp": audit.json()["events"][0]["timestamp"],
            "correlation_id": correlation_id,
        }
    ]


def test_vulnerable_profile_does_not_create_command_audit(
    vulnerable_client: TestClient,
) -> None:
    supervisor = token_for(vulnerable_client, "supervisor")
    admin = token_for(vulnerable_client, "admin")
    correlation_id = "missing-audit-001"

    vulnerable_client.post(
        "/pumps/pump-001/start",
        headers={**bearer(supervisor), "X-Correlation-ID": correlation_id},
    )
    audit = vulnerable_client.get(
        "/audit/events",
        params={"correlation_id": correlation_id},
        headers=bearer(admin),
    )
    assert audit.json() == {"events": []}


def test_ot_command_rate_limit_is_deterministic(
    hardened_client: TestClient,
    vulnerable_client: TestClient,
) -> None:
    hardened_supervisor = token_for(hardened_client, "supervisor")
    vulnerable_supervisor = token_for(vulnerable_client, "supervisor")

    hardened_responses = [
        hardened_client.post(
            "/pumps/pump-001/start", headers=bearer(hardened_supervisor)
        )
        for _ in range(6)
    ]
    vulnerable_responses = [
        vulnerable_client.post(
            "/pumps/pump-001/start", headers=bearer(vulnerable_supervisor)
        )
        for _ in range(8)
    ]

    assert [response.status_code for response in hardened_responses] == [200] * 5 + [429]
    assert hardened_responses[-1].headers["Retry-After"]
    assert [response.status_code for response in vulnerable_responses] == [200] * 8


def test_sqli_simulation_is_non_destructive_and_profile_dependent(
    hardened_client: TestClient,
    vulnerable_client: TestClient,
) -> None:
    hardened_operator = token_for(hardened_client, "operator-a")
    vulnerable_operator = token_for(vulnerable_client, "operator-a")

    baseline = vulnerable_client.get(
        "/maintenance/orders",
        params={"id": "100"},
        headers=bearer(vulnerable_operator),
    )
    assert baseline.status_code == 200
    assert len(baseline.json()["orders"]) == 1

    vulnerable_true = vulnerable_client.get(
        "/maintenance/orders",
        params={"id": "100 OR 1=1"},
        headers=bearer(vulnerable_operator),
    )
    vulnerable_quote = vulnerable_client.get(
        "/maintenance/orders",
        params={"id": "100'"},
        headers=bearer(vulnerable_operator),
    )
    hardened_attempt = hardened_client.get(
        "/maintenance/orders",
        params={"id": "100 OR 1=1"},
        headers=bearer(hardened_operator),
    )

    assert len(vulnerable_true.json()["orders"]) == 2
    assert vulnerable_quote.status_code == 500
    assert "SQL syntax error" in vulnerable_quote.json()["detail"]
    assert hardened_attempt.status_code == 422

