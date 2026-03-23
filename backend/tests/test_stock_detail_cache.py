from datetime import date, timedelta

from sqlalchemy import func, select

from app.api.routes import stocks as stocks_route
from app.models.foreign_investor_daily import ForeignInvestorDaily
from app.models.scan_result import ScanResult
from app.models.scan_run import ScanRun
from app.models.stock_daily_bar import StockDailyBar
from app.models.strategy import Strategy
from app.providers.base import DailyBar, ForeignInvestorIntradaySnapshot
from app.services.auth_service import signup_user
from app.services.market_history_service import upsert_stock_daily_bars
from app.utils.datetime_utils import utcnow


def _build_bars(start: date, days: int, base_price: int = 10000) -> list[DailyBar]:
    rows: list[DailyBar] = []
    for idx in range(days):
        trade_date = start + timedelta(days=idx)
        close = base_price + idx
        rows.append(
            DailyBar(
                trade_date=trade_date,
                open_price=close - 2,
                high_price=close + 3,
                low_price=close - 3,
                close_price=close,
                volume=10_000 + idx,
                trading_value=(10_000 + idx) * close,
            )
        )
    return rows


def _create_scan_result(db_session, user, stock_code: str = '005930', stock_name: str = '삼성전자') -> ScanResult:
    strategy = Strategy(user_id=user.id, name='detail-cache', market='KOSPI', is_active=True)
    db_session.add(strategy)
    db_session.flush()

    run = ScanRun(
        strategy_id=strategy.id,
        run_type='manual',
        started_at=utcnow(),
        finished_at=utcnow(),
        status='completed',
        total_scanned=1,
        total_matched=1,
        failed_count=0,
    )
    db_session.add(run)
    db_session.flush()

    result = ScanResult(
        scan_run_id=run.id,
        strategy_id=strategy.id,
        stock_code=stock_code,
        stock_name=stock_name,
        market='KOSPI',
        price=70000,
        ma5=69800,
        ma20=69500,
        ma60=68000,
        bb_upper=72000,
        bb_mid=70000,
        bb_lower=68000,
        rsi=37.5,
        rsi_signal=35.2,
        foreign_net_buy_qty=123456789,
        foreign_net_buy_confirmed_qty=123456789,
        foreign_net_buy_snapshot_qty=1111111,
        foreign_data_status='confirmed',
        foreign_data_source='confirmed:test|snapshot:test',
        foreign_coverage_days=3,
        foreign_required_days=3,
        trading_value=12300000000,
        score=88,
        grade='A',
        matched_reasons_json=['테스트'],
        failed_reasons_json=[],
    )
    db_session.add(result)
    db_session.add_all(
        [
            ForeignInvestorDaily(
                stock_code=stock_code,
                trade_date=date(2026, 3, 19),
                net_buy_qty=1200,
                source='test_source',
                is_confirmed=True,
            ),
            ForeignInvestorDaily(
                stock_code=stock_code,
                trade_date=date(2026, 3, 20),
                net_buy_qty=-300,
                source='test_source',
                is_confirmed=True,
            ),
            ForeignInvestorDaily(
                stock_code=stock_code,
                trade_date=date(2026, 3, 21),
                net_buy_qty=550,
                source='test_source',
                is_confirmed=True,
            ),
        ]
    )
    db_session.commit()
    db_session.refresh(result)
    return result


def test_stock_detail_reads_recent_closes_from_db_cache_first(db_session, monkeypatch):
    user = signup_user(db_session, 'stock-cache-hit@example.com', 'password123', 'password123')
    result = _create_scan_result(db_session, user)
    upsert_stock_daily_bars(
        db_session,
        result.stock_code,
        _build_bars(date(2026, 1, 1), 40, base_price=60000),
        source='test_seed',
    )

    class CacheHitProvider:
        def __init__(self) -> None:
            self.daily_calls = 0

        def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
            _ = stock_code, days
            self.daily_calls += 1
            raise AssertionError('provider.get_daily_bars should not be called on cache hit')

        def get_foreign_investor_intraday_snapshot(self, stock_code: str) -> ForeignInvestorIntradaySnapshot:
            return ForeignInvestorIntradaySnapshot(
                stock_code=stock_code,
                as_of=utcnow(),
                net_buy_qty=333,
                source='test_intraday_snapshot',
                is_confirmed=False,
            )

    provider = CacheHitProvider()
    monkeypatch.setattr(stocks_route, 'get_market_data_provider', lambda: provider)

    detail = stocks_route.stock_detail(result.stock_code, db_session, user)

    assert provider.daily_calls == 0
    assert len(detail.recent_closes) == 30
    assert detail.foreign_net_buy_snapshot_qty == 333
    assert len(detail.foreign_recent_daily) == 3
    assert detail.foreign_recent_daily[0].net_buy_qty == 550


def test_stock_detail_backfills_when_daily_bar_cache_is_insufficient(db_session, monkeypatch):
    user = signup_user(db_session, 'stock-cache-miss@example.com', 'password123', 'password123')
    result = _create_scan_result(db_session, user, stock_code='000660', stock_name='SK하이닉스')
    upsert_stock_daily_bars(
        db_session,
        result.stock_code,
        _build_bars(date(2026, 2, 1), 5, base_price=150000),
        source='test_seed',
    )

    class BackfillProvider:
        def __init__(self) -> None:
            self.daily_calls = 0

        def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
            _ = stock_code
            self.daily_calls += 1
            return _build_bars(date(2025, 10, 1), days, base_price=140000)

        def get_foreign_investor_intraday_snapshot(self, stock_code: str) -> ForeignInvestorIntradaySnapshot:
            return ForeignInvestorIntradaySnapshot(
                stock_code=stock_code,
                as_of=utcnow(),
                net_buy_qty=555,
                source='test_intraday_snapshot',
                is_confirmed=False,
            )

    provider = BackfillProvider()
    monkeypatch.setattr(stocks_route, 'get_market_data_provider', lambda: provider)

    detail = stocks_route.stock_detail(result.stock_code, db_session, user)

    assert provider.daily_calls == 1
    assert len(detail.recent_closes) == 30
    assert len(detail.foreign_recent_daily) == 3
    row_count = db_session.scalar(
        select(func.count()).select_from(StockDailyBar).where(StockDailyBar.stock_code == result.stock_code)
    )
    assert row_count >= 30
