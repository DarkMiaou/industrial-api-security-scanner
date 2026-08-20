from conftest import bearer, token_for
from fastapi.testclient import TestClient


def test_health_exposes_current_profile(
    vulnerable_client: TestClient,
    hardened_client: TestClient,
) -> None:
    assert vulnerable_client.get("/health").json() == {
        "status": "healthy",
        "profile": "vulnerable",
    }
    assert hardened_client.get("/health").json() == {
        "status": "healthy",
        "profile": "hardened",
    }


def test_reset_is_protected_and_restores_exact_initial_state(
    vulnerable_client: TestClient,
) -> None:
    assert vulnerable_client.post("/demo/reset").status_code == 403

    guest = token_for(vulnerable_client, "guest")
    vulnerable_client.post("/pumps/pump-001/start", headers=bearer(guest))
    response = vulnerable_client.post(
        "/demo/reset",
        headers={"X-Demo-Key": "test-reset-key"},
    )

    assert response.status_code == 200
    state = response.json()
    assert state["pumps"] == [
        {"id": "pump-001", "zone": "A", "status": "stopped"},
        {"id": "pump-002", "zone": "B", "status": "running"},
    ]
    assert state["telemetry"] == {
        "pressure_bar": 2.5,
        "flow_l_min": 120,
        "level_percent": 65,
        "emergency_stop": False,
        "setpoint_bar": 2.5,
    }


def test_telemetry_is_public_only_in_vulnerable_profile(
    vulnerable_client: TestClient,
    hardened_client: TestClient,
) -> None:
    assert vulnerable_client.get("/telemetry").status_code == 200
    assert vulnerable_client.get(
        "/telemetry", headers={"Authorization": "Bearer invalid"}
    ).status_code == 200
    assert hardened_client.get("/telemetry").status_code == 401
    assert hardened_client.get(
        "/telemetry", headers={"Authorization": "Bearer invalid"}
    ).status_code == 401

    operator = token_for(hardened_client, "operator-a")
    assert hardened_client.get("/telemetry", headers=bearer(operator)).status_code == 200


def test_hardened_authentication_is_rate_limited(
    hardened_client: TestClient,
    vulnerable_client: TestClient,
) -> None:
    payload = {"username": "unknown", "password": "invalid"}

    hardened_statuses = [
        hardened_client.post("/auth/token", json=payload).status_code for _ in range(8)
    ]
    vulnerable_statuses = [
        vulnerable_client.post("/auth/token", json=payload).status_code for _ in range(8)
    ]

    assert hardened_statuses[:5] == [401] * 5
    assert hardened_statuses[5:] == [429] * 3
    assert vulnerable_statuses == [401] * 8
