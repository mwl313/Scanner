from sqlalchemy import select

from app.models.scan_result import ScanResult
from app.models.strategy import Strategy
from app.services.auth_service import signup_user
from app.services import scan_service
from app.services.scan_service import run_scan



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
    assert len(results) == run.total_scanned
    assert any(item.score >= 40 for item in results)


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
    assert len(results) == run.total_scanned
    assert any('외인 확정 데이터 없음(중립 처리)' in (item.matched_reasons_json or []) for item in results)
    assert all(item.foreign_data_status == 'unavailable' for item in results)
