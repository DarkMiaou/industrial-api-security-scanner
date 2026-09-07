"""Deterministic BOLA control across the two OT gateway zones."""

from __future__ import annotations

from typing import Any

from core.enums import ScanStatus, Severity, TestType
from schemas.test_result_schemas import TestResultCreate

from .base_scanner import BaseScanner
from .payloads import GATEWAY_OPERATORS


class IDORScanner(BaseScanner):
    """Verify that zone A and B operators cannot read the other zone's pump."""

    def scan(self) -> TestResultCreate:
        checks: list[dict[str, Any]] = []
        own_access_failed = False
        cross_zone_accepted: list[dict[str, str]] = []

        for operator in GATEWAY_OPERATORS:
            token, login_evidence = self.authenticate_gateway(
                operator.username,
                operator.password,
            )
            headers = {"Authorization": f"Bearer {token}"}

            own_response = self.make_request(
                "GET",
                f"/pumps/{operator.own_pump}",
                headers=headers,
            )
            foreign_response = self.make_request(
                "GET",
                f"/pumps/{operator.foreign_pump}",
                headers=headers,
            )

            if own_response.status_code != 200:
                own_access_failed = True
            if foreign_response.status_code == 200:
                cross_zone_accepted.append(
                    {
                        "actor": operator.username,
                        "actor_zone": operator.zone,
                        "foreign_pump": operator.foreign_pump,
                    }
                )

            checks.append(
                {
                    "actor": operator.username,
                    "actor_zone": operator.zone,
                    "authentication": login_evidence,
                    "own_pump": self.collect_evidence(
                        own_response,
                        actor=operator.username,
                        pump_id=operator.own_pump,
                        expected="allowed",
                    ),
                    "foreign_pump": self.collect_evidence(
                        foreign_response,
                        actor=operator.username,
                        pump_id=operator.foreign_pump,
                        expected="denied",
                    ),
                }
            )

        evidence: dict[str, Any] = {
            "control": "ot_cross_zone_bola",
            "zones_tested": ["A", "B"],
            "checks": checks,
            "requests_used": 6,
        }

        if own_access_failed:
            return TestResultCreate(
                test_name=TestType.IDOR,
                status=ScanStatus.ERROR,
                severity=Severity.INFO,
                details="The BOLA prerequisites could not be confirmed",
                evidence_json=evidence,
                recommendations_json=[
                    "Verify both demo operators and their own-zone pump access"
                ],
            )

        if cross_zone_accepted:
            evidence["unauthorized_cross_zone_access"] = cross_zone_accepted
            return TestResultCreate(
                test_name=TestType.IDOR,
                status=ScanStatus.VULNERABLE,
                severity=Severity.HIGH,
                details="Operators can read pump objects belonging to another OT zone",
                evidence_json=evidence,
                recommendations_json=[
                    "Enforce object-level authorization on every pump lookup",
                    "Compare the authenticated operator zone with the pump zone",
                    "Return HTTP 403 for cross-zone object access",
                ],
            )

        foreign_statuses = [
            check["foreign_pump"]["status_code"] for check in checks
        ]
        if all(status_code == 403 for status_code in foreign_statuses):
            return TestResultCreate(
                test_name=TestType.IDOR,
                status=ScanStatus.SAFE,
                severity=Severity.INFO,
                details="Pump object access is correctly isolated between OT zones",
                evidence_json=evidence,
                recommendations_json=[
                    "Keep zone-aware object authorization on all industrial resources"
                ],
            )

        return TestResultCreate(
            test_name=TestType.IDOR,
            status=ScanStatus.ERROR,
            severity=Severity.INFO,
            details="The gateway returned an unexpected cross-zone access response",
            evidence_json=evidence,
            recommendations_json=["Verify the gateway BOLA policy and demo fixtures"],
        )
