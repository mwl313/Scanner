from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyUpdate



def list_strategies(db: Session, user: User) -> list[Strategy]:
    return list(db.scalars(select(Strategy).where(Strategy.user_id == user.id).order_by(Strategy.created_at.desc())).all())



def get_strategy_or_404(db: Session, user: User, strategy_id: int) -> Strategy:
    strategy = db.scalar(select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user.id))
    if not strategy:
        raise AppError(code='strategy_not_found', message='Strategy not found', status_code=404)
    return strategy



def create_strategy(db: Session, user: User, payload: StrategyCreate) -> Strategy:
    strategy = Strategy(user_id=user.id, **payload.model_dump())
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy



def update_strategy(db: Session, strategy: Strategy, payload: StrategyUpdate) -> Strategy:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(strategy, key, value)
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy



def delete_strategy(db: Session, strategy: Strategy) -> None:
    db.delete(strategy)
    db.commit()



def duplicate_strategy(db: Session, user: User, strategy: Strategy) -> Strategy:
    copied = Strategy(
        user_id=user.id,
        name=f'{strategy.name} (복제)',
        description=strategy.description,
        is_active=strategy.is_active,
        market=strategy.market,
        min_market_cap=strategy.min_market_cap,
        min_trading_value=strategy.min_trading_value,
        rsi_period=strategy.rsi_period,
        rsi_signal_period=strategy.rsi_signal_period,
        rsi_min=strategy.rsi_min,
        rsi_max=strategy.rsi_max,
        bb_period=strategy.bb_period,
        bb_std=strategy.bb_std,
        use_ma5_filter=strategy.use_ma5_filter,
        use_ma20_filter=strategy.use_ma20_filter,
        foreign_net_buy_days=strategy.foreign_net_buy_days,
        scan_interval_type=strategy.scan_interval_type,
    )
    db.add(copied)
    db.commit()
    db.refresh(copied)
    return copied
