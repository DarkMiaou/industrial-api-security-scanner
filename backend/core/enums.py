"""
Enum definitions for the application for type safety
"""

from enum import StrEnum


class ScanStatus(StrEnum):
    """
    Enum for scan result status
    """

    VULNERABLE = "vulnerable"
    SAFE = "safe"
    ERROR = "error"


class Severity(StrEnum):
    """
    Enum for vulnerability severity levels
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TestType(StrEnum):
    """
    Enum for available security test types
    """

    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    SQLI = "sqli"
    IDOR = "idor"
    OT_COMMAND_AUTHZ = "ot_command_authz"
    OT_AUDIT = "ot_audit"
    OT_RATE_LIMIT = "ot_rate_limit"


class GatewayProfile(StrEnum):
    """Runtime security profile reported by the local gateway."""

    VULNERABLE = "vulnerable"
    HARDENED = "hardened"


class ScanExecutionStatus(StrEnum):
    """Lifecycle state of one complete scan execution."""

    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
