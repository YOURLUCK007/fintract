"""Cross-cutting helpers: audit logging + a lightweight in-memory rate limiter."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from sqlalchemy.orm import Session

from .config import settings
from .models import AuditLog


def write_audit(db: Session, action: str, user_id: int | None = None, ip: str = "", detail: str = "") -> None:
    db.add(AuditLog(action=action, user_id=user_id, ip=ip, detail=detail))
    db.commit()


class RateLimiter:
    """Sliding-window limiter keyed by client identity (IP).

    Suitable for a single-process deployment / demo. For multi-instance, back this
    with Redis (settings.redis_url) — the interface stays the same.
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True


rate_limiter = RateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)
