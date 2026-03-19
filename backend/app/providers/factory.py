from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import MarketDataProvider
from app.providers.kis_provider import KisMarketDataProvider
from app.providers.mock_provider import MockMarketDataProvider


@lru_cache
def get_market_data_provider() -> MarketDataProvider:
    settings = get_settings()
    if settings.data_provider.lower() == 'kis':
        return KisMarketDataProvider(
            app_key=settings.kis_app_key,
            app_secret=settings.kis_app_secret,
            base_url=settings.kis_base_url,
        )
    return MockMarketDataProvider()
