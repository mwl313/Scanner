from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.user import User
from app.models.watchlist_item import WatchlistItem
from app.schemas.watchlist import WatchlistCreate



def list_watchlist(db: Session, user: User, strategy_id: int | None = None) -> list[WatchlistItem]:
    stmt = select(WatchlistItem).where(WatchlistItem.user_id == user.id)
    if strategy_id is not None:
        stmt = stmt.where(WatchlistItem.strategy_id == strategy_id)
    stmt = stmt.order_by(WatchlistItem.created_at.desc())
    return list(db.scalars(stmt).all())



def add_watchlist_item(db: Session, user: User, payload: WatchlistCreate) -> WatchlistItem:
    existing = db.scalar(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id, WatchlistItem.stock_code == payload.stock_code)
    )
    if existing:
        raise AppError(code='watchlist_exists', message='Stock already exists in watchlist', status_code=409)

    item = WatchlistItem(
        user_id=user.id,
        stock_code=payload.stock_code,
        stock_name=payload.stock_name,
        strategy_id=payload.strategy_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item



def delete_watchlist_item(db: Session, user: User, item_id: int) -> None:
    item = db.scalar(select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id))
    if not item:
        raise AppError(code='watchlist_not_found', message='Watchlist item not found', status_code=404)
    db.delete(item)
    db.commit()
