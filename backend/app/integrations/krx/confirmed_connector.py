from __future__ import annotations

from datetime import date, datetime
import logging
import re
from types import ModuleType

from app.providers.base import ForeignInvestorDailyConfirmed

logger = logging.getLogger(__name__)


class KrxConfirmedForeignInvestorConnector:
    """Fetch confirmed daily foreign investor net-buy quantities from KRX data."""

    def __init__(self, base_url: str, timeout_sec: float = 10.0) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout_sec = timeout_sec

    @staticmethod
    def _to_int_or_none(value) -> int | None:
        if value is None:
            return None
        text = str(value).strip()
        if text == '' or text.lower() == 'nan':
            return None
        normalized = re.sub(r'[^0-9\-]', '', text)
        if normalized in {'', '-'}:
            return None
        try:
            return int(normalized)
        except ValueError:
            return None

    @staticmethod
    def _normalize_trade_date(raw) -> date | None:
        if raw is None:
            return None
        if isinstance(raw, date):
            return raw
        if hasattr(raw, 'to_pydatetime'):
            try:
                return raw.to_pydatetime().date()
            except Exception:
                return None
        text = str(raw).strip()
        if not text:
            return None
        for fmt in ('%Y-%m-%d', '%Y%m%d', '%Y.%m.%d'):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _find_foreign_column(columns: list[str]) -> str | None:
        for candidate in ('외국인합계', '외국인', '외국인순매수', '외국인순매수금액'):
            if candidate in columns:
                return candidate
        for column in columns:
            if '외국인' in column:
                return column
        return None

    @staticmethod
    def _load_pykrx_stock_module() -> ModuleType:
        from pykrx import stock as pykrx_stock

        return pykrx_stock

    def fetch_daily_confirmed(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ForeignInvestorDailyConfirmed]:
        if start_date > end_date:
            return []

        try:
            pykrx_stock = self._load_pykrx_stock_module()
            frame = pykrx_stock.get_market_trading_volume_by_date(
                fromdate=start_date.strftime('%Y%m%d'),
                todate=end_date.strftime('%Y%m%d'),
                ticker=stock_code,
                on='순매수',
            )
        except Exception as exc:
            logger.warning('KRX confirmed foreign fetch failed for %s: %s', stock_code, exc)
            return []

        if frame is None or getattr(frame, 'empty', True):
            return []

        columns = [str(item) for item in list(getattr(frame, 'columns', []))]
        foreign_column = self._find_foreign_column(columns)
        if not foreign_column:
            logger.warning(
                'KRX confirmed foreign fetch missing foreign column for %s (columns=%s)',
                stock_code,
                columns,
            )
            return []

        rows: list[ForeignInvestorDailyConfirmed] = []
        for index_value, row in frame.iterrows():
            trade_date = self._normalize_trade_date(index_value)
            if not trade_date:
                continue
            if trade_date < start_date or trade_date > end_date:
                continue
            row_value = row.get(foreign_column) if hasattr(row, 'get') else None
            rows.append(
                ForeignInvestorDailyConfirmed(
                    stock_code=stock_code,
                    trade_date=trade_date,
                    net_buy_value=self._to_int_or_none(row_value),
                    source='krx_confirmed_daily',
                    is_confirmed=True,
                )
            )

        rows.sort(key=lambda item: item.trade_date)
        return rows
