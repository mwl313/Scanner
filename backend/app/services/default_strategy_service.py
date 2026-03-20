from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.models.user import User


DEFAULT_STRATEGY_FIELDS: dict = {
    'name': 'MVP 기본 전략',
    'description': '눌림 후 반등 후보 자동 탐색',
    'is_active': True,
    'market': 'KOSPI',
    'min_market_cap': 3000000000000,
    'min_trading_value': 10000000000,
    'rsi_period': 14,
    'rsi_signal_period': 9,
    'rsi_min': 30,
    'rsi_max': 45,
    'bb_period': 20,
    'bb_std': 2,
    'use_ma5_filter': True,
    'use_ma20_filter': True,
    'foreign_net_buy_days': 3,
    'scan_interval_type': 'eod',
}


def ensure_default_strategy(db: Session, user: User, *, commit: bool = True) -> Strategy:
    existing = db.scalar(select(Strategy).where(Strategy.user_id == user.id).order_by(Strategy.id.asc()).limit(1))
    if existing:
        return existing

    strategy = Strategy(user_id=user.id, **DEFAULT_STRATEGY_FIELDS)
    db.add(strategy)
    if commit:
        db.commit()
        db.refresh(strategy)
    else:
        db.flush()
    return strategy

