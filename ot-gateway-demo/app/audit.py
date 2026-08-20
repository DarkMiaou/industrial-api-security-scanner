from datetime import UTC, datetime
from threading import Lock

from .models import AuditEvent


class AuditStore:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = Lock()

    def record(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        result: str,
        correlation_id: str,
    ) -> AuditEvent:
        event = AuditEvent(
            actor=actor,
            action=action,
            resource=resource,
            result=result,
            timestamp=datetime.now(UTC),
            correlation_id=correlation_id,
        )
        with self._lock:
            self._events.append(event)
        return event

    def find(self, correlation_id: str | None = None) -> list[AuditEvent]:
        with self._lock:
            events = list(self._events)
        if correlation_id is not None:
            events = [event for event in events if event.correlation_id == correlation_id]
        return events

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

