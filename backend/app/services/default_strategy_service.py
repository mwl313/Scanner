from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.scan_policy import DEFAULT_SCAN_UNIVERSE_LIMIT
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy import StrategyConfig
from app.services.strategy_schema_service import strategy_config_to_legacy_fields


DEFAULT_STRATEGY_CORE_FIELDS: dict = {
    'name': 'MVP 기본 전략',
    'description': '눌림 후 반등 후보 자동 탐색',
    'is_active': True,
    'scan_interval_type': 'eod',
    'scan_universe_limit': DEFAULT_SCAN_UNIVERSE_LIMIT,
}
DEFAULT_STRATEGY_CONFIG = StrategyConfig().model_dump()
DEFAULT_STRATEGY_LEGACY_FIELDS = strategy_config_to_legacy_fields(DEFAULT_STRATEGY_CONFIG)


def ensure_default_strategy(db: Session, user: User, *, commit: bool = True) -> Strategy:
    existing = db.scalar(select(Strategy).where(Strategy.user_id == user.id).order_by(Strategy.id.asc()).limit(1))
    if existing:
        return existing

    strategy = Strategy(
        user_id=user.id,
        strategy_config=DEFAULT_STRATEGY_CONFIG,
        **DEFAULT_STRATEGY_CORE_FIELDS,
        **DEFAULT_STRATEGY_LEGACY_FIELDS,
    )
    db.add(strategy)
    if commit:
        db.commit()
        db.refresh(strategy)
    else:
        db.flush()
    return strategy
