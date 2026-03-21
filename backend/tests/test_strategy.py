import pytest

from app.core.scan_policy import DEFAULT_SCAN_UNIVERSE_LIMIT
from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.services.auth_service import signup_user
from app.services.strategy_service import (
    create_strategy,
    delete_strategy,
    duplicate_strategy,
    get_strategy_or_404,
    list_strategies,
    update_strategy,
)


def test_strategy_schema_scan_universe_limit_default_and_validation():
    payload = StrategyCreate(name='기본값 확인')
    assert payload.scan_universe_limit == DEFAULT_SCAN_UNIVERSE_LIMIT

    with pytest.raises(ValueError):
        StrategyCreate(name='잘못된 범위', scan_universe_limit=150)


def test_strategy_crud_cycle(db_session):
    user = signup_user(db_session, 'strategy@example.com', 'password123', 'password123')
    initial_items = list_strategies(db_session, user)
    initial_count = len(initial_items)

    created = create_strategy(
        db_session,
        user,
        StrategyCreate(
            name='기본 전략',
            description='desc',
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
            scan_universe_limit=500,
        ),
    )

    fetched = get_strategy_or_404(db_session, user, created.id)
    assert fetched.name == '기본 전략'
    assert fetched.scan_universe_limit == 500

    updated = update_strategy(db_session, fetched, StrategyUpdate(name='수정 전략', rsi_max=45, scan_universe_limit=0))
    assert updated.name == '수정 전략'
    assert updated.rsi_max == 45
    assert updated.scan_universe_limit == 0

    copied = duplicate_strategy(db_session, user, updated)
    assert '(복제)' in copied.name
    assert copied.scan_universe_limit == 0

    all_items = list_strategies(db_session, user)
    assert len(all_items) == initial_count + 2

    delete_strategy(db_session, updated)
    all_items = list_strategies(db_session, user)
    assert len(all_items) == initial_count + 1
