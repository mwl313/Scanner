from datetime import date, timedelta

import app.providers.kis_provider as kis_provider_module
from app.core.exceptions import AppError
from app.providers.base import DailyBar, ForeignInvestorDailyConfirmed, StockMeta
from app.providers.kis_provider import KisMarketDataProvider


def make_provider() -> KisMarketDataProvider:
    return KisMarketDataProvider(
        app_key='dummy-key',
        app_secret='dummy-secret',
        base_url='https://openapi.koreainvestment.com:9443',
        request_interval_ms=0,
    )


def test_list_stocks_uses_cache(monkeypatch):
    provider = make_provider()
    calls = {'count': 0}

    def fake_download():
        calls['count'] += 1
        return [StockMeta(code='005930', name='삼성전자', market='KOSPI', market_cap=300000000000000)]

    monkeypatch.setattr(provider, '_download_kospi_universe', fake_download)

    first = provider.list_stocks('KOSPI')
    second = provider.list_stocks('KOSPI')
    other_market = provider.list_stocks('KOSDAQ')

    assert len(first) == 1
    assert len(second) == 1
    assert calls['count'] == 1
    assert other_market == []

    provider._client.close()


def test_get_daily_bars_returns_sorted_recent_rows(monkeypatch):
    provider = make_provider()

    def fake_request_json(method, path, tr_id, params=None, retry_on_unauthorized=True):
        _ = method, path, tr_id, params, retry_on_unauthorized
        return {
            'output2': [
                {
                    'stck_bsop_date': '20260318',
                    'stck_oprc': '10000',
                    'stck_hgpr': '10200',
                    'stck_lwpr': '9900',
                    'stck_clpr': '10100',
                    'acml_vol': '100000',
                    'acml_tr_pbmn': '1010000000',
                },
                {
                    'stck_bsop_date': '20260317',
                    'stck_oprc': '9900',
                    'stck_hgpr': '10100',
                    'stck_lwpr': '9800',
                    'stck_clpr': '10000',
                    'acml_vol': '80000',
                    'acml_tr_pbmn': '800000000',
                },
                {
                    'stck_bsop_date': '20260319',
                    'stck_oprc': '10100',
                    'stck_hgpr': '10300',
                    'stck_lwpr': '10000',
                    'stck_clpr': '10200',
                    'acml_vol': '120000',
                    'acml_tr_pbmn': '1200000000',
                },
            ]
        }

    monkeypatch.setattr(provider, '_request_json', fake_request_json)

    bars = provider.get_daily_bars('005930', 2)

    assert len(bars) == 2
    assert bars[0].trade_date == date(2026, 3, 18)
    assert bars[1].trade_date == date(2026, 3, 19)
    assert bars[1].close_price == 10200

    provider._client.close()


def test_get_daily_bars_uses_latest_korean_trading_date(monkeypatch):
    provider = make_provider()
    requested_end_dates: list[str] = []

    monkeypatch.setattr(kis_provider_module, 'latest_korean_trading_date', lambda now=None: date(2026, 3, 20))

    def fake_request_json(method, path, tr_id, params=None, retry_on_unauthorized=True):
        _ = method, path, tr_id, retry_on_unauthorized
        requested_end_dates.append((params or {}).get('FID_INPUT_DATE_2'))
        return {
            'output2': [
                {
                    'stck_bsop_date': '20260320',
                    'stck_oprc': '10100',
                    'stck_hgpr': '10300',
                    'stck_lwpr': '10000',
                    'stck_clpr': '10200',
                    'acml_vol': '120000',
                    'acml_tr_pbmn': '1200000000',
                }
            ]
        }

    monkeypatch.setattr(provider, '_request_json', fake_request_json)

    bars = provider.get_daily_bars('005930', 1)

    assert requested_end_dates
    assert requested_end_dates[0] == '20260320'
    assert bars[-1].trade_date == date(2026, 3, 20)

    provider._client.close()


def test_get_latest_quote_falls_back_to_daily_bar(monkeypatch):
    provider = make_provider()

    def fake_quote(*_args, **_kwargs):
        return {'output': {'stck_prpr': '0', 'acml_tr_pbmn': '0'}}

    monkeypatch.setattr(provider, '_request_json', fake_quote)
    monkeypatch.setattr(
        provider,
        'get_daily_bars',
        lambda stock_code, days: [
            DailyBar(
                trade_date=date(2026, 3, 19),
                open_price=10000,
                high_price=10300,
                low_price=9900,
                close_price=10200,
                volume=100000,
                trading_value=1200000000,
            )
        ],
    )

    quote = provider.get_latest_quote('005930')

    assert quote.price == 10200
    assert quote.trading_value == 1200000000

    provider._client.close()


def test_get_foreign_net_buy_aggregate_uses_recent_days(monkeypatch):
    provider = make_provider()

    def fake_investor_daily(*_args, **_kwargs):
        return {
            'output2': [
                {'stck_bsop_date': '20260317', 'frgn_ntby_qty': '100'},
                {'stck_bsop_date': '20260319', 'frgn_ntby_qty': '300'},
                {'stck_bsop_date': '20260318', 'frgn_ntby_qty': '-200'},
            ]
        }

    monkeypatch.setattr(provider, '_request_json', fake_investor_daily)

    aggregated = provider.get_foreign_net_buy_aggregate('005930', 2)

    assert aggregated == 100

    provider._client.close()


def test_get_foreign_net_buy_aggregate_uses_latest_trading_date(monkeypatch):
    provider = make_provider()
    captured: dict[str, date] = {}

    monkeypatch.setattr(kis_provider_module, 'latest_korean_trading_date', lambda now=None: date(2026, 3, 20))

    def fake_daily_confirmed(_stock_code, start_date, end_date):
        captured['start_date'] = start_date
        captured['end_date'] = end_date
        return [
            ForeignInvestorDailyConfirmed(
                stock_code='005930',
                trade_date=date(2026, 3, 19),
                net_buy_qty=100,
                source='kis_investor_daily_confirmed',
                is_confirmed=True,
            ),
            ForeignInvestorDailyConfirmed(
                stock_code='005930',
                trade_date=date(2026, 3, 20),
                net_buy_qty=300,
                source='kis_investor_daily_confirmed',
                is_confirmed=True,
            ),
            ForeignInvestorDailyConfirmed(
                stock_code='005930',
                trade_date=date(2026, 3, 18),
                net_buy_qty=-500,
                source='kis_investor_daily_confirmed',
                is_confirmed=True,
            ),
        ]

    monkeypatch.setattr(provider, 'get_foreign_investor_daily_confirmed', fake_daily_confirmed)

    aggregated = provider.get_foreign_net_buy_aggregate('005930', 2)

    assert captured['end_date'] == date(2026, 3, 20)
    assert captured['start_date'] < captured['end_date']
    assert aggregated == 400

    provider._client.close()


def test_intraday_snapshot_uses_quantity(monkeypatch):
    provider = make_provider()

    def fake_snapshot(*_args, **_kwargs):
        return {'output': {'frgn_ntby_tr_pbmn': '', 'frgn_ntby_qty': '99999'}}

    monkeypatch.setattr(provider, '_request_json', fake_snapshot)

    snapshot = provider.get_foreign_investor_intraday_snapshot('005930')

    assert snapshot.net_buy_qty == 99999
    assert snapshot.is_confirmed is False

    provider._client.close()


def test_daily_confirmed_uses_quantity(monkeypatch):
    provider = make_provider()

    def fake_daily(*_args, **_kwargs):
        return {
            'output2': [
                {'stck_bsop_date': '20260319', 'frgn_ntby_tr_pbmn': '', 'frgn_ntby_qty': '12345'},
            ]
        }

    monkeypatch.setattr(provider, '_request_json', fake_daily)

    rows = provider.get_foreign_investor_daily_confirmed('005930', date(2026, 3, 19), date(2026, 3, 19))

    assert len(rows) == 1
    assert rows[0].net_buy_qty == 12345
    assert rows[0].is_confirmed is True

    provider._client.close()


def test_get_access_token_reuses_cached_token(monkeypatch):
    provider = make_provider()
    calls = {'count': 0}

    def fake_issue():
        calls['count'] += 1
        provider._access_token = 'cached-token'
        provider._access_token_expires_at = kis_provider_module.utcnow() + timedelta(hours=1)
        return 'cached-token'

    monkeypatch.setattr(provider, '_issue_access_token', fake_issue)

    first = provider._get_access_token()
    second = provider._get_access_token()

    assert first == 'cached-token'
    assert second == 'cached-token'
    assert calls['count'] == 1

    provider._client.close()


def test_token_rate_limit_uses_cooldown(monkeypatch):
    provider = make_provider()
    calls = {'count': 0}

    class FakeResponse:
        status_code = 403
        text = '{"error_description":"접근토큰 발급 잠시 후 다시 시도하세요(1분당 1회)","error_code":"EGW00133"}'

        @staticmethod
        def json():
            return {'error_description': '접근토큰 발급 잠시 후 다시 시도하세요(1분당 1회)', 'error_code': 'EGW00133'}

    def fake_post(*args, **kwargs):
        _ = args, kwargs
        calls['count'] += 1
        return FakeResponse()

    monkeypatch.setattr(provider._client, 'post', fake_post)

    try:
        provider._issue_access_token()
        raise AssertionError('expected token rate-limited error')
    except AppError as exc:
        assert exc.code == 'kis_token_rate_limited'

    try:
        provider._issue_access_token()
        raise AssertionError('expected token cooldown error')
    except AppError as exc:
        assert exc.code == 'kis_token_cooldown'

    assert calls['count'] == 1
    provider._client.close()
