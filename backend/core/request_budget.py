"""Thread-safe request budget shared by every scanner in one scan."""

from __future__ import annotations

from threading import Lock


class RequestBudgetExceeded(RuntimeError):
    """Raised before a request when the scan-wide budget is exhausted."""


class RequestBudget:
    def __init__(self, limit: int = 60) -> None:
        if limit < 1:
            raise ValueError("Request budget limit must be positive")
        self.limit = limit
        self._count = 0
        self._lock = Lock()

    def reserve(self) -> int:
        """Reserve one outbound attempt and return the new total."""
        with self._lock:
            if self._count >= self.limit:
                raise RequestBudgetExceeded(
                    f"Scan request budget exhausted ({self.limit} requests maximum)"
                )
            self._count += 1
            return self._count

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    @property
    def remaining(self) -> int:
        with self._lock:
            return self.limit - self._count

