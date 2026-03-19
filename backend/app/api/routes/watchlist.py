from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.watchlist import WatchlistCreate, WatchlistOut
from app.services.watchlist_service import add_watchlist_item, delete_watchlist_item, list_watchlist

router = APIRouter()


@router.get('', response_model=list[WatchlistOut])
def get_watchlist(
    strategy_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WatchlistOut]:
    items = list_watchlist(db, current_user, strategy_id=strategy_id)
    return [WatchlistOut.model_validate(item) for item in items]


@router.post('', response_model=WatchlistOut)
def add_watchlist(
    payload: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WatchlistOut:
    item = add_watchlist_item(db, current_user, payload)
    return WatchlistOut.model_validate(item)


@router.delete('/{item_id}', status_code=204)
def remove_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    delete_watchlist_item(db, current_user, item_id)
