from datetime import date, datetime, timedelta, timezone

from app.utils.datetime_utils import latest_korean_trading_date


def test_latest_korean_trading_date_friday_kst_and_utc():
    friday_kst = datetime(2026, 3, 20, 14, 0, tzinfo=timezone(timedelta(hours=9)))
    friday_utc = datetime(2026, 3, 20, 5, 0, tzinfo=timezone.utc)

    assert latest_korean_trading_date(friday_kst) == date(2026, 3, 20)
    assert latest_korean_trading_date(friday_utc) == date(2026, 3, 20)


def test_latest_korean_trading_date_saturday_kst_and_utc():
    saturday_kst = datetime(2026, 3, 21, 11, 0, tzinfo=timezone(timedelta(hours=9)))
    saturday_utc = datetime(2026, 3, 20, 18, 0, tzinfo=timezone.utc)

    assert latest_korean_trading_date(saturday_kst) == date(2026, 3, 20)
    assert latest_korean_trading_date(saturday_utc) == date(2026, 3, 20)


def test_latest_korean_trading_date_sunday_kst_and_utc():
    sunday_kst = datetime(2026, 3, 22, 11, 0, tzinfo=timezone(timedelta(hours=9)))
    sunday_utc = datetime(2026, 3, 21, 18, 0, tzinfo=timezone.utc)

    assert latest_korean_trading_date(sunday_kst) == date(2026, 3, 20)
    assert latest_korean_trading_date(sunday_utc) == date(2026, 3, 20)
