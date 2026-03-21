from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.services.strategy_schema_service import (
    ensure_strategy_config,
    normalize_strategy_config,
    strategy_config_to_legacy_fields,
)


LEGACY_CONFIG_KEYS = {
    'market',
    'min_market_cap',
    'min_trading_value',
    'rsi_period',
    'rsi_signal_period',
    'rsi_min',
    'rsi_max',
    'bb_period',
    'bb_std',
    'use_ma5_filter',
    'use_ma20_filter',
    'foreign_net_buy_days',
}


def _sync_strategy_config_for_items(db: Session, strategies: list[Strategy]) -> None:
    changed = False
    for strategy in strategies:
        _, item_changed = ensure_strategy_config(strategy)
        if item_changed:
            changed = True
            db.add(strategy)
    if changed:
        db.commit()
        for strategy in strategies:
            db.refresh(strategy)


def _apply_strategy_config(strategy: Strategy, strategy_config_payload) -> None:
    normalized = normalize_strategy_config(strategy_config_payload, legacy_source=strategy)
    strategy.strategy_config = normalized
    legacy_fields = strategy_config_to_legacy_fields(normalized)
    for key, value in legacy_fields.items():
        setattr(strategy, key, value)



def list_strategies(db: Session, user: User) -> list[Strategy]:
    strategies = list(db.scalars(select(Strategy).where(Strategy.user_id == user.id).order_by(Strategy.created_at.desc())).all())
    _sync_strategy_config_for_items(db, strategies)
    return strategies



def get_strategy_or_404(db: Session, user: User, strategy_id: int) -> Strategy:
    strategy = db.scalar(select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user.id))
    if not strategy:
        raise AppError(code='strategy_not_found', message='Strategy not found', status_code=404)
    config_changed = ensure_strategy_config(strategy)[1]
    if config_changed:
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
    return strategy



def create_strategy(db: Session, user: User, payload: StrategyCreate) -> Strategy:
    payload_data = payload.model_dump()
    strategy_config_payload = payload_data.pop('strategy_config', None)
    strategy = Strategy(user_id=user.id, **payload_data)
    _apply_strategy_config(strategy, strategy_config_payload)
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy



def update_strategy(db: Session, strategy: Strategy, payload: StrategyUpdate) -> Strategy:
    changes = payload.model_dump(exclude_unset=True)
    strategy_config_payload = changes.pop('strategy_config', None)
    has_legacy_field_update = any(key in LEGACY_CONFIG_KEYS for key in changes.keys())

    for key, value in changes.items():
        setattr(strategy, key, value)

    if strategy_config_payload is not None:
        _apply_strategy_config(strategy, strategy_config_payload)
    elif has_legacy_field_update:
        _apply_strategy_config(strategy, None)
    else:
        ensure_strategy_config(strategy)

    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy



def delete_strategy(db: Session, strategy: Strategy) -> None:
    db.delete(strategy)
    db.commit()



def duplicate_strategy(db: Session, user: User, strategy: Strategy) -> Strategy:
    strategy_config, changed = ensure_strategy_config(strategy)
    if changed:
        db.add(strategy)
        db.commit()
        db.refresh(strategy)

    legacy_fields = strategy_config_to_legacy_fields(strategy_config)
    copied = Strategy(
        user_id=user.id,
        name=f'{strategy.name} (복제)',
        description=strategy.description,
        is_active=strategy.is_active,
        scan_interval_type=strategy.scan_interval_type,
        scan_universe_limit=strategy.scan_universe_limit,
        strategy_config=deepcopy(strategy_config),
        **legacy_fields,
    )
    db.add(copied)
    db.commit()
    db.refresh(copied)
    return copied
