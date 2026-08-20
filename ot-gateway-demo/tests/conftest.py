import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _settings(profile: str) -> Settings:
    return Settings(
        profile=profile,
        jwt_secret="test-gateway-secret",
        demo_reset_key="test-reset-key",
    )


@pytest.fixture
def vulnerable_client() -> TestClient:
    with TestClient(create_app(_settings("vulnerable"))) as client:
        yield client


@pytest.fixture
def hardened_client() -> TestClient:
    with TestClient(create_app(_settings("hardened"))) as client:
        yield client


def token_for(client: TestClient, username: str) -> str:
    response = client.post(
        "/auth/token",
        json={"username": username, "password": f"{username}-demo"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

