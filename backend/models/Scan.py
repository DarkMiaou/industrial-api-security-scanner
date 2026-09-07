"""
ⒸAngelaMos | 2025
Scan model for storing security scan metadata
"""

from datetime import (
    UTC,
    datetime,
)
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from config import settings
from core.enums import GatewayProfile, ScanExecutionStatus
from .Base import BaseModel


class Scan(BaseModel):
    """
    Stores metadata about scans performed on target URLs
    """

    __tablename__ = "scans"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_scans_score_range"),
        CheckConstraint("request_count >= 0", name="ck_scans_request_count"),
        CheckConstraint("duration_ms >= 0", name="ck_scans_duration_ms"),
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id",
                   ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    target_url = Column(
        String(settings.URL_MAX_LENGTH),
        nullable = False,
    )
    target_key = Column(
        String(64),
        nullable=False,
        default="ot-gateway-demo",
        server_default="ot-gateway-demo",
    )
    target_name = Column(
        String(255),
        nullable=False,
        default="Water Pump Gateway",
        server_default="Water Pump Gateway",
    )
    profile = Column(
        Enum(GatewayProfile),
        nullable=False,
    )
    status = Column(
        Enum(ScanExecutionStatus),
        nullable=False,
        default=ScanExecutionStatus.RUNNING,
        server_default=ScanExecutionStatus.RUNNING.name,
        index=True,
    )
    authorization_confirmed = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    score = Column(Integer, nullable=True)
    request_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    duration_ms = Column(Integer, nullable=True)
    scan_date = Column(
        DateTime(timezone = True),
        default = lambda: datetime.now(UTC),
        nullable = False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref = "scans")
    test_results = relationship(
        "TestResult",
        back_populates = "scan",
        cascade = "all, delete-orphan",
        order_by="TestResult.id",
    )

    def __repr__(self) -> str:
        """
        String representation of Scan
        """
        return f"<Scan(id={self.id}, target_url={self.target_url}, user_id={self.user_id})>"

    @property
    def has_vulnerabilities(self) -> bool:
        """
        Check if scan found any vulnerabilities

        Returns:
            bool: True if any test result is vulnerable
        """
        return any(
            result.status == "vulnerable"
            for result in self.test_results
        )

    @property
    def vulnerability_count(self) -> int:
        """
        Count of vulnerabilities found in this scan

        Returns:
            int: Number of vulnerable test results
        """
        return sum(
            1 for result in self.test_results
            if result.status == "vulnerable"
        )
