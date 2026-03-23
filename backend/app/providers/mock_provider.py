from datetime import date, timedelta
import random

from app.providers.base import (
    DailyBar,
    ForeignInvestorDailyConfirmed,
    ForeignInvestorIntradaySnapshot,
    MarketDataProvider,
    Quote,
    StockMeta,
)
from app.providers.mock_symbols import MOCK_STOCKS
from app.utils.datetime_utils import utcnow


class MockMarketDataProvider(MarketDataProvider):
    def __init__(self) -> None:
        self._stocks = [
            StockMeta(code=item['code'], name=item['name'], market='KOSPI', market_cap=item['market_cap'])
            for item in MOCK_STOCKS
        ]

    def list_stocks(self, market: str) -> list[StockMeta]:
        if market.upper() != 'KOSPI':
            return []
        return list(self._stocks)

    def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
        seed = int(stock_code)
        rng = random.Random(seed)

        base_price = rng.uniform(18000, 220000)
        drift = rng.uniform(0.0002, 0.0012)
        volatility = rng.uniform(0.008, 0.03)

        today = utcnow().date()
        close = base_price
        bars: list[DailyBar] = []

        for idx in range(days):
            day = today - timedelta(days=(days - idx))
            shock = rng.uniform(-volatility, volatility)
            pattern = 0.0

            if idx > days - 8:
                # 최근 눌림 후 반등 패턴을 강제로 넣어 신호 후보를 만들기 위함.
                last_idx = idx - (days - 8)
                if last_idx <= 3:
                    pattern = -0.018
                else:
                    pattern = 0.022

            close = max(1000.0, close * (1 + drift + shock + pattern))
            open_price = close * (1 + rng.uniform(-0.01, 0.01))
            high_price = max(open_price, close) * (1 + rng.uniform(0.001, 0.025))
            low_price = min(open_price, close) * (1 - rng.uniform(0.001, 0.02))

            volume = int(rng.uniform(120000, 2000000))
            trading_value = int(close * volume)

            bars.append(
                DailyBar(
                    trade_date=day,
                    open_price=round(open_price, 2),
                    high_price=round(high_price, 2),
                    low_price=round(low_price, 2),
                    close_price=round(close, 2),
                    volume=volume,
                    trading_value=trading_value,
                )
            )

        return bars

    def get_latest_quote(self, stock_code: str) -> Quote:
        bar = self.get_daily_bars(stock_code, 90)[-1]
        return Quote(code=stock_code, price=bar.close_price, trading_value=bar.trading_value)

    def get_foreign_investor_intraday_snapshot(self, stock_code: str) -> ForeignInvestorIntradaySnapshot:
        seed = int(stock_code) + 29
        rng = random.Random(seed)
        value = int(rng.uniform(-5000000000, 5000000000))
        return ForeignInvestorIntradaySnapshot(
            stock_code=stock_code,
            as_of=utcnow(),
            net_buy_qty=value,
            source='mock_intraday_snapshot',
            is_confirmed=False,
        )

    def get_foreign_investor_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        if start_date > end_date:
            return []

        seed = int(stock_code) + 17
        rng = random.Random(seed)

        entries: list[ForeignInvestorDailyConfirmed] = []
        cursor = start_date
        while cursor <= end_date:
            if cursor.weekday() < 5:
                value = int(rng.uniform(-800000000, 1200000000))
                if int(stock_code[-1]) % 2 == 0:
                    value += 250000000
                entries.append(
                    ForeignInvestorDailyConfirmed(
                        stock_code=stock_code,
                        trade_date=cursor,
                        net_buy_qty=value,
                        source='mock_daily_confirmed',
                        is_confirmed=True,
                    )
                )
            cursor += timedelta(days=1)
        return entries

    def get_foreign_net_buy_aggregate(self, stock_code: str, days: int) -> int:
        target_days = max(days, 1)
        end_date = utcnow().date()
        start_date = end_date - timedelta(days=target_days * 2)
        rows = self.get_foreign_investor_daily_confirmed(stock_code, start_date, end_date)
        rows_sorted = sorted(rows, key=lambda item: item.trade_date, reverse=True)
        picked_values: list[int] = []
        for item in rows_sorted:
            if item.net_buy_qty is None:
                continue
            picked_values.append(int(item.net_buy_qty))
            if len(picked_values) >= target_days:
                break
        return int(sum(picked_values))
