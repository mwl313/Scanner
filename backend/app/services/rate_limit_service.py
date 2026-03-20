from __future__ import annotations

from collections import deque
import math
import threading
import time

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.utils.request_meta import get_client_ip


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._store: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, max_attempts: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            bucket = self._store.get(key)
            if bucket is None:
                bucket = deque()
                self._store[key] = bucket

            threshold = now - window_seconds
            while bucket and bucket[0] <= threshold:
                bucket.popleft()

            if len(bucket) >= max_attempts:
                retry_after = max(1, int(math.ceil(window_seconds - (now - bucket[0]))))
                return False, retry_after

            bucket.append(now)
            return True, 0

    def reset(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)


_rate_limiter = InMemoryRateLimiter()


def _enforce_limit(scope: str, identity: str, max_attempts: int, window_seconds: int) -> None:
    key = f'{scope}:{identity}'
    allowed, retry_after = _rate_limiter.hit(key, max_attempts=max_attempts, window_seconds=window_seconds)
    if allowed:
        return

    raise AppError(
        code='rate_limit_exceeded',
        message='Too many authentication attempts. Please retry later.',
        status_code=429,
        details={
            'scope': scope,
            'retry_after_seconds': retry_after,
            'max_attempts': max_attempts,
            'window_seconds': window_seconds,
        },
    )


def enforce_login_rate_limit(request: Request, email: str) -> None:
    settings = get_settings()
    normalized_email = email.lower().strip()
    client_ip = get_client_ip(request)

    _enforce_limit(
        scope='auth_login_ip',
        identity=client_ip,
        max_attempts=max(settings.auth_login_rate_limit_ip_max, 1),
        window_seconds=max(settings.auth_login_rate_limit_window_sec, 1),
    )
    _enforce_limit(
        scope='auth_login_email',
        identity=normalized_email,
        max_attempts=max(settings.auth_login_rate_limit_email_max, 1),
        window_seconds=max(settings.auth_login_rate_limit_window_sec, 1),
    )


def clear_login_rate_limit(request: Request, email: str) -> None:
    normalized_email = email.lower().strip()
    client_ip = get_client_ip(request)
    _rate_limiter.reset(f'auth_login_ip:{client_ip}')
    _rate_limiter.reset(f'auth_login_email:{normalized_email}')


def enforce_signup_rate_limit(request: Request, email: str) -> None:
    settings = get_settings()
    normalized_email = email.lower().strip()
    client_ip = get_client_ip(request)

    _enforce_limit(
        scope='auth_signup_ip',
        identity=client_ip,
        max_attempts=max(settings.auth_signup_rate_limit_ip_max, 1),
        window_seconds=max(settings.auth_signup_rate_limit_window_sec, 1),
    )
    _enforce_limit(
        scope='auth_signup_email',
        identity=normalized_email,
        max_attempts=max(settings.auth_signup_rate_limit_email_max, 1),
        window_seconds=max(settings.auth_signup_rate_limit_window_sec, 1),
    )

