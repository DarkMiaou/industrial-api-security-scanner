"""
ⒸAngelaMos | 2025
Scan model API validation and serialization
"""

from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from datetime import datetime
from typing import Literal

from core.enums import GatewayProfile, ScanExecutionStatus, TestType
from core.target_policy import TargetKey
from .test_result_schemas import TestResultResponse


class ScanRequest(BaseModel):
    """
    Schema for creating a new security scan
    """

    model_config = ConfigDict(extra="forbid")

    target: TargetKey
    tests_to_run: list[TestType] = Field(min_length = 1)
    authorization_confirmed: Literal[True]


class ScanResponse(BaseModel):
    """
    Schema for scan data in API responses
    """

    model_config = ConfigDict(from_attributes = True)

    id: int
    user_id: int
    target_url: str
    target_key: TargetKey
    target_name: str
    profile: GatewayProfile
    status: ScanExecutionStatus
    authorization_confirmed: bool
    score: int | None
    request_count: int
    duration_ms: int | None
    scan_date: datetime
    completed_at: datetime | None
    created_at: datetime
    test_results: list[TestResultResponse] = Field(default_factory=list)

    @property
    def total_tests(self) -> int:
        """
        Total number of tests run
        """
        return len(self.test_results)

    @property
    def vulnerabilities_found(self) -> int:
        """
        Number of vulnerabilities found
        """
        return sum(
            1 for r in self.test_results if r.status == "vulnerable"
        )
