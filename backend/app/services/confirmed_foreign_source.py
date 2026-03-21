from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from functools import lru_cache

from app.core.config import get_settings
from app.integrations.krx import KrxConfirmedForeignInvestorConnector
from app.providers import ForeignInvestorDailyConfirmed, MarketDataProvider


class ConfirmedForeignInvestorSource(ABC):
    @abstractmethod
    def fetch_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        raise NotImplementedError


class ProviderConfirmedForeignInvestorSource(ConfirmedForeignInvestorSource):
    def __init__(self, provider: MarketDataProvider) -> None:
        self.provider = provider

    def fetch_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        return self.provider.get_foreign_investor_daily_confirmed(stock_code, start_date, end_date)


class KrxConfirmedForeignInvestorSource(ConfirmedForeignInvestorSource):
    def __init__(self, connector: KrxConfirmedForeignInvestorConnector) -> None:
        self.connector = connector

    def fetch_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        return self.connector.fetch_daily_confirmed(stock_code, start_date, end_date)


@lru_cache
def _get_krx_connector() -> KrxConfirmedForeignInvestorConnector:
    settings = get_settings()
    return KrxConfirmedForeignInvestorConnector(
        base_url=settings.krx_base_url,
        timeout_sec=settings.krx_request_timeout_sec,
    )


def resolve_confirmed_foreign_source(provider: MarketDataProvider) -> ConfirmedForeignInvestorSource:
    settings = get_settings()
    mode = (settings.foreign_confirmed_source or 'provider').lower()

    if mode in {'provider', 'auto'}:
        return ProviderConfirmedForeignInvestorSource(provider)
    if mode == 'krx':
        return KrxConfirmedForeignInvestorSource(_get_krx_connector())

    # Unknown mode fallback: provider 기반 경로를 우선 사용한다.
    return ProviderConfirmedForeignInvestorSource(provider)
