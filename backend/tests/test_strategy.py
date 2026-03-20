from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.services.strategy_service import (
    create_strategy,
    delete_strategy,
    duplicate_strategy,
    get_strategy_or_404,
    list_strategies,
    update_strategy,
)
from app.services.auth_service import signup_user



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
        ),
    )

    fetched = get_strategy_or_404(db_session, user, created.id)
    assert fetched.name == '기본 전략'

    updated = update_strategy(db_session, fetched, StrategyUpdate(name='수정 전략', rsi_max=45))
    assert updated.name == '수정 전략'
    assert updated.rsi_max == 45

    copied = duplicate_strategy(db_session, user, updated)
    assert '(복제)' in copied.name

    all_items = list_strategies(db_session, user)
    assert len(all_items) == initial_count + 2

    delete_strategy(db_session, updated)
    all_items = list_strategies(db_session, user)
    assert len(all_items) == initial_count + 1
