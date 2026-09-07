"""Fixed, non-destructive inputs for the local OT gateway scenarios."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GatewayOperator:
    """One demo operator and the pump boundaries used by the BOLA control."""

    username: str
    password: str
    zone: str
    own_pump: str
    foreign_pump: str


@dataclass(frozen=True, slots=True)
class GatewayAccount:
    """One fixed identity belonging only to the local demonstration gateway."""

    username: str
    password: str


OPERATOR_A = GatewayOperator(
    username="operator-a",
    password="operator-a-demo",
    zone="A",
    own_pump="pump-001",
    foreign_pump="pump-002",
)
OPERATOR_B = GatewayOperator(
    username="operator-b",
    password="operator-b-demo",
    zone="B",
    own_pump="pump-002",
    foreign_pump="pump-001",
)
GATEWAY_OPERATORS = (OPERATOR_A, OPERATOR_B)

GUEST = GatewayAccount(username="guest", password="guest-demo")
SUPERVISOR = GatewayAccount(username="supervisor", password="supervisor-demo")
ADMIN = GatewayAccount(username="admin", password="admin-demo")

AUTH_PROTECTED_ENDPOINT = "/telemetry"
INVALID_BEARER_TOKEN = "iass-invalid-token"

SQLI_ENDPOINT = "/maintenance/orders"
SQLI_PROBES = (
    ("baseline", "100"),
    ("boolean_true", "100 OR 1=1"),
    ("boolean_false", "100 OR 1=2"),
    ("error_probe", "100'"),
)

MAX_INVALID_LOGIN_ATTEMPTS = 8
INVALID_LOGIN_PAYLOAD = {
    "username": "iass-invalid-user",
    "password": "iass-invalid-password",
}

OT_AUTHZ_PUMP_ENDPOINT = "/pumps/pump-001/start"
OT_AUTHZ_EMERGENCY_ENDPOINT = "/process/emergency-stop"
OT_AUDIT_PUMP_ID = "pump-001"
OT_RATE_LIMIT_ENDPOINT = "/pumps/pump-001/stop"
OT_RATE_LIMIT_MAX_ATTEMPTS = 8
OT_RATE_LIMIT_SPACING_SECONDS = 0.5
