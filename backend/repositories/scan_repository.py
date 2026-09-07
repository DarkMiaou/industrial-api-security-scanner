"""
ⒸAngelaMos | 2025
Handles all Scan model database queries
"""

from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from config import settings
from core.enums import GatewayProfile, ScanExecutionStatus
from models.Scan import Scan


class ScanRepository:
    """
    Repository for Scan database operations
    """
    @staticmethod
    def create_scan(
        db: Session,
        user_id: int,
        target_url: str,
        target_key: str,
        target_name: str,
        profile: GatewayProfile,
        authorization_confirmed: bool,
        commit: bool = True
    ) -> Scan:
        """
        Create a new scan

        Args:
            db: Database session
            user_id: User ID who initiated the scan
            target_url: Target URL to scan
            commit: Whether to commit the transaction

        Returns:
            Scan: Created scan instance
        """
        scan = Scan(
            user_id = user_id,
            target_url = target_url,
            target_key=target_key,
            target_name=target_name,
            profile=profile,
            status=ScanExecutionStatus.RUNNING,
            authorization_confirmed=authorization_confirmed,
            request_count=0,
            scan_date = datetime.now(UTC),
        )
        db.add(scan)
        if commit:
            db.commit()
            db.refresh(scan)
        return scan

    @staticmethod
    def finalize_scan(
        db: Session,
        scan: Scan,
        *,
        status: ScanExecutionStatus,
        score: int | None,
        request_count: int,
        duration_ms: int,
    ) -> Scan:
        """Persist the terminal execution metrics for one scan."""
        scan.status = status
        scan.score = score
        scan.request_count = request_count
        scan.duration_ms = duration_ms
        scan.completed_at = datetime.now(UTC)
        db.commit()
        db.refresh(scan)
        return scan

    @staticmethod
    def get_by_id(db: Session, scan_id: int) -> Scan | None:
        """
        Get scan by ID with test results loaded

        Args:
            db: Database session
            scan_id: Scan ID

        Returns:
            Scan | None: Scan instance or None if not found
        """
        return (
            db.query(Scan).options(
                joinedload(Scan.test_results)
            ).filter(Scan.id == scan_id).first()
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int | None = None
    ) -> list[Scan]:
        """
        Get all scans for a user with pagination.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return (DEFAULT_PAGINATION_LIMIT)

        Returns:
            list[Scan]: List of scans with test results
        """
        if limit is None:
            limit = settings.DEFAULT_PAGINATION_LIMIT

        return (
            db.query(Scan).options(
                joinedload(Scan.test_results)
            ).filter(Scan.user_id == user_id).order_by(
                Scan.scan_date.desc()
            ).offset(skip).limit(limit).all()
        )

    @staticmethod
    def get_recent(db: Session,
                   limit: int | None = None) -> list[Scan]:
        """
        Get most recent scans across all users.

        Args:
            db: Database session
            limit: Maximum number of scans to return (DEFAULT_PAGINATION_LIMIT)

        Returns:
            list[Scan]: List of recent scans
        """
        if limit is None:
            limit = settings.DEFAULT_PAGINATION_LIMIT

        return (
            db.query(Scan).options(
                joinedload(Scan.test_results)
            ).order_by(Scan.scan_date.desc()).limit(limit).all()
        )

    @staticmethod
    def delete(
        db: Session,
        scan_id: int,
        commit: bool = True
    ) -> bool:
        """
        Delete a scan (cascades to test results).

        Args:
            db: Database session
            scan_id: Scan ID to delete
            commit: Whether to commit the transaction

        Returns:
            bool: True if deleted, False if not found
        """
        scan = ScanRepository.get_by_id(db, scan_id)
        if scan:
            db.delete(scan)
            if commit:
                db.commit()
            return True
        return False

    @staticmethod
    def count_by_user(db: Session, user_id: int) -> int:
        """
        Count total scans for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            int: Total number of scans
        """
        return db.query(Scan).filter(Scan.user_id == user_id).count()
