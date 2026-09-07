"""Deterministic authentication control for the local OT gateway."""

from __future__ import annotations

from core.enums import ScanStatus, Severity, TestType
from schemas.test_result_schemas import TestResultCreate

from .base_scanner import BaseScanner
from .payloads import AUTH_PROTECTED_ENDPOINT, INVALID_BEARER_TOKEN


class AuthScanner(BaseScanner):
    """Verify that OT telemetry rejects missing and invalid authentication."""

    def scan(self) -> TestResultCreate:
        missing = self.make_request("GET", AUTH_PROTECTED_ENDPOINT)
        invalid = self.make_request(
            "GET",
            AUTH_PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {INVALID_BEARER_TOKEN}"},
        )
        evidence = {
            "control": "ot_telemetry_authentication",
            "endpoint": AUTH_PROTECTED_ENDPOINT,
            "missing_authentication": self.collect_evidence(missing),
            "invalid_token": self.collect_evidence(invalid),
            "requests_used": 2,
        }

        accepted = [
            name
            for name, response in (
                ("missing_authentication", missing),
                ("invalid_token", invalid),
            )
            if response.status_code == 200
        ]
        if accepted:
            evidence["accepted_without_valid_identity"] = accepted
            return TestResultCreate(
                test_name=TestType.AUTH,
                status=ScanStatus.VULNERABLE,
                severity=Severity.HIGH,
                details="OT telemetry is accessible without a valid gateway identity",
                evidence_json=evidence,
                recommendations_json=[
                    "Require a valid gateway token before returning OT telemetry",
                    "Reject missing and malformed Bearer tokens with HTTP 401",
                    "Log failed authentication attempts without storing credentials",
                ],
            )

        if all(response.status_code in {401, 403} for response in (missing, invalid)):
            return TestResultCreate(
                test_name=TestType.AUTH,
                status=ScanStatus.SAFE,
                severity=Severity.INFO,
                details="OT telemetry rejects missing and invalid authentication",
                evidence_json=evidence,
                recommendations_json=[
                    "Keep gateway token validation and authentication monitoring enabled"
                ],
            )

        return TestResultCreate(
            test_name=TestType.AUTH,
            status=ScanStatus.ERROR,
            severity=Severity.INFO,
            details="The gateway returned an unexpected authentication response",
            evidence_json=evidence,
            recommendations_json=[
                "Verify the OT telemetry route and gateway authentication policy"
            ],
        )
