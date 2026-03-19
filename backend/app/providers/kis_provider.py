from app.core.exceptions import AppError
from app.providers.base import DailyBar, MarketDataProvider, Quote, StockMeta


class KisMarketDataProvider(MarketDataProvider):
    """
    MVP에서는 KIS 연동 인터페이스만 유지하고, 실제 엔드포인트 연결은 운영 키 준비 후 확장한다.
    """

    def __init__(self, app_key: str | None, app_secret: str | None, base_url: str) -> None:
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url

    def _ensure_credentials(self) -> None:
        if not self.app_key or not self.app_secret:
            raise AppError(
                code='kis_credentials_missing',
                message='KIS provider requires API credentials',
                status_code=500,
            )

    def list_stocks(self, market: str) -> list[StockMeta]:
        self._ensure_credentials()
        raise AppError(
            code='kis_not_implemented',
            message='KIS list_stocks endpoint mapping is not implemented in MVP mock mode',
            status_code=501,
        )

    def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
        self._ensure_credentials()
        raise AppError(
            code='kis_not_implemented',
            message='KIS get_daily_bars endpoint mapping is not implemented in MVP mock mode',
            status_code=501,
        )

    def get_latest_quote(self, stock_code: str) -> Quote:
        self._ensure_credentials()
        raise AppError(
            code='kis_not_implemented',
            message='KIS get_latest_quote endpoint mapping is not implemented in MVP mock mode',
            status_code=501,
        )

    def get_foreign_net_buy_aggregate(self, stock_code: str, days: int) -> int:
        self._ensure_credentials()
        raise AppError(
            code='kis_not_implemented',
            message='KIS get_foreign_net_buy_aggregate endpoint mapping is not implemented in MVP mock mode',
            status_code=501,
        )
