from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import io
import logging
import re
import threading
import time
import zipfile

import httpx

from app.core.exceptions import AppError
from app.providers.base import (
    DailyBar,
    ForeignInvestorDailyConfirmed,
    ForeignInvestorIntradaySnapshot,
    MarketDataProvider,
    Quote,
    StockMeta,
)
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


class KisMarketDataProvider(MarketDataProvider):
    TOKEN_ENDPOINT = '/oauth2/tokenP'
    QUOTE_ENDPOINT = '/uapi/domestic-stock/v1/quotations/inquire-price'
    DAILY_ENDPOINT = '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
    INVESTOR_ENDPOINT = '/uapi/domestic-stock/v1/quotations/inquire-investor'
    INVESTOR_DAILY_ENDPOINT = '/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily'
    KOSPI_MASTER_ZIP_URL = 'https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip'

    FIXED_FIELD_WIDTHS = [
        2,
        1,
        4,
        4,
        4,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        9,
        5,
        5,
        1,
        1,
        1,
        2,
        1,
        1,
        1,
        2,
        2,
        2,
        3,
        1,
        3,
        12,
        12,
        8,
        15,
        21,
        2,
        7,
        1,
        1,
        1,
        1,
        1,
        9,
        9,
        9,
        5,
        9,
        8,
        9,
        3,
        1,
        1,
        1,
    ]
    FIXED_FIELD_COLUMNS = [
        '그룹코드',
        '시가총액규모',
        '지수업종대분류',
        '지수업종중분류',
        '지수업종소분류',
        '제조업',
        '저유동성',
        '지배구조지수종목',
        'KOSPI200섹터업종',
        'KOSPI100',
        'KOSPI50',
        'KRX',
        'ETP',
        'ELW발행',
        'KRX100',
        'KRX자동차',
        'KRX반도체',
        'KRX바이오',
        'KRX은행',
        'SPAC',
        'KRX에너지화학',
        'KRX철강',
        '단기과열',
        'KRX미디어통신',
        'KRX건설',
        'Non1',
        'KRX증권',
        'KRX선박',
        'KRX섹터_보험',
        'KRX섹터_운송',
        'SRI',
        '기준가',
        '매매수량단위',
        '시간외수량단위',
        '거래정지',
        '정리매매',
        '관리종목',
        '시장경고',
        '경고예고',
        '불성실공시',
        '우회상장',
        '락구분',
        '액면변경',
        '증자구분',
        '증거금비율',
        '신용가능',
        '신용기간',
        '전일거래량',
        '액면가',
        '상장일자',
        '상장주수',
        '자본금',
        '결산월',
        '공모가',
        '우선주',
        '공매도과열',
        '이상급등',
        'KRX300',
        'KOSPI',
        '매출액',
        '영업이익',
        '경상이익',
        '당기순이익',
        'ROE',
        '기준년월',
        '시가총액',
        '그룹사코드',
        '회사신용한도초과',
        '담보대출가능',
        '대주가능',
    ]
    KST = timezone(timedelta(hours=9))

    def __init__(
        self,
        app_key: str | None,
        app_secret: str | None,
        base_url: str,
        timeout_sec: float = 10.0,
        request_interval_ms: int = 80,
        universe_limit: int = 120,
        universe_cache_hours: int = 24,
    ) -> None:
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url.rstrip('/')
        self.timeout_sec = timeout_sec
        self.request_interval_ms = max(request_interval_ms, 0)
        self.universe_limit = universe_limit
        self.universe_cache_hours = max(universe_cache_hours, 1)

        self._client = httpx.Client(timeout=self.timeout_sec)
        self._token_lock = threading.Lock()
        self._access_token: str | None = None
        self._access_token_expires_at: datetime | None = None

        self._request_lock = threading.Lock()
        self._last_request_monotonic = 0.0

        self._universe_lock = threading.Lock()
        self._universe_cache: list[StockMeta] | None = None
        self._universe_cached_at: datetime | None = None

    def _ensure_credentials(self) -> None:
        if not self.app_key or not self.app_secret:
            raise AppError(
                code='kis_credentials_missing',
                message='KIS provider requires API credentials',
                status_code=500,
            )

    def _respect_rate_limit(self) -> None:
        if self.request_interval_ms <= 0:
            return
        interval_sec = self.request_interval_ms / 1000.0
        with self._request_lock:
            now = time.monotonic()
            wait = interval_sec - (now - self._last_request_monotonic)
            if wait > 0:
                time.sleep(wait)
            self._last_request_monotonic = time.monotonic()

    def _parse_token_expiry(self, raw: str | None) -> datetime:
        if not raw:
            return utcnow() + timedelta(hours=23)
        try:
            parsed = datetime.strptime(raw, '%Y-%m-%d %H:%M:%S')
            return parsed.replace(tzinfo=self.KST).astimezone(timezone.utc)
        except ValueError:
            logger.warning('KIS token expiry parse failed, fallback 23h window: %s', raw)
            return utcnow() + timedelta(hours=23)

    def _issue_access_token(self) -> str:
        self._ensure_credentials()
        self._respect_rate_limit()
        try:
            response = self._client.post(
                f'{self.base_url}{self.TOKEN_ENDPOINT}',
                json={
                    'grant_type': 'client_credentials',
                    'appkey': self.app_key,
                    'appsecret': self.app_secret,
                },
                headers={
                    'content-type': 'application/json; charset=UTF-8',
                    'accept': 'application/json',
                    'user-agent': 'kospi-scanner/1.0',
                },
            )
        except httpx.HTTPError as exc:
            raise AppError(
                code='kis_http_error',
                message='Failed to request KIS access token',
                status_code=502,
                details={'reason': str(exc)},
            ) from exc

        if response.status_code >= 400:
            raise AppError(
                code='kis_token_http_error',
                message='KIS token request failed',
                status_code=502,
                details={'status_code': response.status_code, 'body': response.text[:400]},
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise AppError(
                code='kis_token_invalid_json',
                message='Invalid KIS token response payload',
                status_code=502,
            ) from exc

        if payload.get('rt_cd') not in (None, '0'):
            raise AppError(
                code='kis_token_api_error',
                message=payload.get('msg1') or 'KIS token API returned an error',
                status_code=502,
                details={'msg_cd': payload.get('msg_cd'), 'rt_cd': payload.get('rt_cd')},
            )

        token = payload.get('access_token')
        if not token:
            raise AppError(
                code='kis_token_missing',
                message='KIS token response did not include access_token',
                status_code=502,
            )

        self._access_token = token
        self._access_token_expires_at = self._parse_token_expiry(payload.get('access_token_token_expired'))
        return token

    def _get_access_token(self, force_refresh: bool = False) -> str:
        with self._token_lock:
            now = utcnow()
            if (
                not force_refresh
                and self._access_token
                and self._access_token_expires_at
                and self._access_token_expires_at - timedelta(minutes=5) > now
            ):
                return self._access_token
            return self._issue_access_token()

    def _request_json(
        self,
        method: str,
        path: str,
        tr_id: str,
        params: dict[str, str] | None = None,
        retry_on_unauthorized: bool = True,
    ) -> dict:
        self._ensure_credentials()
        self._respect_rate_limit()
        token = self._get_access_token()
        headers = {
            'authorization': f'Bearer {token}',
            'appkey': self.app_key or '',
            'appsecret': self.app_secret or '',
            'tr_id': tr_id,
            'tr_cont': '',
            'custtype': 'P',
            'content-type': 'application/json; charset=UTF-8',
            'accept': 'application/json',
        }

        try:
            response = self._client.request(
                method=method,
                url=f'{self.base_url}{path}',
                headers=headers,
                params=params or {},
            )
        except httpx.HTTPError as exc:
            raise AppError(
                code='kis_http_error',
                message='KIS request failed',
                status_code=502,
                details={'path': path, 'reason': str(exc)},
            ) from exc

        if response.status_code == 401 and retry_on_unauthorized:
            self._get_access_token(force_refresh=True)
            return self._request_json(method, path, tr_id, params, retry_on_unauthorized=False)

        if response.status_code >= 400:
            raise AppError(
                code='kis_http_status_error',
                message='KIS request returned HTTP error',
                status_code=502,
                details={
                    'path': path,
                    'status_code': response.status_code,
                    'body': response.text[:400],
                },
            )

        try:
            payload: dict = response.json()
        except ValueError as exc:
            raise AppError(
                code='kis_invalid_json',
                message='KIS response is not valid JSON',
                status_code=502,
                details={'path': path},
            ) from exc

        if payload.get('rt_cd') not in (None, '0'):
            raise AppError(
                code='kis_api_error',
                message=payload.get('msg1') or 'KIS API returned an error',
                status_code=502,
                details={
                    'path': path,
                    'msg_cd': payload.get('msg_cd'),
                    'rt_cd': payload.get('rt_cd'),
                },
            )
        return payload

    @staticmethod
    def _to_int(value: str | int | float | None) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        text = str(value).strip()
        if text == '':
            return 0
        normalized = re.sub(r'[^0-9\-]', '', text)
        if normalized in {'', '-'}:
            return 0
        try:
            return int(normalized)
        except ValueError:
            return 0

    @staticmethod
    def _to_float(value: str | int | float | None) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if text == '':
            return 0.0
        normalized = re.sub(r'[^0-9.\-]', '', text)
        if normalized in {'', '-', '.', '-.'}:
            return 0.0
        try:
            return float(normalized)
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_trade_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y%m%d').date()
        except ValueError:
            return None

    @classmethod
    def _split_fixed_width_bytes(cls, raw: bytes) -> dict[str, str]:
        values: list[str] = []
        cursor = 0
        for width in cls.FIXED_FIELD_WIDTHS:
            values.append(raw[cursor : cursor + width].decode('cp949', errors='ignore').strip())
            cursor += width
        return dict(zip(cls.FIXED_FIELD_COLUMNS, values, strict=False))

    def _master_market_cap_to_won(self, raw: str, listed_shares_raw: str, base_price_raw: str) -> int:
        market_cap = self._to_int(raw)
        if market_cap > 0 and market_cap < 1_000_000_000:
            market_cap *= 1_000_000
        if market_cap > 0:
            return market_cap
        listed_shares = self._to_int(listed_shares_raw)
        base_price = self._to_int(base_price_raw)
        if listed_shares > 0 and base_price > 0:
            return listed_shares * base_price
        return 0

    def _download_kospi_universe(self) -> list[StockMeta]:
        self._ensure_credentials()
        self._respect_rate_limit()
        try:
            response = self._client.get(self.KOSPI_MASTER_ZIP_URL)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AppError(
                code='kis_universe_download_failed',
                message='Failed to download KOSPI master file',
                status_code=502,
                details={'reason': str(exc)},
            ) from exc

        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                with zf.open('kospi_code.mst') as fp:
                    raw_content = fp.read()
        except Exception as exc:
            raise AppError(
                code='kis_universe_parse_failed',
                message='Failed to read KOSPI master file content',
                status_code=502,
                details={'reason': str(exc)},
            ) from exc

        strict_stocks: list[StockMeta] = []
        relaxed_stocks: list[StockMeta] = []

        stocks: list[StockMeta] = []
        for raw_line in raw_content.splitlines():
            line = raw_line.rstrip(b'\r\n')
            if len(line) < 228:
                continue
            part1 = line[:-228]
            part2 = line[-228:]

            code = part1[:9].decode('cp949', errors='ignore').strip()
            if not code.isdigit() or len(code) != 6:
                continue
            name = part1[21:].decode('cp949', errors='ignore').strip()
            if not name:
                continue

            meta = self._split_fixed_width_bytes(part2)
            market_cap = self._master_market_cap_to_won(
                meta.get('시가총액', ''),
                meta.get('상장주수', ''),
                meta.get('기준가', ''),
            )
            candidate = StockMeta(code=code, name=name, market='KOSPI', market_cap=market_cap)
            relaxed_stocks.append(candidate)

            if meta.get('KOSPI') not in {'Y', '1'}:
                continue
            if meta.get('ETP') == 'Y' or meta.get('ELW발행') == 'Y' or meta.get('SPAC') == 'Y':
                continue
            if meta.get('거래정지') == 'Y' or meta.get('정리매매') == 'Y' or meta.get('관리종목') == 'Y':
                continue
            strict_stocks.append(candidate)

        if strict_stocks:
            stocks = strict_stocks
        else:
            logger.warning(
                'KIS strict universe filter returned zero stocks. Falling back to relaxed KOSPI master list.'
            )
            stocks = relaxed_stocks

        stocks.sort(key=lambda item: item.market_cap, reverse=True)
        if self.universe_limit > 0:
            return stocks[: self.universe_limit]
        return stocks

    def list_stocks(self, market: str) -> list[StockMeta]:
        if market.upper() != 'KOSPI':
            return []

        now = utcnow()
        with self._universe_lock:
            if self._universe_cache and self._universe_cached_at:
                age = now - self._universe_cached_at
                if age < timedelta(hours=self.universe_cache_hours):
                    return list(self._universe_cache)

            stocks = self._download_kospi_universe()
            if not stocks:
                raise AppError(
                    code='kis_universe_empty',
                    message='KOSPI universe is empty from KIS master file',
                    status_code=502,
                )
            self._universe_cache = stocks
            self._universe_cached_at = now
            return list(stocks)

    def _daily_bar_params(self, stock_code: str, start_date: date, end_date: date) -> dict[str, str]:
        return {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': start_date.strftime('%Y%m%d'),
            'FID_INPUT_DATE_2': end_date.strftime('%Y%m%d'),
            'FID_PERIOD_DIV_CODE': 'D',
            'FID_ORG_ADJ_PRC': '1',
        }

    def get_daily_bars(self, stock_code: str, days: int) -> list[DailyBar]:
        target_days = max(days, 1)
        daily_map: dict[date, DailyBar] = {}

        cursor_end = datetime.now(self.KST).date()
        attempts = 0
        while len(daily_map) < target_days and attempts < 8:
            cursor_start = cursor_end - timedelta(days=220)
            payload = self._request_json(
                method='GET',
                path=self.DAILY_ENDPOINT,
                tr_id='FHKST03010100',
                params=self._daily_bar_params(stock_code, cursor_start, cursor_end),
            )
            rows = payload.get('output2') or []
            if not isinstance(rows, list) or not rows:
                break

            oldest_date: date | None = None
            parsed_rows = 0
            for row in rows:
                trade_date = self._parse_trade_date(row.get('stck_bsop_date'))
                if not trade_date:
                    continue
                bar = DailyBar(
                    trade_date=trade_date,
                    open_price=self._to_float(row.get('stck_oprc')),
                    high_price=self._to_float(row.get('stck_hgpr')),
                    low_price=self._to_float(row.get('stck_lwpr')),
                    close_price=self._to_float(row.get('stck_clpr')),
                    volume=self._to_int(row.get('acml_vol')),
                    trading_value=self._to_int(row.get('acml_tr_pbmn')),
                )
                daily_map[trade_date] = bar
                parsed_rows += 1
                if oldest_date is None or trade_date < oldest_date:
                    oldest_date = trade_date

            if parsed_rows == 0 or oldest_date is None:
                break
            if len(rows) < 90:
                break

            next_end = oldest_date - timedelta(days=1)
            if next_end >= cursor_end:
                break
            cursor_end = next_end
            attempts += 1

        bars = [daily_map[day] for day in sorted(daily_map.keys())]
        if not bars:
            raise AppError(
                code='kis_daily_bars_empty',
                message='No daily bars from KIS',
                status_code=502,
                details={'stock_code': stock_code},
            )
        return bars[-target_days:]

    def get_latest_quote(self, stock_code: str) -> Quote:
        payload = self._request_json(
            method='GET',
            path=self.QUOTE_ENDPOINT,
            tr_id='FHKST01010100',
            params={
                'FID_COND_MRKT_DIV_CODE': 'J',
                'FID_INPUT_ISCD': stock_code,
            },
        )
        output = payload.get('output') or payload.get('output1') or {}
        if isinstance(output, list):
            output = output[0] if output else {}

        price = self._to_float(output.get('stck_prpr'))
        trading_value = self._to_int(output.get('acml_tr_pbmn'))

        if price <= 0:
            latest_bar = self.get_daily_bars(stock_code, 1)[-1]
            price = latest_bar.close_price
            trading_value = latest_bar.trading_value

        return Quote(code=stock_code, price=price, trading_value=trading_value)

    @staticmethod
    def _extract_money_value(raw: str | int | float | None) -> int | None:
        if raw is None:
            return None
        text = str(raw).strip()
        if text == '':
            return None
        normalized = re.sub(r'[^0-9\-]', '', text)
        if normalized in {'', '-'}:
            return None
        try:
            return int(normalized)
        except ValueError:
            return None

    def get_foreign_investor_intraday_snapshot(self, stock_code: str) -> ForeignInvestorIntradaySnapshot:
        try:
            payload = self._request_json(
                method='GET',
                path=self.INVESTOR_ENDPOINT,
                tr_id='FHKST01010900',
                params={
                    'FID_COND_MRKT_DIV_CODE': 'J',
                    'FID_INPUT_ISCD': stock_code,
                },
            )
        except AppError as exc:
            logger.warning('KIS intraday investor snapshot failed for %s: %s', stock_code, exc.message)
            return ForeignInvestorIntradaySnapshot(
                stock_code,
                as_of=utcnow(),
                net_buy_value=None,
                source='kis_intraday_snapshot_unavailable',
                is_confirmed=False,
            )

        output = payload.get('output') or {}
        if isinstance(output, list):
            output = output[0] if output else {}

        return ForeignInvestorIntradaySnapshot(
            stock_code=stock_code,
            as_of=utcnow(),
            net_buy_value=self._extract_money_value(output.get('frgn_ntby_tr_pbmn')),
            source='kis_investor_intraday_snapshot',
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

        try:
            payload = self._request_json(
                method='GET',
                path=self.INVESTOR_DAILY_ENDPOINT,
                tr_id='FHPTJ04160001',
                params={
                    'FID_COND_MRKT_DIV_CODE': 'J',
                    'FID_INPUT_ISCD': stock_code,
                    'FID_INPUT_DATE_1': end_date.strftime('%Y%m%d'),
                    'FID_ORG_ADJ_PRC': '',
                    'FID_ETC_CLS_CODE': '',
                },
            )
        except AppError as exc:
            logger.warning('KIS daily confirmed investor fetch failed for %s: %s', stock_code, exc.message)
            return []

        rows = payload.get('output2') or []
        if not isinstance(rows, list) or not rows:
            return []

        dedup: dict[date, ForeignInvestorDailyConfirmed] = {}
        for row in rows:
            trade_date = self._parse_trade_date(row.get('stck_bsop_date'))
            if not trade_date:
                continue
            if trade_date < start_date or trade_date > end_date:
                continue
            dedup[trade_date] = ForeignInvestorDailyConfirmed(
                stock_code=stock_code,
                trade_date=trade_date,
                net_buy_value=self._extract_money_value(row.get('frgn_ntby_tr_pbmn')),
                source='kis_investor_daily_confirmed',
                is_confirmed=True,
            )
        return [dedup[key] for key in sorted(dedup.keys())]

    def get_foreign_net_buy_aggregate(self, stock_code: str, days: int) -> int:
        target_days = max(days, 1)
        end_date = datetime.now(self.KST).date()
        start_date = end_date - timedelta(days=target_days * 4)
        rows = self.get_foreign_investor_daily_confirmed(stock_code, start_date, end_date)
        ordered_values: list[int] = []
        for item in sorted(rows, key=lambda row: row.trade_date, reverse=True):
            if item.net_buy_value is None:
                continue
            ordered_values.append(int(item.net_buy_value))
            if len(ordered_values) >= target_days:
                break

        return int(sum(ordered_values))
