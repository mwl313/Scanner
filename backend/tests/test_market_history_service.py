from datetime import date, timedelta

from sqlalchemy import func, select

from app.models.stock_daily_bar import StockDailyBar
from app.providers.base import DailyBar
from app.services.market_history_service import ensure_daily_bars_cached, upsert_stock_daily_bars


def _build_bars(start: date, days: int, base_price: int = 10000) -> list[DailyBar]:
    bars: list[DailyBar] = []
    for idx in range(days):
        trade_date = start + timedelta(days=idx)
        close = base_price + idx
        bars.append(
            DailyBar(
                trade_date=trade_date,
                open_price=close - 1,
                high_price=close + 2,
                low_price=close - 2,
                close_price=close,
                volume=1000 + idx,
                trading_value=(1000 + idx) * close,
            )
        )
    return bars


def test_stock_daily_bar_upsert_is_duplicate_safe(db_session):
    stock_code = '005930'
    start = date(2026, 3, 10)
    first = _build_bars(start, 3, base_price=10000)
    second = _build_bars(start, 3, base_price=20000)

    saved_first = upsert_stock_daily_bars(db_session, stock_code, first, source='test:first')
    saved_second = upsert_stock_daily_bars(db_session, stock_code, second, source='test:second')

    assert saved_first == 3
    assert saved_second == 3

    total_rows = db_session.scalar(
        select(func.count()).select_from(StockDailyBar).where(StockDailyBar.stock_code == stock_code)
    )
    assert total_rows == 3

    latest = db_session.scalar(
        select(StockDailyBar)
        .where(StockDailyBar.stock_code == stock_code, StockDailyBar.trade_date == start + timedelta(days=2))
    )
    assert latest is not None
    assert float(latest.close_price) == 20002
    assert latest.source == 'test:second'


def test_ensure_daily_bars_cached_uses_db_first(db_session):
    class Provider:
        def __init__(self) -> None:
            self.calls = 0

        def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
            self.calls += 1
            return _build_bars(date(2025, 1, 1), days, base_price=10000)

    provider = Provider()
    stock_code = '000001'

    first = ensure_daily_bars_cached(db_session, provider, stock_code, 20)
    assert len(first) == 20
    assert provider.calls == 1

    second = ensure_daily_bars_cached(db_session, provider, stock_code, 20)
    assert len(second) == 20
    assert provider.calls == 1


def test_ensure_daily_bars_cached_backfills_when_cache_insufficient(db_session):
    class Provider:
        def __init__(self) -> None:
            self.calls = 0

        def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
            self.calls += 1
            return _build_bars(date(2025, 5, 1), days, base_price=30000)

    provider = Provider()
    stock_code = '000002'

    partial = _build_bars(date(2025, 5, 1), 5, base_price=12000)
    upsert_stock_daily_bars(db_session, stock_code, partial, source='seed')

    bars = ensure_daily_bars_cached(db_session, provider, stock_code, 30)
    assert len(bars) == 30
    assert provider.calls == 1

    total_rows = db_session.scalar(
        select(func.count()).select_from(StockDailyBar).where(StockDailyBar.stock_code == stock_code)
    )
    assert total_rows >= 30
