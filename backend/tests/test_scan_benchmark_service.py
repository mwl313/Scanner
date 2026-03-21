import pytest
from sqlalchemy import func, select

from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.services.auth_service import signup_user
from app.services.scan_benchmark_service import (
    measure_elapsed_call,
    report_samples_to_csv_rows,
    report_to_markdown,
    run_scan_benchmark,
)


def _create_strategy(db_session, user_id: int, name: str) -> Strategy:
    strategy = Strategy(
        user_id=user_id,
        name=name,
        description=name,
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
    return strategy


def test_benchmark_full_universe_requires_explicit_allow(db_session):
    user = signup_user(db_session, 'bench-guard@example.com', 'password123', 'password123')
    strategy = _create_strategy(db_session, user.id, 'bench-guard')

    with pytest.raises(ValueError):
        run_scan_benchmark(
            db_session,
            strategy,
            provider_name='mock',
            universe_limits=[0],
            repeats=1,
            pre_screen_modes=[False],
            allow_full_universe=False,
        )


def test_benchmark_generates_samples_and_summary(db_session):
    user = signup_user(db_session, 'bench-report@example.com', 'password123', 'password123')
    strategy = _create_strategy(db_session, user.id, 'bench-report')

    report = run_scan_benchmark(
        db_session,
        strategy,
        provider_name='mock',
        universe_limits=[2],
        repeats=1,
        pre_screen_modes=[False, True],
        pre_screen_min_market_cap=0,
        allow_full_universe=False,
        keep_runs=False,
    )

    assert len(report.samples) == 2
    assert len(report.summaries) == 2
    assert report.provider == 'mock'
    assert report.warmup_universe_count > 0
    assert report.estimated_stock_scans_upper_bound >= 2

    markdown = report_to_markdown(report)
    assert 'Scan Benchmark Report' in markdown
    assert '케이스별 결과 (raw)' in markdown
    assert 'Suspicious Findings' in markdown

    rows = report_samples_to_csv_rows(report)
    assert len(rows) == 2
    assert rows[0]['provider'] == 'mock'
    assert 'total_elapsed_seconds' in rows[0]
    assert 'provider_fetch_elapsed_seconds' in rows[0]

    # pre-screen ON/OFF지만 min_market_cap=0이므로 필터 카운트가 동일하게 기록되어야 함.
    on_sample = next(item for item in report.samples if item.pre_screen_enabled)
    off_sample = next(item for item in report.samples if not item.pre_screen_enabled)
    assert on_sample.filtered_universe_count == off_sample.filtered_universe_count

    benchmark_run_count = db_session.scalar(
        select(func.count(ScanRun.id)).where(ScanRun.run_type == 'benchmark')
    )
    assert benchmark_run_count == 0


def test_measure_elapsed_call_records_elapsed_and_value():
    result = measure_elapsed_call(lambda x, y: x + y, 2, 3)
    assert result.value == 5
    assert result.elapsed_seconds >= 0.0
