from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyOut, StrategyUpdate
from app.services.strategy_service import (
    create_strategy,
    delete_strategy,
    duplicate_strategy,
    get_strategy_or_404,
    list_strategies,
    update_strategy,
)

router = APIRouter()


@router.get('', response_model=list[StrategyOut])
def get_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StrategyOut]:
    return [StrategyOut.model_validate(item) for item in list_strategies(db, current_user)]


@router.post('', response_model=StrategyOut)
def post_strategy(
    payload: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrategyOut:
    strategy = create_strategy(db, current_user, payload)
    return StrategyOut.model_validate(strategy)


@router.get('/{strategy_id}', response_model=StrategyOut)
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrategyOut:
    strategy = get_strategy_or_404(db, current_user, strategy_id)
    return StrategyOut.model_validate(strategy)


@router.patch('/{strategy_id}', response_model=StrategyOut)
def patch_strategy(
    strategy_id: int,
    payload: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrategyOut:
    strategy = get_strategy_or_404(db, current_user, strategy_id)
    strategy = update_strategy(db, strategy, payload)
    return StrategyOut.model_validate(strategy)


@router.delete('/{strategy_id}', status_code=204)
def remove_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    strategy = get_strategy_or_404(db, current_user, strategy_id)
    delete_strategy(db, strategy)


@router.post('/{strategy_id}/duplicate', response_model=StrategyOut)
def duplicate_strategy_endpoint(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrategyOut:
    strategy = get_strategy_or_404(db, current_user, strategy_id)
    copied = duplicate_strategy(db, current_user, strategy)
    return StrategyOut.model_validate(copied)
