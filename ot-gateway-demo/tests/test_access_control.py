from conftest import bearer, token_for
from fastapi.testclient import TestClient


def test_bola_is_present_only_in_vulnerable_profile(
    vulnerable_client: TestClient,
    hardened_client: TestClient,
) -> None:
    vulnerable_operator = token_for(vulnerable_client, "operator-a")
    hardened_operator = token_for(hardened_client, "operator-a")

    assert vulnerable_client.get(
        "/pumps/pump-001", headers=bearer(vulnerable_operator)
    ).status_code == 200
    assert vulnerable_client.get(
        "/pumps/pump-002", headers=bearer(vulnerable_operator)
    ).status_code == 200

    assert hardened_client.get(
        "/pumps/pump-001", headers=bearer(hardened_operator)
    ).status_code == 200
    assert hardened_client.get(
        "/pumps/pump-002", headers=bearer(hardened_operator)
    ).status_code == 403


def test_pump_command_requires_supervisor_in_hardened_profile(
    vulnerable_client: TestClient,
    hardened_client: TestClient,
) -> None:
    vulnerable_guest = token_for(vulnerable_client, "guest")
    hardened_guest = token_for(hardened_client, "guest")
    hardened_operator = token_for(hardened_client, "operator-a")
    hardened_supervisor = token_for(hardened_client, "supervisor")

    assert vulnerable_client.post(
        "/pumps/pump-001/start", headers=bearer(vulnerable_guest)
    ).status_code == 200
    assert hardened_client.post(
        "/pumps/pump-001/start", headers=bearer(hardened_guest)
    ).status_code == 403
    assert hardened_client.post(
        "/pumps/pump-001/start", headers=bearer(hardened_operator)
    ).status_code == 403
    assert hardened_client.post(
        "/pumps/pump-001/start", headers=bearer(hardened_supervisor)
    ).status_code == 200


def test_emergency_stop_requires_admin_and_explicit_confirmation(
    vulnerable_client: TestClient,
    hardened_client: TestClient,
) -> None:
    vulnerable_operator = token_for(vulnerable_client, "operator-a")
    hardened_supervisor = token_for(hardened_client, "supervisor")
    hardened_admin = token_for(hardened_client, "admin")

    assert vulnerable_client.post(
        "/process/emergency-stop", headers=bearer(vulnerable_operator)
    ).status_code == 200
    assert hardened_client.post(
        "/process/emergency-stop", headers=bearer(hardened_supervisor)
    ).status_code == 403
    assert hardened_client.post(
        "/process/emergency-stop", headers=bearer(hardened_admin)
    ).status_code == 403

    confirmed = hardened_client.post(
        "/process/emergency-stop",
        headers={
            **bearer(hardened_admin),
            "X-Confirm-Emergency-Stop": "true",
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["emergency_stop"] is True

