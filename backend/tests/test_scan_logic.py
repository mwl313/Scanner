from sqlalchemy import select

from app.models.scan_result import ScanResult
from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.services.auth_service import signup_user
from app.services import scan_service
from app.providers.base import StockMeta
from app.services.scan_service import (
    ScanExecutionOptions,
    delete_scan_run,
    resolve_strategy_scan_execution_options,
    run_scan,
    run_scan_with_metrics,
    run_scheduled_scans,
)
from app.schemas.strategy import StrategyConfig



def test_scan_engine_runs_and_scores(db_session):
    user = signup_user(db_session, 'scan@example.com', 'password123', 'password123')
    strategy = Strategy(
        user_id=user.id,
        name='scan',
        description='scan',
        is_active=True,
        market='KOSPI',
        min_market_cap=3000000000000,
        min_trading_value=10000000000,
        rsi_period=14,
        rsi_signal_period=9,
        rsi_min=25,
        rsi_max=55,
        bb_period=20,
        bb_std=2,
        use_ma5_filter=True,
        use_ma20_filter=True,
        foreign_net_buy_days=3,
        scan_interval_type='eod',
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    run = run_scan(db_session, strategy, 'manual')

    assert run.total_scanned > 0
    assert run.status in {'completed', 'partial_failed'}

    results = db_session.scalars(select(ScanResult).where(ScanResult.scan_run_id == run.id)).all()
    assert len(results) + run.failed_count == run.total_scanned
    assert any(item.score >= 40 for item in results)
    assert all(0 <= item.score <= 100 for item in results)


def test_scan_engine_uses_neutral_when_confirmed_foreign_missing(db_session, monkeypatch):
    user = signup_user(db_session, 'scan2@example.com', 'password123', 'password123')
    strategy = Strategy(
        user_id=user.id,
        name='scan2',
        description='scan2',
        is_active=True,
        market='KOSPI',
        min_market_cap=1,
        min_trading_value=1,
        rsi_period=14,
        rsi_signal_period=9,
        rsi_min=25,
        rsi_max=55,
        bb_period=20,
        bb_std=2,
        use_ma5_filter=True,
        use_ma20_filter=True,
        foreign_net_buy_days=3,
        scan_interval_type='eod',
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    monkeypatch.setattr(
        scan_service,
        'get_foreign_investor_context',
        lambda db, provider, stock_code, days: {
            'confirmed_aggregate_value': None,
            'snapshot_value': 99999999,
            'status': 'unavailable',
            'source': 'confirmed_daily_unavailable',
            'snapshot_source': 'mock_snapshot',
        },
    )

    run = run_scan(db_session, strategy, 'manual')
    results = db_session.scalars(select(ScanResult).where(ScanResult.scan_run_id == run.id)).all()

    assert run.total_scanned > 0
    assert len(results) + run.failed_count == run.total_scanned
    assert any('외인 확정 데이터 없음(중립 처리)' in (item.matched_reasons_json or []) for item in results)
    assert all(item.foreign_data_status == 'unavailable' for item in results)


def test_scan_engine_excludes_when_mandatory_trading_value_fails(db_session):
    user = signup_user(db_session, 'scan3@example.com', 'password123', 'password123')
    config = StrategyConfig().model_dump()
    config['categories']['trading_value']['min_trading_value'] = 10**15
    config['categories']['trading_value']['mandatory'] = True

    strategy = Strategy(
        user_id=user.id,
        name='scan3',
        description='scan3',
        is_active=True,
        market='KOSPI',
        min_market_cap=3000000000000,
        min_trading_value=10000000000,
        rsi_period=14,
        rsi_signal_period=9,
        rsi_min=30,
        rsi_max=40,
        bb_period=20,
        bb_std=2,
        use_ma5_filter=True,
        use_ma20_filter=True,
        foreign_net_buy_days=3,
        scan_interval_type='eod',
        strategy_config=config,
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    run = run_scan(db_session, strategy, 'manual')
    results = db_session.scalars(select(ScanResult).where(ScanResult.scan_run_id == run.id)).all()

    assert run.total_scanned > 0
    assert len(results) + run.failed_count == run.total_scanned
    assert all(item.grade == 'EXCLUDED' for item in results)


def test_delete_scan_run_removes_run_and_results(db_session):
    user = signup_user(db_session, 'scan-delete@example.com', 'password123', 'password123')
    strategy = Strategy(
        user_id=user.id,
        name='scan-delete',
        description='scan-delete',
        is_active=True,
        market='KOSPI',
        min_market_cap=3000000000000,
        min_trading_value=10000000000,
        rsi_period=14,
        rsi_signal_period=9,
        rsi_min=30,
        rsi_max=40,
        bb_period=20,
        bb_std=2,
        use_ma5_filter=True,
        use_ma20_filter=True,
        foreign_net_buy_days=3,
        scan_interval_type='eod',
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    run = run_scan(db_session, strategy, 'manual')
    assert db_session.scalar(select(ScanRun).where(ScanRun.id == run.id)) is not None
    assert db_session.scalars(select(ScanResult).where(ScanResult.scan_run_id == run.id)).all()

    delete_scan_run(db_session, user, run.id)

    assert db_session.scalar(select(ScanRun).where(ScanRun.id == run.id)) is None
    assert db_session.scalars(select(ScanResult).where(ScanResult.scan_run_id == run.id)).all() == []


def test_run_scan_with_pre_screen_filters_universe(db_session, monkeypatch):
    user = signup_user(db_session, 'scan-prescreen@example.com', 'password123', 'password123')
    strategy = Strategy(
        user_id=user.id,
        name='scan-prescreen',
        description='scan-prescreen',
        is_active=True,
        market='KOSPI',
        min_market_cap=3000000000000,
        min_trading_value=10000000000,
        rsi_period=14,
        rsi_signal_period=9,
        rsi_min=30,
        rsi_max=40,
        bb_period=20,
        bb_std=2,
        use_ma5_filter=True,
        use_ma20_filter=True,
        foreign_net_buy_days=3,
        scan_interval_type='eod',
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    class TinyProvider:
        def list_stocks(self, market):
            assert market == 'KOSPI'
            return [
                StockMeta(code='111111', name='A', market='KOSPI', market_cap=4_000_000_000_000),
                StockMeta(code='222222', name='B', market='KOSPI', market_cap=2_500_000_000_000),
                StockMeta(code='333333', name='C', market='KOSPI', market_cap=1_000_000_000_000),
            ]

        def get_daily_bars(self, stock_code, days):
            _ = stock_code, days
            return []

    monkeypatch.setattr(
        scan_service,
        'get_foreign_investor_context',
        lambda db, provider, stock_code, days: {
            'confirmed_aggregate_value': 1,
            'snapshot_value': 1,
            'status': 'confirmed',
            'source': 'test',
            'snapshot_source': 'test',
        },
    )
    monkeypatch.setattr(
        scan_service,
        '_evaluate_stock',
        lambda strategy, strategy_config, stock, bars, foreign_data: {
            'stock_code': stock.code,
            'stock_name': stock.name,
            'market': stock.market,
            'price': 10000,
            'ma5': 10000,
            'ma20': 10000,
            'ma60': 10000,
            'bb_upper': 10200,
            'bb_mid': 10000,
            'bb_lower': 9800,
            'rsi': 35,
            'rsi_signal': 33,
            'foreign_net_buy_value': 100,
            'foreign_net_buy_confirmed_value': 100,
            'foreign_net_buy_snapshot_value': 100,
            'foreign_data_status': 'confirmed',
            'foreign_data_source': 'test',
            'trading_value': 10_000_000_000,
            'score': 85,
            'grade': 'A',
            'matched_reasons_json': ['테스트'],
            'failed_reasons_json': [],
        },
    )

    outcome = run_scan_with_metrics(
        db_session,
        strategy,
        run_type='benchmark',
        provider=TinyProvider(),
        execution_options=ScanExecutionOptions(
            universe_limit=2,
            pre_screen_enabled=True,
            pre_screen_min_market_cap=3_000_000_000_000,
        ),
    )

    assert outcome.metrics.original_universe_count == 3
    assert outcome.metrics.limited_universe_count == 2
    assert outcome.metrics.pre_screen_universe_count == 1
    assert outcome.run.total_scanned == 1


def test_run_scan_uses_strategy_scan_universe_policy_when_options_missing(db_session, monkeypatch):
    user = signup_user(db_session, 'scan-auto-policy@example.com', 'password123', 'password123')
    strategy = Strategy(
        user_id=user.id,
        name='scan-auto-policy',
        description='scan-auto-policy',
        is_active=True,
        market='KOSPI',
        scan_universe_limit=500,
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    class TinyProvider:
        def list_stocks(self, market):
            assert market == 'KOSPI'
            return [
                StockMeta(code='111111', name='A', market='KOSPI', market_cap=4_000_000_000_000),
                StockMeta(code='222222', name='B', market='KOSPI', market_cap=2_500_000_000_000),
                StockMeta(code='333333', name='C', market='KOSPI', market_cap=1_000_000_000_000),
            ]

        def get_daily_bars(self, stock_code, days):
            _ = stock_code, days
            return []

    monkeypatch.setattr(
        scan_service,
        'get_foreign_investor_context',
        lambda db, provider, stock_code, days: {
            'confirmed_aggregate_value': 1,
            'snapshot_value': 1,
            'status': 'confirmed',
            'source': 'test',
            'snapshot_source': 'test',
        },
    )
    monkeypatch.setattr(
        scan_service,
        '_evaluate_stock',
        lambda strategy, strategy_config, stock, bars, foreign_data: {
            'stock_code': stock.code,
            'stock_name': stock.name,
            'market': stock.market,
            'price': 10000,
            'ma5': 10000,
            'ma20': 10000,
            'ma60': 10000,
            'bb_upper': 10200,
            'bb_mid': 10000,
            'bb_lower': 9800,
            'rsi': 35,
            'rsi_signal': 33,
            'foreign_net_buy_value': 100,
            'foreign_net_buy_confirmed_value': 100,
            'foreign_net_buy_snapshot_value': 100,
            'foreign_data_status': 'confirmed',
            'foreign_data_source': 'test',
            'trading_value': 10_000_000_000,
            'score': 85,
            'grade': 'A',
            'matched_reasons_json': ['테스트'],
            'failed_reasons_json': [],
        },
    )

    outcome = run_scan_with_metrics(
        db_session,
        strategy,
        run_type='manual',
        provider=TinyProvider(),
    )

    assert outcome.metrics.universe_limit == 500
    assert outcome.metrics.pre_screen_enabled is True
    assert outcome.metrics.original_universe_count == 3
    assert outcome.metrics.pre_screen_universe_count == 1
    assert outcome.run.total_scanned == 1


def test_scheduled_scan_path_uses_same_strategy_scan_policy(db_session, monkeypatch):
    user = signup_user(db_session, 'scan-scheduled-policy@example.com', 'password123', 'password123')
    strategy_300 = Strategy(
        user_id=user.id,
        name='scan-scheduled-300',
        description='scan-scheduled-300',
        is_active=True,
        market='KOSPI',
        scan_interval_type='eod',
        scan_universe_limit=300,
    )
    strategy_500 = Strategy(
        user_id=user.id,
        name='scan-scheduled-500',
        description='scan-scheduled-500',
        is_active=True,
        market='KOSPI',
        scan_interval_type='eod',
        scan_universe_limit=500,
    )
    db_session.add_all([strategy_300, strategy_500])
    db_session.commit()
    db_session.refresh(strategy_300)
    db_session.refresh(strategy_500)

    captured: dict[int, ScanExecutionOptions] = {}

    monkeypatch.setattr(scan_service, 'sync_confirmed_foreign_for_market', lambda db, market, lookback_days: (0, 0))

    def fake_run_scan(db, strategy, run_type='manual', *, execution_options=None, provider=None):
        _ = db, provider
        assert run_type == 'scheduled'
        assert execution_options is not None
        captured[strategy.id] = execution_options
        return None

    monkeypatch.setattr(scan_service, 'run_scan', fake_run_scan)

    run_scheduled_scans(db_session)

    assert captured[strategy_300.id].universe_limit == 300
    assert captured[strategy_300.id].pre_screen_enabled is False
    assert captured[strategy_500.id].universe_limit == 500
    assert captured[strategy_500.id].pre_screen_enabled is True


def test_resolve_strategy_scan_execution_options_mapping(db_session):
    user = signup_user(db_session, 'scan-resolver@example.com', 'password123', 'password123')
    expectations = [
        (120, False),
        (200, False),
        (300, False),
        (500, True),
        (0, True),
    ]

    for universe_limit, expected_pre_screen in expectations:
        strategy = Strategy(
            user_id=user.id,
            name=f'scan-resolver-{universe_limit}',
            description='scan-resolver',
            is_active=True,
            market='KOSPI',
            scan_universe_limit=universe_limit,
        )
        db_session.add(strategy)
        db_session.flush()

        options = resolve_strategy_scan_execution_options(strategy)
        assert options.universe_limit == universe_limit
        assert options.pre_screen_enabled is expected_pre_screen
