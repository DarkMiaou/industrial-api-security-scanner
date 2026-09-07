"""Correlated audit validation for one reversible simulated OT command."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from core.enums import ScanStatus, Severity, TestType
from schemas.test_result_schemas import TestResultCreate

from .base_scanner import BaseScanner
from .payloads import ADMIN, OT_AUDIT_PUMP_ID, SUPERVISOR


class OTAuditScanner(BaseScanner):
    """Issue one correlated command, inspect its audit event, then restore the pump."""

    REQUIRED_EVENT_FIELDS = {
        "actor",
        "action",
        "resource",
        "result",
        "timestamp",
        "correlation_id",
    }

    def scan(self) -> TestResultCreate:
        supervisor_token, supervisor_login = self.authenticate_gateway(
            SUPERVISOR.username,
            SUPERVISOR.password,
        )
        admin_token, admin_login = self.authenticate_gateway(
            ADMIN.username,
            ADMIN.password,
        )
        supervisor_headers = {"Authorization": f"Bearer {supervisor_token}"}
        initial = self.make_request(
            "GET",
            f"/pumps/{OT_AUDIT_PUMP_ID}",
            headers=supervisor_headers,
        )
        initial_status = self._pump_status(initial)
        if initial.status_code != 200 or initial_status is None:
            return TestResultCreate(
                test_name=TestType.OT_AUDIT,
                status=ScanStatus.ERROR,
                severity=Severity.INFO,
                details="The initial pump state could not be established for the audit control",
                evidence_json={"initial_state": self.collect_evidence(initial)},
                recommendations_json=["Verify access to the audit test pump"],
            )

        command_action = "start" if initial_status == "stopped" else "stop"
        restore_action = "stop" if initial_status == "stopped" else "start"
        correlation_id = f"iass-audit-{uuid4()}"
        command_headers = {
            **supervisor_headers,
            "X-Correlation-ID": correlation_id,
        }
        command_attempted = False
        try:
            command_attempted = True
            command = self.make_request(
                "POST",
                f"/pumps/{OT_AUDIT_PUMP_ID}/{command_action}",
                headers=command_headers,
            )
            audit = self.make_request(
                "GET",
                "/audit/events",
                params={"correlation_id": correlation_id},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        except Exception:
            self._restore_after_failure(
                command_attempted,
                restore_action,
                supervisor_headers,
            )
            raise

        restored = self.make_request(
            "POST",
            f"/pumps/{OT_AUDIT_PUMP_ID}/{restore_action}",
            headers={
                **supervisor_headers,
                "X-Correlation-ID": f"iass-restore-{uuid4()}",
            },
        )
        restored_status = self._pump_status(restored)
        evidence: dict[str, Any] = {
            "control": "ot_correlated_audit",
            "authentication": {
                "supervisor": supervisor_login,
                "admin": admin_login,
            },
            "correlation_id": correlation_id,
            "initial_state": self.collect_evidence(
                initial,
                pump_id=OT_AUDIT_PUMP_ID,
                pump_status=initial_status,
            ),
            "command": self.collect_evidence(
                command,
                action=f"pump.{command_action}",
                correlation_id=correlation_id,
            ),
            "audit_lookup": self.collect_evidence(
                audit,
                correlation_id=correlation_id,
            ),
            "restoration": self.collect_evidence(
                restored,
                action=f"pump.{restore_action}",
                restored_status=restored_status,
            ),
            "requests_used": 6,
        }

        if restored.status_code != 200 or restored_status != initial_status:
            return TestResultCreate(
                test_name=TestType.OT_AUDIT,
                status=ScanStatus.ERROR,
                severity=Severity.HIGH,
                details="The audit control could not restore the initial pump state",
                evidence_json=evidence,
                recommendations_json=[
                    "Reset the local gateway before running another OT control"
                ],
            )
        if command.status_code != 200 or audit.status_code != 200:
            return TestResultCreate(
                test_name=TestType.OT_AUDIT,
                status=ScanStatus.ERROR,
                severity=Severity.INFO,
                details="The correlated audit scenario returned an unexpected response",
                evidence_json=evidence,
                recommendations_json=["Verify the Supervisor and Admin audit permissions"],
            )

        events = self._events(audit)
        if not events:
            return TestResultCreate(
                test_name=TestType.OT_AUDIT,
                status=ScanStatus.VULNERABLE,
                severity=Severity.HIGH,
                details="The simulated OT command produced no correlated audit event",
                evidence_json=evidence,
                recommendations_json=[
                    "Record every process-changing command in an append-only audit trail",
                    "Make events searchable by a scanner-generated correlation identifier",
                ],
            )

        event = events[0]
        missing_fields = sorted(self.REQUIRED_EVENT_FIELDS - event.keys())
        expected_values = {
            "actor": SUPERVISOR.username,
            "action": f"pump.{command_action}",
            "resource": OT_AUDIT_PUMP_ID,
            "result": "allowed",
            "correlation_id": correlation_id,
        }
        incorrect_fields = sorted(
            field for field, expected in expected_values.items() if event.get(field) != expected
        )
        if not self._valid_timestamp(event.get("timestamp")):
            incorrect_fields.append("timestamp")
        evidence["event_validation"] = {
            "missing_fields": missing_fields,
            "incorrect_fields": incorrect_fields,
        }
        if missing_fields or incorrect_fields:
            return TestResultCreate(
                test_name=TestType.OT_AUDIT,
                status=ScanStatus.VULNERABLE,
                severity=Severity.MEDIUM,
                details="The OT audit event is present but incomplete or inconsistent",
                evidence_json=evidence,
                recommendations_json=[
                    "Record actor, action, resource, result, timestamp and correlation ID"
                ],
            )

        return TestResultCreate(
            test_name=TestType.OT_AUDIT,
            status=ScanStatus.SAFE,
            severity=Severity.INFO,
            details="The reversible OT command produced a complete correlated audit event",
            evidence_json=evidence,
            recommendations_json=["Keep correlated OT command auditing enabled"],
        )

    @staticmethod
    def _pump_status(response: Any) -> str | None:
        try:
            status = response.json().get("status")
        except (ValueError, AttributeError):
            return None
        return status if status in {"running", "stopped"} else None

    @staticmethod
    def _events(response: Any) -> list[dict[str, Any]]:
        try:
            events = response.json().get("events")
        except (ValueError, AttributeError):
            return []
        if not isinstance(events, list):
            return []
        return [event for event in events if isinstance(event, dict)]

    @staticmethod
    def _valid_timestamp(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return True

    def _restore_after_failure(
        self,
        attempted: bool,
        restore_action: str,
        headers: dict[str, str],
    ) -> None:
        if not attempted:
            return
        try:
            self.make_request(
                "POST",
                f"/pumps/{OT_AUDIT_PUMP_ID}/{restore_action}",
                headers=headers,
            )
        except Exception as cleanup_error:
            raise RuntimeError(
                "OT audit failed and pump restoration could not be confirmed"
            ) from cleanup_error
