from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class StockMeta:
    code: str
    name: str
    market: str
    market_cap: int


@dataclass
class DailyBar:
    trade_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    trading_value: int


@dataclass
class Quote:
    code: str
    price: float
    trading_value: int


@dataclass
class ForeignInvestorIntradaySnapshot:
    stock_code: str
    as_of: datetime
    net_buy_qty: int | None
    source: str
    is_confirmed: bool = False


@dataclass
class ForeignInvestorDailyConfirmed:
    stock_code: str
    trade_date: date
    net_buy_qty: int | None
    source: str
    is_confirmed: bool = True


class MarketDataProvider(ABC):
    @abstractmethod
    def list_stocks(self, market: str) -> list[StockMeta]:
        raise NotImplementedError

    @abstractmethod
    def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
        raise NotImplementedError

    @abstractmethod
    def get_latest_quote(self, stock_code: str) -> Quote:
        raise NotImplementedError

    @abstractmethod
    def get_foreign_investor_intraday_snapshot(self, stock_code: str) -> ForeignInvestorIntradaySnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_foreign_investor_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        raise NotImplementedError

    @abstractmethod
    def get_foreign_net_buy_aggregate(self, stock_code: str, days: int) -> int:
        raise NotImplementedError
