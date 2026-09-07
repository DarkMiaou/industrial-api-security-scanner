"""Bounded, non-destructive SQL injection control for maintenance orders."""

from __future__ import annotations

from typing import Any

import requests

from core.enums import ScanStatus, Severity, TestType
from schemas.test_result_schemas import TestResultCreate

from .base_scanner import BaseScanner
from .payloads import OPERATOR_A, SQLI_ENDPOINT, SQLI_PROBES


def _order_count(response: requests.Response) -> int | None:
    try:
        orders = response.json().get("orders")
    except (ValueError, AttributeError):
        return None
    return len(orders) if isinstance(orders, list) else None


class SQLiScanner(BaseScanner):
    """Compare four harmless inputs; never use destructive or time-based payloads."""

    def scan(self) -> TestResultCreate:
        token, login_evidence = self.authenticate_gateway(
            OPERATOR_A.username,
            OPERATOR_A.password,
        )
        headers = {"Authorization": f"Bearer {token}"}
        responses: dict[str, requests.Response] = {}
        probes: list[dict[str, Any]] = []

        for name, value in SQLI_PROBES:
            response = self.make_request(
                "GET",
                SQLI_ENDPOINT,
                params={"id": value},
                headers=headers,
            )
            responses[name] = response
            probes.append(
                {
                    "name": name,
                    "value": value,
                    "order_count": _order_count(response),
                    "response": self.collect_evidence(response, payload={"id": value}),
                }
            )

        evidence: dict[str, Any] = {
            "control": "maintenance_order_sqli",
            "endpoint": SQLI_ENDPOINT,
            "authentication": login_evidence,
            "probes": probes,
            "payload_count": len(SQLI_PROBES),
            "contains_destructive_payload": False,
            "contains_time_based_payload": False,
            "requests_used": 5,
        }

        baseline_count = _order_count(responses["baseline"])
        true_count = _order_count(responses["boolean_true"])
        false_count = _order_count(responses["boolean_false"])
        boolean_difference = (
            responses["baseline"].status_code == 200
            and responses["boolean_true"].status_code == 200
            and responses["boolean_false"].status_code == 200
            and baseline_count is not None
            and true_count is not None
            and false_count is not None
            and true_count > baseline_count
            and false_count < true_count
        )
        error_disclosure = responses["error_probe"].status_code >= 500
        evidence["signals"] = {
            "boolean_response_difference": boolean_difference,
            "database_error_response": error_disclosure,
        }

        if boolean_difference or error_disclosure:
            return TestResultCreate(
                test_name=TestType.SQLI,
                status=ScanStatus.VULNERABLE,
                severity=Severity.CRITICAL,
                details="The maintenance order filter exhibits deterministic SQL injection signals",
                evidence_json=evidence,
                recommendations_json=[
                    "Validate the order identifier as an integer before data access",
                    "Use parameterized database queries exclusively",
                    "Return a generic client error instead of database error details",
                ],
            )

        malformed_responses = (
            responses["boolean_true"],
            responses["boolean_false"],
            responses["error_probe"],
        )
        if responses["baseline"].status_code == 200 and all(
            response.status_code in {400, 422} for response in malformed_responses
        ):
            return TestResultCreate(
                test_name=TestType.SQLI,
                status=ScanStatus.SAFE,
                severity=Severity.INFO,
                details="The maintenance order filter rejects all non-integer probes",
                evidence_json=evidence,
                recommendations_json=[
                    "Keep strict input validation and parameterized queries in place"
                ],
            )

        return TestResultCreate(
            test_name=TestType.SQLI,
            status=ScanStatus.ERROR,
            severity=Severity.INFO,
            details="The gateway returned an unexpected maintenance filter response",
            evidence_json=evidence,
            recommendations_json=["Verify the maintenance order demo scenario"],
        )
