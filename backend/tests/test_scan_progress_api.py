from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import create_app
from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.services.auth_service import signup_user
from app.utils.datetime_utils import utcnow


@contextmanager
def _api_client(db_session, user):
    app = create_app()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def _create_strategy(db_session, user) -> Strategy:
    strategy = Strategy(
        user_id=user.id,
        name='progress-test',
        description='progress-test',
        is_active=True,
        market='KOSPI',
        min_market_cap=1,
        min_trading_value=1,
        rsi_period=14,
        rsi_signal_period=9,
        rsi_min=30,
        rsi_max=45,
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


def _create_run(
    db_session,
    strategy: Strategy,
    *,
    status: str,
    total_scanned: int,
    total_target: int,
) -> ScanRun:
    run = ScanRun(
        strategy_id=strategy.id,
        run_type='manual',
        started_at=utcnow(),
        finished_at=(None if status == 'running' else utcnow()),
        status=status,
        total_scanned=total_scanned,
        total_target=total_target,
        total_matched=max(total_scanned - 1, 0),
        failed_count=1 if total_scanned > 0 else 0,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_scans_endpoint_excludes_running_runs_by_default(db_session):
    user = signup_user(db_session, 'progress-api-a@example.com', 'password123', 'password123')
    strategy = _create_strategy(db_session, user)
    completed = _create_run(db_session, strategy, status='completed', total_scanned=120, total_target=120)
    _ = _create_run(db_session, strategy, status='running', total_scanned=30, total_target=300)

    with _api_client(db_session, user) as client:
        response = client.get('/api/scans')
        assert response.status_code == 200
        payload = response.json()
        assert payload
        assert all(item['status'] != 'running' for item in payload)
        assert any(item['id'] == completed.id for item in payload)

        include_running = client.get('/api/scans?include_running=true')
        assert include_running.status_code == 200
        include_payload = include_running.json()
        assert any(item['status'] == 'running' for item in include_payload)


def test_scan_progress_endpoint_returns_running_progress(db_session):
    user = signup_user(db_session, 'progress-api-b@example.com', 'password123', 'password123')
    strategy = _create_strategy(db_session, user)
    running = _create_run(db_session, strategy, status='running', total_scanned=30, total_target=120)

    with _api_client(db_session, user) as client:
        response = client.get('/api/scans/progress')
        assert response.status_code == 200
        payload = response.json()

    assert payload is not None
    assert payload['run_id'] == running.id
    assert payload['strategy_id'] == strategy.id
    assert payload['total_scanned'] == 30
    assert payload['total_target'] == 120
    assert payload['progress_pct'] == 25.0
    assert payload['status'] == 'running'


def test_running_progress_disappears_after_completion_and_completed_list_includes_run(db_session):
    user = signup_user(db_session, 'progress-api-c@example.com', 'password123', 'password123')
    strategy = _create_strategy(db_session, user)
    run = _create_run(db_session, strategy, status='running', total_scanned=90, total_target=120)

    with _api_client(db_session, user) as client:
        running_response = client.get('/api/scans/progress')
        assert running_response.status_code == 200
        assert running_response.json()['run_id'] == run.id

    run.status = 'completed'
    run.finished_at = utcnow()
    run.total_scanned = run.total_target
    db_session.add(run)
    db_session.commit()

    with _api_client(db_session, user) as client:
        progress_response = client.get('/api/scans/progress')
        assert progress_response.status_code == 200
        assert progress_response.json() is None

        scans_response = client.get('/api/scans')
        assert scans_response.status_code == 200
        scans_payload = scans_response.json()
        assert any(item['id'] == run.id for item in scans_payload)
        assert all(item['status'] != 'running' for item in scans_payload)
