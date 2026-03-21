from datetime import date, datetime

import pytest

from app.integrations.krx.confirmed_connector import KrxConfirmedForeignInvestorConnector
from app.models.foreign_investor_daily import ForeignInvestorDaily
from app.providers.base import (
    DailyBar,
    ForeignInvestorDailyConfirmed,
    ForeignInvestorIntradaySnapshot,
    MarketDataProvider,
    Quote,
    StockMeta,
)
from app.providers.mock_provider import MockMarketDataProvider
from app.services.confirmed_foreign_source import (
    ConfirmedForeignInvestorSource,
    KrxConfirmedForeignInvestorSource,
    ProviderConfirmedForeignInvestorSource,
    resolve_confirmed_foreign_source,
)
from app.services.foreign_investor_service import sync_confirmed_foreign_for_stock


@pytest.fixture(autouse=True)
def clear_settings_cache():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class DummyProvider(MarketDataProvider):
    def list_stocks(self, market: str) -> list[StockMeta]:
        _ = market
        return []

    def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
        _ = stock_code, days
        return []

    def get_latest_quote(self, stock_code: str) -> Quote:
        _ = stock_code
        return Quote(code='000000', price=0.0, trading_value=0)

    def get_foreign_investor_intraday_snapshot(self, stock_code: str) -> ForeignInvestorIntradaySnapshot:
        _ = stock_code
        return ForeignInvestorIntradaySnapshot(
            stock_code='000000',
            as_of=datetime.now(),
            net_buy_value=None,
            source='dummy',
            is_confirmed=False,
        )

    def get_foreign_investor_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        _ = stock_code, start_date, end_date
        raise AssertionError('provider daily confirmed should not be called in this test')

    def get_foreign_net_buy_aggregate(self, stock_code: str, days: int) -> int:
        _ = stock_code, days
        return 0


class StubConfirmedSource(ConfirmedForeignInvestorSource):
    def __init__(self, rows: list[ForeignInvestorDailyConfirmed]) -> None:
        self.rows = rows

    def fetch_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        _ = stock_code, start_date, end_date
        return list(self.rows)


def test_resolve_source_auto_mock_uses_provider(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv('DATA_PROVIDER', 'mock')
    monkeypatch.setenv('FOREIGN_CONFIRMED_SOURCE', 'auto')
    get_settings.cache_clear()

    source = resolve_confirmed_foreign_source(MockMarketDataProvider())
    assert isinstance(source, ProviderConfirmedForeignInvestorSource)


def test_resolve_source_auto_kis_uses_provider(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv('DATA_PROVIDER', 'kis')
    monkeypatch.setenv('FOREIGN_CONFIRMED_SOURCE', 'auto')
    get_settings.cache_clear()

    source = resolve_confirmed_foreign_source(MockMarketDataProvider())
    assert isinstance(source, ProviderConfirmedForeignInvestorSource)


def test_resolve_source_explicit_krx_uses_krx(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv('DATA_PROVIDER', 'kis')
    monkeypatch.setenv('FOREIGN_CONFIRMED_SOURCE', 'krx')
    get_settings.cache_clear()

    source = resolve_confirmed_foreign_source(MockMarketDataProvider())
    assert isinstance(source, KrxConfirmedForeignInvestorSource)


def test_sync_confirmed_foreign_for_stock_uses_confirmed_source(db_session):
    rows = [
        ForeignInvestorDailyConfirmed(
            stock_code='005930',
            trade_date=date(2026, 3, 19),
            net_buy_value=12345,
            source='krx_confirmed_daily',
            is_confirmed=True,
        )
    ]
    saved = sync_confirmed_foreign_for_stock(
        db_session,
        DummyProvider(),
        stock_code='005930',
        start_date=date(2026, 3, 19),
        end_date=date(2026, 3, 19),
        confirmed_source=StubConfirmedSource(rows),
        commit=True,
    )

    assert saved == 1
    persisted = db_session.query(ForeignInvestorDaily).filter_by(stock_code='005930').all()
    assert len(persisted) == 1
    assert persisted[0].source == 'krx_confirmed_daily'


def test_krx_connector_normalizes_confirmed_rows(monkeypatch):
    connector = KrxConfirmedForeignInvestorConnector(base_url='http://data.krx.co.kr')

    class FakeFrame:
        empty = False
        columns = ['외국인합계']

        @staticmethod
        def iterrows():
            yield '2026-03-18', {'외국인합계': '1,234'}
            yield '2026-03-19', {'외국인합계': '-200'}

    class FakeStockModule:
        @staticmethod
        def get_market_trading_value_by_date(fromdate, todate, ticker, on='순매수'):
            _ = fromdate, todate, ticker, on
            return FakeFrame()

    monkeypatch.setattr(connector, '_load_pykrx_stock_module', lambda: FakeStockModule)

    rows = connector.fetch_daily_confirmed('005930', date(2026, 3, 18), date(2026, 3, 19))

    assert len(rows) == 2
    assert rows[0].trade_date == date(2026, 3, 18)
    assert rows[0].net_buy_value == 1234
    assert rows[1].net_buy_value == -200
    assert rows[0].source == 'krx_confirmed_daily'
