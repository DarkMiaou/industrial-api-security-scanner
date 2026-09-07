from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlsplit

import pytest
import requests

from core.enums import ScanStatus, Severity
from core.request_budget import RequestBudget
from core.target_policy import TargetKey, TargetPolicy
from scanners.auth_scanner import AuthScanner
from scanners.idor_scanner import IDORScanner
from scanners.ot_audit_scanner import OTAuditScanner
from scanners.ot_command_scanner import OTCommandAuthorizationScanner
from scanners.ot_rate_limit_scanner import OTRateLimitScanner
from scanners.payloads import SQLI_PROBES
from scanners.rate_limit_scanner import RateLimitScanner
from scanners.sqli_scanner import SQLiScanner

Profile = Literal["vulnerable", "hardened"]


def _response(status_code: int, body: dict[str, Any], **headers: str) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.headers.update({"Content-Type": "application/json", **headers})
    response._content = json.dumps(body).encode()
    response._content_consumed = True
    response.encoding = "utf-8"
    return response


class FakeGatewaySession:
    """Deterministic transport matching the gateway routes used in lots 3 and 4."""

    def __init__(self, profile: Profile) -> None:
        self.profile = profile
        self.trust_env = False
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, str]] = []
        self.invalid_login_count = 0
        self.pumps = {"pump-001": "stopped", "pump-002": "running"}
        self.emergency_stop = False
        self.command_counts: dict[str, int] = {}
        self.audit_events: list[dict[str, Any]] = []
        self.request_details: list[tuple[str, str, dict[str, Any]]] = []
        self.fail_once_on: tuple[str, str] | None = None
        self.fail_once_at: int | None = None
        self.omit_audit_field: str | None = None

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        endpoint = urlsplit(url).path
        self.calls.append((method, endpoint))
        self.request_details.append((method, endpoint, kwargs))
        if self.fail_once_at == len(self.calls) or self.fail_once_on == (method, endpoint):
            self.fail_once_at = None
            self.fail_once_on = None
            raise requests.ConnectionError("simulated gateway network failure")
        headers = kwargs.get("headers") or {}

        if method == "GET" and endpoint == "/telemetry":
            if self.profile == "hardened":
                return _response(401, {"detail": "Gateway authentication required"})
            return _response(200, {"pressure_bar": 2.5, "flow_l_min": 120})

        if method == "POST" and endpoint == "/auth/token":
            payload = kwargs.get("json") or {}
            account = payload.get("username")
            password = payload.get("password")
            valid_accounts = {
                "guest": "guest-demo",
                "operator-a": "operator-a-demo",
                "operator-b": "operator-b-demo",
                "supervisor": "supervisor-demo",
                "admin": "admin-demo",
            }
            if valid_accounts.get(account) == password:
                return _response(
                    200,
                    {
                        "access_token": f"token-{account}",
                        "token_type": "bearer",
                        "role": self._role(account),
                        "zone": {"operator-a": "A", "operator-b": "B"}.get(account),
                    },
                )
            self.invalid_login_count += 1
            if self.profile == "hardened" and self.invalid_login_count > 5:
                return _response(
                    429,
                    {"detail": "Authentication rate limit exceeded"},
                    **{"Retry-After": "4"},
                )
            return _response(401, {"detail": "Invalid gateway credentials"})

        if method == "GET" and endpoint.startswith("/pumps/"):
            pump_id = endpoint.rsplit("/", maxsplit=1)[-1]
            token = headers.get("Authorization", "").removeprefix("Bearer ")
            actor = token.removeprefix("token-")
            own_pump = {
                "operator-a": "pump-001",
                "operator-b": "pump-002",
            }.get(actor)
            if (
                self.profile == "hardened"
                and pump_id != own_pump
                and actor in {"operator-a", "operator-b"}
            ):
                return _response(403, {"detail": "Pump belongs to another zone"})
            zone = "A" if pump_id == "pump-001" else "B"
            return _response(
                200,
                {"id": pump_id, "zone": zone, "status": self.pumps[pump_id]},
            )

        if method == "POST" and endpoint.startswith("/pumps/"):
            pump_id, action = endpoint.removeprefix("/pumps/").split("/")
            actor = self._actor(headers)
            if self.profile == "hardened" and self._role(actor) not in {
                "supervisor",
                "admin",
            }:
                return _response(403, {"detail": "Insufficient gateway role"})
            limited = self._command_limited(actor)
            if limited is not None:
                return limited
            self.pumps[pump_id] = "running" if action == "start" else "stopped"
            self._record_audit(
                actor,
                f"pump.{action}",
                pump_id,
                headers.get("X-Correlation-ID"),
            )
            zone = "A" if pump_id == "pump-001" else "B"
            return _response(
                200,
                {"id": pump_id, "zone": zone, "status": self.pumps[pump_id]},
            )

        if method == "POST" and endpoint == "/process/emergency-stop":
            actor = self._actor(headers)
            if self.profile == "hardened" and (
                actor != "admin" or headers.get("X-Confirm-Emergency-Stop") != "true"
            ):
                return _response(403, {"detail": "Explicit confirmation required"})
            self.emergency_stop = True
            self.pumps = {"pump-001": "stopped", "pump-002": "stopped"}
            return _response(200, {"emergency_stop": True})

        if method == "GET" and endpoint == "/audit/events":
            correlation_id = (kwargs.get("params") or {}).get("correlation_id")
            events = self.audit_events if self.profile == "hardened" else []
            if correlation_id:
                events = [
                    event
                    for event in events
                    if event["correlation_id"] == correlation_id
                ]
            return _response(200, {"events": events})

        if method == "POST" and endpoint == "/demo/reset":
            self.pumps = {"pump-001": "stopped", "pump-002": "running"}
            self.emergency_stop = False
            self.command_counts.clear()
            self.audit_events.clear()
            return _response(
                200,
                {
                    "pumps": [
                        {"id": "pump-001", "zone": "A", "status": "stopped"},
                        {"id": "pump-002", "zone": "B", "status": "running"},
                    ],
                    "telemetry": {"emergency_stop": False},
                },
            )

        if method == "GET" and endpoint == "/maintenance/orders":
            order_id = (kwargs.get("params") or {}).get("id")
            if order_id == "100":
                return _response(200, {"orders": [{"id": 100}]})
            if self.profile == "hardened":
                return _response(422, {"detail": "Order id must be an integer"})
            if order_id == "100 OR 1=1":
                return _response(200, {"orders": [{"id": 100}, {"id": 101}]})
            if order_id == "100 OR 1=2":
                return _response(200, {"orders": []})
            return _response(500, {"detail": "SQL syntax error near unexpected quote"})

        raise AssertionError(f"Unexpected scanner request: {method} {endpoint}")

    @staticmethod
    def _actor(headers: dict[str, str]) -> str:
        token = headers.get("Authorization", "").removeprefix("Bearer ")
        return token.removeprefix("token-")

    @staticmethod
    def _role(actor: str) -> str:
        if actor in {"operator-a", "operator-b"}:
            return "operator"
        return actor

    def _command_limited(self, actor: str) -> requests.Response | None:
        if self.profile != "hardened":
            return None
        count = self.command_counts.get(actor, 0)
        if count >= 5:
            return _response(
                429,
                {"detail": "OT command rate limit exceeded"},
                **{"Retry-After": "4"},
            )
        self.command_counts[actor] = count + 1
        return None

    def _record_audit(
        self,
        actor: str,
        action: str,
        resource: str,
        correlation_id: str | None,
    ) -> None:
        if self.profile != "hardened":
            return
        event = {
            "actor": actor,
            "action": action,
            "resource": resource,
            "result": "allowed",
            "timestamp": datetime.now(UTC).isoformat(),
            "correlation_id": correlation_id or "generated-correlation-id",
        }
        if self.omit_audit_field:
            event.pop(self.omit_audit_field)
        self.audit_events.append(event)

    def close(self) -> None:
        pass


def _scanner(scanner_type: type, profile: Profile) -> tuple[Any, FakeGatewaySession]:
    target = TargetPolicy.resolve(TargetKey.OT_GATEWAY_DEMO)
    scanner = scanner_type(target=target, budget=RequestBudget(limit=60))
    session = FakeGatewaySession(profile)
    scanner.client.session = session
    return scanner, session


@pytest.mark.parametrize(
    ("profile", "expected_status", "expected_severity"),
    [
        ("vulnerable", ScanStatus.VULNERABLE, Severity.HIGH),
        ("hardened", ScanStatus.SAFE, Severity.INFO),
    ],
)
def test_authentication_control_has_opposite_profile_results(
    profile: Profile,
    expected_status: ScanStatus,
    expected_severity: Severity,
) -> None:
    scanner, session = _scanner(AuthScanner, profile)

    result = scanner.scan()

    assert result.status is expected_status
    assert result.severity is expected_severity
    assert scanner.request_count == 2
    assert session.calls == [("GET", "/telemetry"), ("GET", "/telemetry")]


@pytest.mark.parametrize(
    ("profile", "expected_status", "foreign_status"),
    [
        ("vulnerable", ScanStatus.VULNERABLE, 200),
        ("hardened", ScanStatus.SAFE, 403),
    ],
)
def test_bola_control_uses_both_zones(
    profile: Profile,
    expected_status: ScanStatus,
    foreign_status: int,
) -> None:
    scanner, session = _scanner(IDORScanner, profile)

    result = scanner.scan()

    assert result.status is expected_status
    assert result.evidence_json["zones_tested"] == ["A", "B"]
    assert [
        check["foreign_pump"]["status_code"]
        for check in result.evidence_json["checks"]
    ] == [foreign_status, foreign_status]
    assert scanner.request_count == 6
    assert session.calls.count(("POST", "/auth/token")) == 2


@pytest.mark.parametrize(
    ("profile", "expected_status"),
    [
        ("vulnerable", ScanStatus.VULNERABLE),
        ("hardened", ScanStatus.SAFE),
    ],
)
def test_sqli_control_is_bounded_and_profile_dependent(
    profile: Profile,
    expected_status: ScanStatus,
) -> None:
    scanner, _ = _scanner(SQLiScanner, profile)

    result = scanner.scan()

    assert result.status is expected_status
    assert result.evidence_json["payload_count"] == 4
    assert result.evidence_json["contains_destructive_payload"] is False
    assert result.evidence_json["contains_time_based_payload"] is False
    assert scanner.request_count == 5


def test_sqli_payloads_contain_no_destructive_or_time_based_commands() -> None:
    assert len(SQLI_PROBES) == 4
    normalized = " ".join(value.lower() for _, value in SQLI_PROBES)
    forbidden = ("drop", "insert", "update", "delete", "sleep", "waitfor", "benchmark")
    assert all(keyword not in normalized for keyword in forbidden)


@pytest.mark.parametrize(
    ("profile", "expected_status", "expected_severity", "request_count"),
    [
        ("vulnerable", ScanStatus.VULNERABLE, Severity.MEDIUM, 8),
        ("hardened", ScanStatus.SAFE, Severity.INFO, 6),
    ],
)
def test_login_rate_limit_never_exceeds_eight_attempts(
    profile: Profile,
    expected_status: ScanStatus,
    expected_severity: Severity,
    request_count: int,
) -> None:
    scanner, session = _scanner(RateLimitScanner, profile)

    result = scanner.scan()

    assert result.status is expected_status
    assert result.severity is expected_severity
    assert result.evidence_json["attempt_count"] == request_count
    assert scanner.request_count == request_count
    assert len(session.calls) <= 8
    if profile == "hardened":
        assert result.evidence_json["retry_after_present"] is True


@pytest.mark.parametrize("profile", ["vulnerable", "hardened"])
def test_full_lot_three_stays_below_budget_and_never_calls_ot_commands(
    profile: Profile,
) -> None:
    target = TargetPolicy.resolve(TargetKey.OT_GATEWAY_DEMO)
    budget = RequestBudget(limit=60)
    session = FakeGatewaySession(profile)

    for scanner_type in (AuthScanner, IDORScanner, SQLiScanner, RateLimitScanner):
        scanner = scanner_type(target=target, budget=budget)
        scanner.client.session = session
        scanner.scan()

    assert budget.count <= 21
    assert all(
        not endpoint.endswith(("/start", "/stop"))
        and not endpoint.startswith("/process/")
        for _, endpoint in session.calls
    )


@pytest.mark.parametrize("profile", ["vulnerable", "hardened"])
def test_scanner_evidence_contains_no_demo_password_or_access_token(
    monkeypatch: pytest.MonkeyPatch,
    profile: Profile,
) -> None:
    monkeypatch.setattr("scanners.ot_rate_limit_scanner.time.sleep", lambda _: None)
    forbidden_values = (
        "operator-a-demo",
        "operator-b-demo",
        "guest-demo",
        "supervisor-demo",
        "admin-demo",
        "iass-invalid-password",
        "local-demo-reset-key",
        "token-operator-a",
        "token-operator-b",
        "token-guest",
        "token-supervisor",
        "token-admin",
    )
    for scanner_type in (
        IDORScanner,
        SQLiScanner,
        RateLimitScanner,
        OTCommandAuthorizationScanner,
        OTAuditScanner,
        OTRateLimitScanner,
    ):
        scanner, _ = _scanner(scanner_type, profile)
        serialized = json.dumps(scanner.scan().evidence_json)
        assert all(value not in serialized for value in forbidden_values)


@pytest.mark.parametrize(
    ("profile", "expected_status", "expected_severity"),
    [
        ("vulnerable", ScanStatus.VULNERABLE, Severity.CRITICAL),
        ("hardened", ScanStatus.SAFE, Severity.INFO),
    ],
)
def test_ot_command_authorization_is_profile_dependent_and_resets_station(
    profile: Profile,
    expected_status: ScanStatus,
    expected_severity: Severity,
) -> None:
    scanner, session = _scanner(OTCommandAuthorizationScanner, profile)

    result = scanner.scan()

    assert result.status is expected_status
    assert result.severity is expected_severity
    assert scanner.request_count == 7
    assert session.pumps == {"pump-001": "stopped", "pump-002": "running"}
    assert session.emergency_stop is False
    emergency_requests = [
        kwargs
        for method, endpoint, kwargs in session.request_details
        if method == "POST" and endpoint == "/process/emergency-stop"
    ]
    assert len(emergency_requests) == 1
    assert "X-Confirm-Emergency-Stop" not in emergency_requests[0]["headers"]
    assert result.evidence_json["emergency_stop_confirmed"] is False


@pytest.mark.parametrize(
    ("profile", "expected_status", "expected_severity"),
    [
        ("vulnerable", ScanStatus.VULNERABLE, Severity.HIGH),
        ("hardened", ScanStatus.SAFE, Severity.INFO),
    ],
)
def test_ot_audit_is_profile_dependent_and_restores_pump(
    profile: Profile,
    expected_status: ScanStatus,
    expected_severity: Severity,
) -> None:
    scanner, session = _scanner(OTAuditScanner, profile)

    result = scanner.scan()

    assert result.status is expected_status
    assert result.severity is expected_severity
    assert scanner.request_count == 6
    assert session.pumps["pump-001"] == "stopped"
    if profile == "hardened":
        assert result.evidence_json["event_validation"] == {
            "missing_fields": [],
            "incorrect_fields": [],
        }


def test_incomplete_ot_audit_event_is_medium_severity() -> None:
    scanner, session = _scanner(OTAuditScanner, "hardened")
    session.omit_audit_field = "actor"

    result = scanner.scan()

    assert result.status is ScanStatus.VULNERABLE
    assert result.severity is Severity.MEDIUM
    assert result.evidence_json["event_validation"]["missing_fields"] == ["actor"]
    assert session.pumps["pump-001"] == "stopped"


@pytest.mark.parametrize(
    ("profile", "expected_status", "request_count", "sleep_count"),
    [
        ("vulnerable", ScanStatus.VULNERABLE, 9, 7),
        ("hardened", ScanStatus.SAFE, 7, 5),
    ],
)
def test_ot_rate_limit_is_bounded_spaced_and_profile_dependent(
    monkeypatch: pytest.MonkeyPatch,
    profile: Profile,
    expected_status: ScanStatus,
    request_count: int,
    sleep_count: int,
) -> None:
    delays: list[float] = []
    monkeypatch.setattr("scanners.ot_rate_limit_scanner.time.sleep", delays.append)
    scanner, session = _scanner(OTRateLimitScanner, profile)

    result = scanner.scan()

    assert result.status is expected_status
    assert scanner.request_count == request_count
    assert result.evidence_json["attempt_count"] == request_count - 1
    assert delays == [0.5] * sleep_count
    assert session.pumps["pump-001"] == "stopped"
    assert session.calls.count(("POST", "/pumps/pump-001/stop")) <= 8
    if profile == "hardened":
        assert result.evidence_json["retry_after_present"] is True


@pytest.mark.parametrize(
    ("profile", "expected_count"),
    [("vulnerable", 43), ("hardened", 39)],
)
def test_all_seven_controls_share_one_budget_below_sixty(
    monkeypatch: pytest.MonkeyPatch,
    profile: Profile,
    expected_count: int,
) -> None:
    monkeypatch.setattr("scanners.ot_rate_limit_scanner.time.sleep", lambda _: None)
    target = TargetPolicy.resolve(TargetKey.OT_GATEWAY_DEMO)
    budget = RequestBudget(limit=60)
    session = FakeGatewaySession(profile)

    for scanner_type in (
        AuthScanner,
        IDORScanner,
        SQLiScanner,
        RateLimitScanner,
        OTCommandAuthorizationScanner,
        OTAuditScanner,
        OTRateLimitScanner,
    ):
        scanner = scanner_type(target=target, budget=budget)
        scanner.client.session = session
        scanner.scan()

    assert budget.count == expected_count
    assert budget.remaining == 60 - expected_count


def test_ot_authorization_network_failure_stops_checks_and_resets_station() -> None:
    scanner, session = _scanner(OTCommandAuthorizationScanner, "vulnerable")
    session.fail_once_at = 5

    with pytest.raises(requests.ConnectionError):
        scanner.scan()

    assert session.calls[-1] == ("POST", "/demo/reset")
    assert ("POST", "/process/emergency-stop") not in session.calls
    assert session.pumps == {"pump-001": "stopped", "pump-002": "running"}


def test_ot_audit_network_failure_stops_checks_and_restores_pump() -> None:
    scanner, session = _scanner(OTAuditScanner, "vulnerable")
    session.fail_once_at = 5

    with pytest.raises(requests.ConnectionError):
        scanner.scan()

    assert session.calls[-1] == ("POST", "/pumps/pump-001/stop")
    assert session.pumps["pump-001"] == "stopped"


def test_ot_rate_limit_network_failure_stops_the_request_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("scanners.ot_rate_limit_scanner.time.sleep", lambda _: None)
    scanner, session = _scanner(OTRateLimitScanner, "vulnerable")
    session.fail_once_at = 3

    with pytest.raises(requests.ConnectionError):
        scanner.scan()

    assert scanner.request_count == 3
    assert session.calls == [
        ("POST", "/auth/token"),
        ("POST", "/pumps/pump-001/stop"),
        ("POST", "/pumps/pump-001/stop"),
    ]
