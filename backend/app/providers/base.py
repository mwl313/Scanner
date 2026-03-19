from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


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
    def get_foreign_net_buy_aggregate(self, stock_code: str, days: int) -> int:
        raise NotImplementedError
