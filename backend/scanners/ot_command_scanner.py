"""Authorization checks for sensitive commands on the simulated OT gateway."""

from __future__ import annotations

from typing import Any

from core.enums import ScanStatus, Severity, TestType
from schemas.test_result_schemas import TestResultCreate

from .base_scanner import BaseScanner
from .payloads import (
    ADMIN,
    GUEST,
    OPERATOR_A,
    OT_AUTHZ_EMERGENCY_ENDPOINT,
    OT_AUTHZ_PUMP_ENDPOINT,
)


class OTCommandAuthorizationScanner(BaseScanner):
    """Test low-privilege pump access and an unconfirmed emergency stop."""

    def scan(self) -> TestResultCreate:
        guest_token, guest_login = self.authenticate_gateway(
            GUEST.username,
            GUEST.password,
        )
        operator_token, operator_login = self.authenticate_gateway(
            OPERATOR_A.username,
            OPERATOR_A.password,
        )
        admin_token, admin_login = self.authenticate_gateway(
            ADMIN.username,
            ADMIN.password,
        )

        mutation_attempted = False
        try:
            mutation_attempted = True
            guest_start = self.make_request(
                "POST",
                OT_AUTHZ_PUMP_ENDPOINT,
                headers={"Authorization": f"Bearer {guest_token}"},
            )
            operator_start = self.make_request(
                "POST",
                OT_AUTHZ_PUMP_ENDPOINT,
                headers={"Authorization": f"Bearer {operator_token}"},
            )
            emergency_stop = self.make_request(
                "POST",
                OT_AUTHZ_EMERGENCY_ENDPOINT,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        except Exception:
            self._reset_after_failure(mutation_attempted)
            raise

        reset_evidence = self.reset_gateway()
        checks = {
            "guest_pump_start": self.collect_evidence(
                guest_start,
                actor=GUEST.username,
                expected="denied",
            ),
            "operator_pump_start": self.collect_evidence(
                operator_start,
                actor=OPERATOR_A.username,
                expected="denied",
            ),
            "unconfirmed_emergency_stop": self.collect_evidence(
                emergency_stop,
                actor=ADMIN.username,
                confirmation_header_sent=False,
                expected="denied",
            ),
        }
        evidence: dict[str, Any] = {
            "control": "ot_command_authorization",
            "authentication": {
                "guest": guest_login,
                "operator": operator_login,
                "admin": admin_login,
            },
            "checks": checks,
            "emergency_stop_confirmed": False,
            "station_reset": reset_evidence,
            "requests_used": 7,
        }

        emergency_accepted = 200 <= emergency_stop.status_code < 300
        pump_access_accepted = any(
            200 <= response.status_code < 300
            for response in (guest_start, operator_start)
        )
        if emergency_accepted:
            return TestResultCreate(
                test_name=TestType.OT_COMMAND_AUTHZ,
                status=ScanStatus.VULNERABLE,
                severity=Severity.CRITICAL,
                details="The gateway executed an emergency stop without explicit confirmation",
                evidence_json=evidence,
                recommendations_json=[
                    "Require the Admin role and an explicit confirmation header",
                    "Reject every unconfirmed emergency-stop request with HTTP 403",
                    "Audit all emergency control attempts",
                ],
            )

        if pump_access_accepted:
            return TestResultCreate(
                test_name=TestType.OT_COMMAND_AUTHZ,
                status=ScanStatus.VULNERABLE,
                severity=Severity.HIGH,
                details="A low-privilege identity can start a simulated industrial pump",
                evidence_json=evidence,
                recommendations_json=[
                    "Restrict pump commands to Supervisor and Admin roles",
                    "Apply authorization before changing process state",
                ],
            )

        if all(
            response.status_code in {401, 403}
            for response in (guest_start, operator_start, emergency_stop)
        ):
            return TestResultCreate(
                test_name=TestType.OT_COMMAND_AUTHZ,
                status=ScanStatus.SAFE,
                severity=Severity.INFO,
                details="Sensitive OT commands reject insufficient roles and missing confirmation",
                evidence_json=evidence,
                recommendations_json=[
                    "Keep role checks and explicit emergency confirmation enforced"
                ],
            )

        return TestResultCreate(
            test_name=TestType.OT_COMMAND_AUTHZ,
            status=ScanStatus.ERROR,
            severity=Severity.INFO,
            details="The gateway returned an unexpected OT authorization response",
            evidence_json=evidence,
            recommendations_json=["Verify the gateway command authorization matrix"],
        )

    def _reset_after_failure(self, attempted: bool) -> None:
        if not attempted:
            return
        try:
            self.reset_gateway()
        except Exception as cleanup_error:
            raise RuntimeError(
                "OT authorization failed and station reset could not be confirmed"
            ) from cleanup_error
