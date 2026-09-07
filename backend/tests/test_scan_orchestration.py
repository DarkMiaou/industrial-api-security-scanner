from __future__ import annotations

import inspect
import json
from typing import Any

import pytest
import requests
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import models  # noqa: F401 - registers every mapped table on Base metadata
from config import settings
from core.database import Base
from core.enums import (
    GatewayProfile,
    ScanExecutionStatus,
    ScanStatus,
    Severity,
    TestType as ControlType,
)
from core.request_budget import RequestBudget
from core.scoring import calculate_security_score
from models.Scan import Scan
from models.TestResult import TestResult as ResultRecord
from models.User import User
from repositories.scan_repository import ScanRepository
from routes.scans import create_scan
from schemas.scan_schemas import ScanRequest
from schemas.test_result_schemas import TestResultCreate as ResultCreate
from services.scan_service import CONTROL_ORDER, SCANNER_MAPPING, ScanService


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _response(status_code: int, body: dict[str, Any]) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.headers["Content-Type"] = "application/json"
    response._content = json.dumps(body).encode()
    response._content_consumed = True
    return response


class FakePreflightClient:
    def __init__(
        self,
        budget: RequestBudget,
        *,
        profile: str = "vulnerable",
        reset_status: int = 200,
    ) -> None:
        self.budget = budget
        self.profile = profile
        self.reset_status = reset_status
        self.calls: list[tuple[str, str]] = []

    def request(self, method: str, endpoint: str, **_kwargs: Any) -> requests.Response:
        self.budget.reserve()
        self.calls.append((method, endpoint))
        if endpoint == "/health":
            return _response(200, {"status": "healthy", "profile": self.profile})
        if endpoint == "/demo/reset":
            return _response(self.reset_status, {"status": "reset"})
        raise AssertionError(f"Unexpected preflight request: {method} {endpoint}")


def _user(db: Session, email: str) -> User:
    user = User(email=email, hashed_password="test-hash", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _request(*tests: ControlType) -> ScanRequest:
    return ScanRequest(
        target="ot-gateway-demo",
        tests_to_run=list(tests),
        authorization_confirmed=True,
    )


def _scanner_class(
    test_type: ControlType,
    *,
    result_status: ScanStatus,
    severity: Severity,
    call_order: list[ControlType],
    persisted_counts: list[int],
    db: Session,
    fail: bool = False,
) -> type:
    class FakeScanner:
        def __init__(self, target: Any, budget: RequestBudget) -> None:
            self.target = target
            self.budget = budget

        def scan(self) -> ResultCreate:
            call_order.append(test_type)
            persisted_counts.append(db.query(ResultRecord).count())
            self.budget.reserve()
            if fail:
                raise requests.ConnectionError("simulated scanner failure")
            return ResultCreate(
                test_name=test_type,
                status=result_status,
                severity=severity,
                details=f"Result for {test_type.value}",
            )

    return FakeScanner


def _install_preflight(
    monkeypatch: pytest.MonkeyPatch,
    *,
    profile: str = "vulnerable",
    reset_status: int = 200,
) -> list[FakePreflightClient]:
    clients: list[FakePreflightClient] = []

    def factory(_target: Any, budget: RequestBudget) -> FakePreflightClient:
        client = FakePreflightClient(
            budget,
            profile=profile,
            reset_status=reset_status,
        )
        clients.append(client)
        return client

    monkeypatch.setattr(ScanService, "_gateway_client", staticmethod(factory))
    return clients


def test_orchestration_uses_fixed_order_persists_progress_and_metrics(
    monkeypatch: pytest.MonkeyPatch,
    db: Session,
) -> None:
    user = _user(db, "orchestration@example.test")
    clients = _install_preflight(monkeypatch, profile="hardened")
    call_order: list[ControlType] = []
    persisted_counts: list[int] = []
    selected = (ControlType.OT_AUDIT, ControlType.AUTH, ControlType.SQLI)
    for test_type in selected:
        monkeypatch.setitem(
            SCANNER_MAPPING,
            test_type,
            _scanner_class(
                test_type,
                result_status=ScanStatus.SAFE,
                severity=Severity.INFO,
                call_order=call_order,
                persisted_counts=persisted_counts,
                db=db,
            ),
        )

    response = ScanService.run_scan(db, user.id, _request(*selected))

    assert call_order == [ControlType.AUTH, ControlType.SQLI, ControlType.OT_AUDIT]
    assert persisted_counts == [0, 1, 2]
    assert response.profile is GatewayProfile.HARDENED
    assert response.status is ScanExecutionStatus.COMPLETED
    assert response.score == 100
    assert response.request_count == 5
    assert response.duration_ms is not None and response.duration_ms >= 0
    assert response.completed_at is not None
    assert response.authorization_confirmed is True
    assert response.target_key == "ot-gateway-demo"
    assert response.target_name == "Water Pump Gateway"
    assert [result.test_name for result in response.test_results] == call_order
    assert all(result.title and result.method and result.endpoint for result in response.test_results)
    assert all(result.ot_impact for result in response.test_results)
    assert clients[0].calls == [("GET", "/health"), ("POST", "/demo/reset")]


def test_partial_scan_keeps_results_and_errors_do_not_reduce_score(
    monkeypatch: pytest.MonkeyPatch,
    db: Session,
) -> None:
    user = _user(db, "partial@example.test")
    _install_preflight(monkeypatch)
    call_order: list[ControlType] = []
    persisted_counts: list[int] = []
    definitions = {
        ControlType.AUTH: (ScanStatus.SAFE, Severity.INFO, False),
        ControlType.IDOR: (ScanStatus.ERROR, Severity.INFO, True),
        ControlType.SQLI: (ScanStatus.VULNERABLE, Severity.CRITICAL, False),
    }
    for test_type, (result_status, severity, fail) in definitions.items():
        monkeypatch.setitem(
            SCANNER_MAPPING,
            test_type,
            _scanner_class(
                test_type,
                result_status=result_status,
                severity=severity,
                call_order=call_order,
                persisted_counts=persisted_counts,
                db=db,
                fail=fail,
            ),
        )

    response = ScanService.run_scan(db, user.id, _request(*definitions))

    assert response.status is ScanExecutionStatus.PARTIAL
    assert response.score == 70
    assert response.request_count == 5
    assert [result.status for result in response.test_results] == [
        ScanStatus.SAFE,
        ScanStatus.ERROR,
        ScanStatus.VULNERABLE,
    ]
    assert db.query(ResultRecord).count() == 3


def test_failed_reset_finalizes_scan_without_running_a_control(
    monkeypatch: pytest.MonkeyPatch,
    db: Session,
) -> None:
    user = _user(db, "reset-failure@example.test")
    _install_preflight(monkeypatch, reset_status=500)

    response = ScanService.run_scan(db, user.id, _request(ControlType.AUTH))

    assert response.status is ScanExecutionStatus.FAILED
    assert response.score is None
    assert response.request_count == 2
    assert response.completed_at is not None
    assert response.test_results == []


def test_score_formula_and_floor() -> None:
    def make_result(status: ScanStatus, severity: Severity) -> ResultCreate:
        return ResultCreate(
            test_name=ControlType.AUTH,
            status=status,
            severity=severity,
            details="score fixture",
        )

    results = [
        make_result(ScanStatus.VULNERABLE, Severity.CRITICAL),
        make_result(ScanStatus.VULNERABLE, Severity.HIGH),
        make_result(ScanStatus.VULNERABLE, Severity.MEDIUM),
        make_result(ScanStatus.VULNERABLE, Severity.LOW),
        make_result(ScanStatus.ERROR, Severity.CRITICAL),
        make_result(ScanStatus.SAFE, Severity.CRITICAL),
    ]
    assert calculate_security_score(results) == 46
    assert calculate_security_score(results * 3) == 0


def test_scan_ownership_is_always_forbidden_to_another_user(db: Session) -> None:
    owner = _user(db, "owner@example.test")
    other = _user(db, "other@example.test")
    scan = ScanRepository.create_scan(
        db,
        owner.id,
        "http://ot-gateway-demo:8081",
        "ot-gateway-demo",
        "Water Pump Gateway",
        GatewayProfile.VULNERABLE,
        True,
    )

    with pytest.raises(HTTPException) as read_error:
        ScanService.get_scan_by_id(db, scan.id, other.id)
    with pytest.raises(HTTPException) as delete_error:
        ScanService.delete_scan(db, scan.id, other.id)

    assert read_error.value.status_code == 403
    assert delete_error.value.status_code == 403
    assert db.get(Scan, scan.id) is not None


def test_default_scan_history_page_contains_twenty_newest_records(db: Session) -> None:
    user = _user(db, "pagination@example.test")
    for _ in range(25):
        ScanRepository.create_scan(
            db,
            user.id,
            "http://ot-gateway-demo:8081",
            "ot-gateway-demo",
            "Water Pump Gateway",
            GatewayProfile.VULNERABLE,
            True,
        )

    scans = ScanRepository.get_by_user(db, user.id)

    assert settings.DEFAULT_PAGINATION_LIMIT == 20
    assert len(scans) == 20
    assert [scan.id for scan in scans] == list(range(25, 5, -1))


def test_create_route_dispatches_scan_work_to_threadpool() -> None:
    source = inspect.getsource(create_scan)
    assert "await run_in_threadpool" in source
    assert "ScanService.run_scan_in_new_session" in source


def test_control_order_contains_the_seven_unique_controls() -> None:
    assert CONTROL_ORDER == (
        ControlType.AUTH,
        ControlType.IDOR,
        ControlType.SQLI,
        ControlType.RATE_LIMIT,
        ControlType.OT_COMMAND_AUTHZ,
        ControlType.OT_AUDIT,
        ControlType.OT_RATE_LIMIT,
    )
    assert len(set(CONTROL_ORDER)) == 7
