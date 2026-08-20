from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic


class FixedWindowRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= limit:
                retry_after = max(1, ceil(window_seconds - (now - requests[0])))
                return False, retry_after
            requests.append(now)
            return True, 0

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()

