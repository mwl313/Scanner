from datetime import datetime, timezone
from zoneinfo import ZoneInfo

KST = ZoneInfo('Asia/Seoul')


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_kst(now: datetime | None = None) -> datetime:
    target = now or datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    return target.astimezone(KST)


def is_korean_trading_day(now: datetime | None = None) -> bool:
    return as_kst(now).weekday() < 5
