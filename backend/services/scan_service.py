"""Orchestrate the seven bounded IASS-OT controls and persist their results."""

from __future__ import annotations

from time import monotonic

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from config import settings
from core.database import SessionLocal
from core.enums import GatewayProfile, ScanExecutionStatus, ScanStatus, TestType
from core.redaction import redact, redact_text
from core.request_budget import RequestBudget
from core.safe_http import SafeScannerClient
from core.scoring import calculate_security_score
from core.target_policy import ResolvedTarget, TargetPolicy, TargetPolicyError
from repositories.scan_repository import ScanRepository
from repositories.test_result_repository import TestResultRepository
from scanners.auth_scanner import AuthScanner
from scanners.base_scanner import BaseScanner
from scanners.idor_scanner import IDORScanner
from scanners.ot_audit_scanner import OTAuditScanner
from scanners.ot_command_scanner import OTCommandAuthorizationScanner
from scanners.ot_rate_limit_scanner import OTRateLimitScanner
from scanners.rate_limit_scanner import RateLimitScanner
from scanners.sqli_scanner import SQLiScanner
from schemas.scan_schemas import ScanRequest, ScanResponse
from schemas.test_result_schemas import TestResultCreate

CONTROL_ORDER = (
    TestType.AUTH,
    TestType.IDOR,
    TestType.SQLI,
    TestType.RATE_LIMIT,
    TestType.OT_COMMAND_AUTHZ,
    TestType.OT_AUDIT,
    TestType.OT_RATE_LIMIT,
)

SCANNER_MAPPING: dict[TestType, type[BaseScanner]] = {
    TestType.AUTH: AuthScanner,
    TestType.IDOR: IDORScanner,
    TestType.SQLI: SQLiScanner,
    TestType.RATE_LIMIT: RateLimitScanner,
    TestType.OT_COMMAND_AUTHZ: OTCommandAuthorizationScanner,
    TestType.OT_AUDIT: OTAuditScanner,
    TestType.OT_RATE_LIMIT: OTRateLimitScanner,
}


class ScanService:
    """Coordinate target preflight, controls, persistence and final metrics."""

    @staticmethod
    def run_scan_in_new_session(
        user_id: int,
        scan_request: ScanRequest,
    ) -> ScanResponse:
        """Open the database session inside the worker thread used by the route."""
        with SessionLocal() as db:
            return ScanService.run_scan(db, user_id, scan_request)

    @staticmethod
    def run_scan(db: Session, user_id: int, scan_request: ScanRequest) -> ScanResponse:
        started_at = monotonic()
        try:
            target = TargetPolicy.resolve(
                scan_request.target,
                configured_url=settings.OT_GATEWAY_URL,
            )
        except TargetPolicyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The local OT target policy is not available",
            ) from exc

        budget = RequestBudget(settings.SCANNER_REQUEST_BUDGET)
        gateway_client = ScanService._gateway_client(target, budget)
        try:
            profile = ScanService._read_gateway_profile(gateway_client)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The local OT gateway is unavailable or returned an invalid profile",
            ) from exc

        scan = ScanRepository.create_scan(
            db=db,
            user_id=user_id,
            target_url=target.base_url,
            target_key=target.key.value,
            target_name=target.display_name,
            profile=profile,
            authorization_confirmed=scan_request.authorization_confirmed,
        )

        try:
            ScanService._reset_gateway(gateway_client)
        except Exception:
            ScanRepository.finalize_scan(
                db,
                scan,
                status=ScanExecutionStatus.FAILED,
                score=None,
                request_count=budget.count,
                duration_ms=ScanService._duration_ms(started_at),
            )
            return ScanService._response(db, scan.id)

        results: list[TestResultCreate] = []
        selected_tests = set(scan_request.tests_to_run)
        for test_type in CONTROL_ORDER:
            if test_type not in selected_tests:
                continue
            scanner_class = SCANNER_MAPPING[test_type]
            try:
                result = scanner_class(target=target, budget=budget).scan()
            except Exception as exc:
                result = TestResultCreate(
                    test_name=test_type,
                    status=ScanStatus.ERROR,
                    severity="info",
                    details=redact_text(f"Scanner error: {exc}"),
                    evidence_json=redact(
                        {
                            "error": str(exc),
                            "request_count_at_failure": budget.count,
                        }
                    ),
                    recommendations_json=[
                        "Check that the local OT gateway is healthy",
                        "Review the safety limit that stopped this control",
                    ],
                )

            results.append(result)
            ScanService._persist_result(db, scan.id, result)

        execution_status = ScanService._execution_status(results)
        useful_results = [
            result for result in results if result.status is not ScanStatus.ERROR
        ]
        score = calculate_security_score(results) if useful_results else None
        ScanRepository.finalize_scan(
            db,
            scan,
            status=execution_status,
            score=score,
            request_count=budget.count,
            duration_ms=ScanService._duration_ms(started_at),
        )
        return ScanService._response(db, scan.id)

    @staticmethod
    def get_scan_by_id(db: Session, scan_id: int, user_id: int) -> ScanResponse:
        scan = ScanRepository.get_by_id(db, scan_id)
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found",
            )
        if scan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this scan",
            )
        return ScanResponse.model_validate(scan)

    @staticmethod
    def get_user_scans(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int | None = None,
    ) -> list[ScanResponse]:
        scans = ScanRepository.get_by_user(db=db, user_id=user_id, skip=skip, limit=limit)
        return [ScanResponse.model_validate(scan) for scan in scans]

    @staticmethod
    def delete_scan(db: Session, scan_id: int, user_id: int) -> bool:
        scan = ScanRepository.get_by_id(db, scan_id)
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found",
            )
        if scan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this scan",
            )
        return ScanRepository.delete(db, scan_id)

    @staticmethod
    def _gateway_client(
        target: ResolvedTarget,
        budget: RequestBudget,
    ) -> SafeScannerClient:
        return SafeScannerClient(
            target=target,
            budget=budget,
            connect_timeout=settings.SCANNER_CONNECTION_TIMEOUT,
            read_timeout=settings.SCANNER_READ_TIMEOUT,
            max_response_bytes=settings.SCANNER_MAX_RESPONSE_BYTES,
            user_agent=f"{settings.APP_NAME}/{settings.VERSION}",
        )

    @staticmethod
    def _read_gateway_profile(client: SafeScannerClient) -> GatewayProfile:
        response = client.request("GET", "/health")
        if response.status_code != 200:
            raise RuntimeError(f"Gateway health check failed: HTTP {response.status_code}")
        try:
            return GatewayProfile(response.json()["profile"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("Gateway returned an unsupported profile") from exc

    @staticmethod
    def _reset_gateway(client: SafeScannerClient) -> None:
        response = client.request(
            "POST",
            "/demo/reset",
            headers={"X-Demo-Key": settings.OT_DEMO_RESET_KEY},
        )
        if response.status_code != 200:
            raise RuntimeError(f"Gateway reset failed: HTTP {response.status_code}")

    @staticmethod
    def _persist_result(db: Session, scan_id: int, result: TestResultCreate) -> None:
        TestResultRepository.create_test_result(
            db=db,
            scan_id=scan_id,
            test_name=result.test_name,
            status=result.status,
            severity=result.severity,
            title=result.title,
            method=result.method,
            endpoint=result.endpoint,
            details=result.details,
            ot_impact=result.ot_impact,
            evidence_json=redact(result.evidence_json),
            recommendations_json=result.recommendations_json,
        )

    @staticmethod
    def _execution_status(results: list[TestResultCreate]) -> ScanExecutionStatus:
        error_count = sum(result.status is ScanStatus.ERROR for result in results)
        if error_count == 0 and results:
            return ScanExecutionStatus.COMPLETED
        if error_count < len(results):
            return ScanExecutionStatus.PARTIAL
        return ScanExecutionStatus.FAILED

    @staticmethod
    def _duration_ms(started_at: float) -> int:
        return max(0, round((monotonic() - started_at) * 1000))

    @staticmethod
    def _response(db: Session, scan_id: int) -> ScanResponse:
        scan = ScanRepository.get_by_id(db, scan_id)
        if scan is None:
            raise RuntimeError("Persisted scan could not be reloaded")
        return ScanResponse.model_validate(scan)
