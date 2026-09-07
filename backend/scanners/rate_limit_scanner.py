"""Bounded authentication rate-limit control for the local OT gateway."""

from __future__ import annotations

from typing import Any

from core.enums import ScanStatus, Severity, TestType
from schemas.test_result_schemas import TestResultCreate

from .base_scanner import BaseScanner
from .payloads import INVALID_LOGIN_PAYLOAD, MAX_INVALID_LOGIN_ATTEMPTS


class RateLimitScanner(BaseScanner):
    """Send at most eight invalid logins and stop on the first HTTP 429."""

    def scan(self) -> TestResultCreate:
        attempts: list[dict[str, Any]] = []
        limited_response = None
        credentials_accepted = False

        for attempt_number in range(1, MAX_INVALID_LOGIN_ATTEMPTS + 1):
            response = self.make_request(
                "POST",
                "/auth/token",
                json=INVALID_LOGIN_PAYLOAD,
            )
            attempts.append(
                {
                    "attempt": attempt_number,
                    "response": self.collect_evidence(
                        response,
                        payload=INVALID_LOGIN_PAYLOAD,
                    ),
                }
            )
            if response.status_code == 200:
                credentials_accepted = True
                break
            if response.status_code == 429:
                limited_response = response
                break

        evidence: dict[str, Any] = {
            "control": "gateway_login_rate_limit",
            "endpoint": "/auth/token",
            "attempts": attempts,
            "attempt_count": len(attempts),
            "maximum_attempts": MAX_INVALID_LOGIN_ATTEMPTS,
        }

        if credentials_accepted:
            return TestResultCreate(
                test_name=TestType.RATE_LIMIT,
                status=ScanStatus.VULNERABLE,
                severity=Severity.CRITICAL,
                details="The gateway accepted deliberately invalid credentials",
                evidence_json=evidence,
                recommendations_json=[
                    "Reject invalid credentials before issuing any gateway token"
                ],
            )

        if limited_response is not None:
            retry_after = limited_response.headers.get("Retry-After")
            evidence["limit_detected_at_attempt"] = len(attempts)
            evidence["retry_after_present"] = bool(retry_after)
            if retry_after:
                return TestResultCreate(
                    test_name=TestType.RATE_LIMIT,
                    status=ScanStatus.SAFE,
                    severity=Severity.INFO,
                    details="Invalid gateway logins are limited with Retry-After guidance",
                    evidence_json=evidence,
                    recommendations_json=[
                        "Keep authentication throttling and failed-login monitoring enabled"
                    ],
                )
            return TestResultCreate(
                test_name=TestType.RATE_LIMIT,
                status=ScanStatus.VULNERABLE,
                severity=Severity.MEDIUM,
                details="The gateway limits logins but omits the Retry-After header",
                evidence_json=evidence,
                recommendations_json=[
                    "Include Retry-After on every HTTP 429 authentication response"
                ],
            )

        if len(attempts) == MAX_INVALID_LOGIN_ATTEMPTS and all(
            attempt["response"]["status_code"] == 401 for attempt in attempts
        ):
            return TestResultCreate(
                test_name=TestType.RATE_LIMIT,
                status=ScanStatus.VULNERABLE,
                severity=Severity.MEDIUM,
                details="Eight invalid gateway logins were accepted without throttling",
                evidence_json=evidence,
                recommendations_json=[
                    "Rate-limit failed authentication attempts by a trusted client identity",
                    "Return HTTP 429 and Retry-After when the threshold is reached",
                ],
            )

        return TestResultCreate(
            test_name=TestType.RATE_LIMIT,
            status=ScanStatus.ERROR,
            severity=Severity.INFO,
            details="The gateway returned an unexpected login throttling response",
            evidence_json=evidence,
            recommendations_json=["Verify the gateway authentication rate-limit policy"],
        )
