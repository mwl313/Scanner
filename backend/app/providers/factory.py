from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import MarketDataProvider
from app.providers.kis_provider import KisMarketDataProvider
from app.providers.mock_provider import MockMarketDataProvider


def create_market_data_provider(provider_name: str | None = None) -> MarketDataProvider:
    settings = get_settings()
    selected = (provider_name or settings.data_provider).lower()
    if selected == 'kis':
        return KisMarketDataProvider(
            app_key=settings.kis_app_key,
            app_secret=settings.kis_app_secret,
            base_url=settings.kis_base_url,
            timeout_sec=settings.kis_request_timeout_sec,
            request_interval_ms=settings.kis_request_interval_ms,
            token_retry_cooldown_sec=settings.kis_token_retry_cooldown_sec,
            universe_limit=settings.kis_universe_limit,
            universe_cache_hours=settings.kis_universe_cache_hours,
        )
    return MockMarketDataProvider()


@lru_cache
def get_market_data_provider() -> MarketDataProvider:
    settings = get_settings()
    return create_market_data_provider(settings.data_provider)
