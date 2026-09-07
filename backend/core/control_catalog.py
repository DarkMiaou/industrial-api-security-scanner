"""Stable display metadata for the seven IASS-OT controls."""

from __future__ import annotations

from dataclasses import dataclass

from core.enums import TestType


@dataclass(frozen=True, slots=True)
class ControlMetadata:
    title: str
    method: str
    endpoint: str
    ot_impact: str


CONTROL_METADATA: dict[TestType, ControlMetadata] = {
    TestType.AUTH: ControlMetadata(
        title="OT telemetry authentication",
        method="GET",
        endpoint="/telemetry",
        ot_impact="Unauthorized disclosure of industrial process telemetry.",
    ),
    TestType.IDOR: ControlMetadata(
        title="Cross-zone pump object authorization",
        method="GET",
        endpoint="/pumps/{pump_id}",
        ot_impact="An operator may observe equipment outside the assigned OT zone.",
    ),
    TestType.SQLI: ControlMetadata(
        title="Maintenance order input validation",
        method="GET",
        endpoint="/maintenance/orders",
        ot_impact="Maintenance information may be exposed or the service destabilized.",
    ),
    TestType.RATE_LIMIT: ControlMetadata(
        title="Gateway authentication throttling",
        method="POST",
        endpoint="/auth/token",
        ot_impact="Unlimited login attempts increase credential attack and service load risk.",
    ),
    TestType.OT_COMMAND_AUTHZ: ControlMetadata(
        title="Sensitive OT command authorization",
        method="POST",
        endpoint="/pumps/pump-001/start",
        ot_impact="An unauthorized identity may alter the simulated industrial process.",
    ),
    TestType.OT_AUDIT: ControlMetadata(
        title="Correlated OT command audit trail",
        method="POST",
        endpoint="/pumps/pump-001/start",
        ot_impact="Untraceable process changes obstruct incident investigation.",
    ),
    TestType.OT_RATE_LIMIT: ControlMetadata(
        title="OT command throttling",
        method="POST",
        endpoint="/pumps/pump-001/stop",
        ot_impact="Repeated commands may overload or destabilize industrial operations.",
    ),
}
