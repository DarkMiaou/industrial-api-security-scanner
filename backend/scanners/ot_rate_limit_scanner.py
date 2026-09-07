"""Rate-limit validation for idempotent simulated OT commands."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from core.enums import ScanStatus, Severity, TestType
from schemas.test_result_schemas import TestResultCreate

from .base_scanner import BaseScanner
from .payloads import (
    ADMIN,
    OT_RATE_LIMIT_ENDPOINT,
    OT_RATE_LIMIT_MAX_ATTEMPTS,
    OT_RATE_LIMIT_SPACING_SECONDS,
)


class OTRateLimitScanner(BaseScanner):
    """Send at most eight idempotent pump stops, spaced by half a second."""

    def scan(self) -> TestResultCreate:
        token, login_evidence = self.authenticate_gateway(
            ADMIN.username,
            ADMIN.password,
        )
        attempts: list[dict[str, Any]] = []
        limited_response = None

        for attempt_number in range(1, OT_RATE_LIMIT_MAX_ATTEMPTS + 1):
            response = self.make_request(
                "POST",
                OT_RATE_LIMIT_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Correlation-ID": f"iass-rate-{uuid4()}",
                },
            )
            attempts.append(
                {
                    "attempt": attempt_number,
                    "response": self.collect_evidence(response),
                }
            )
            if response.status_code == 429:
                limited_response = response
                break
            if response.status_code != 200:
                break
            if attempt_number < OT_RATE_LIMIT_MAX_ATTEMPTS:
                time.sleep(OT_RATE_LIMIT_SPACING_SECONDS)

        evidence: dict[str, Any] = {
            "control": "ot_command_rate_limit",
            "endpoint": OT_RATE_LIMIT_ENDPOINT,
            "method": "POST",
            "idempotent_command": True,
            "spacing_seconds": OT_RATE_LIMIT_SPACING_SECONDS,
            "authentication": login_evidence,
            "attempts": attempts,
            "attempt_count": len(attempts),
            "maximum_attempts": OT_RATE_LIMIT_MAX_ATTEMPTS,
        }

        if limited_response is not None:
            retry_after = limited_response.headers.get("Retry-After")
            evidence["limit_detected_at_attempt"] = len(attempts)
            evidence["retry_after_present"] = bool(retry_after)
            if retry_after:
                return TestResultCreate(
                    test_name=TestType.OT_RATE_LIMIT,
                    status=ScanStatus.SAFE,
                    severity=Severity.INFO,
                    details="OT commands are throttled with Retry-After guidance",
                    evidence_json=evidence,
                    recommendations_json=["Keep actor-based OT command throttling enabled"],
                )
            return TestResultCreate(
                test_name=TestType.OT_RATE_LIMIT,
                status=ScanStatus.VULNERABLE,
                severity=Severity.LOW,
                details="OT commands are throttled but Retry-After is missing",
                evidence_json=evidence,
                recommendations_json=["Include Retry-After on OT command HTTP 429 responses"],
            )

        if len(attempts) == OT_RATE_LIMIT_MAX_ATTEMPTS and all(
            attempt["response"]["status_code"] == 200 for attempt in attempts
        ):
            return TestResultCreate(
                test_name=TestType.OT_RATE_LIMIT,
                status=ScanStatus.VULNERABLE,
                severity=Severity.HIGH,
                details="Eight OT commands were accepted without throttling",
                evidence_json=evidence,
                recommendations_json=[
                    "Limit repeated process commands by authenticated actor",
                    "Return HTTP 429 with Retry-After before the eighth attempt",
                ],
            )

        return TestResultCreate(
            test_name=TestType.OT_RATE_LIMIT,
            status=ScanStatus.ERROR,
            severity=Severity.INFO,
            details="The gateway returned an unexpected OT command response",
            evidence_json=evidence,
            recommendations_json=["Verify the OT command rate-limit policy"],
        )
