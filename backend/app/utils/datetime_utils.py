from datetime import date, datetime, timedelta, timezone
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


def latest_korean_trading_date(now: datetime | None = None) -> date:
    """Return the latest Korean trading date (weekend-adjusted, KST-based)."""
    kst_now = as_kst(now)
    kst_date = kst_now.date()
    weekday = kst_now.weekday()
    if weekday == 5:  # Saturday
        return kst_date - timedelta(days=1)
    if weekday == 6:  # Sunday
        return kst_date - timedelta(days=2)
    return kst_date
