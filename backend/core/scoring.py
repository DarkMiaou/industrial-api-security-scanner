"""Pedagogical IASS-OT security score calculation."""

from __future__ import annotations

from collections.abc import Iterable

from core.enums import ScanStatus, Severity
from schemas.test_result_schemas import TestResultCreate

SEVERITY_PENALTIES = {
    Severity.CRITICAL: 30,
    Severity.HIGH: 15,
    Severity.MEDIUM: 7,
    Severity.LOW: 2,
    Severity.INFO: 0,
}


def calculate_security_score(results: Iterable[TestResultCreate]) -> int:
    """Return a 0-100 score; safe and error results never reduce it."""
    penalty = sum(
        SEVERITY_PENALTIES[result.severity]
        for result in results
        if result.status is ScanStatus.VULNERABLE
    )
    return max(0, 100 - penalty)
