from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.trade_journal import TradeJournal
from app.models.user import User
from app.schemas.journal import TradeJournalCreate, TradeJournalUpdate



def _compute_profit(quantity: int, entry_price: float, exit_price: float | None) -> tuple[Decimal, Decimal]:
    if exit_price is None:
        return Decimal('0'), Decimal('0')

    qty = Decimal(str(quantity))
    entry = Decimal(str(entry_price))
    exit_v = Decimal(str(exit_price))

    profit_value = (exit_v - entry) * qty
    profit_rate = (exit_v - entry) / entry

    return (
        profit_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        profit_rate.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP),
    )



def list_journals(db: Session, user: User) -> list[TradeJournal]:
    return list(db.scalars(select(TradeJournal).where(TradeJournal.user_id == user.id).order_by(TradeJournal.trade_date.desc())).all())



def get_journal_or_404(db: Session, user: User, journal_id: int) -> TradeJournal:
    journal = db.scalar(select(TradeJournal).where(TradeJournal.id == journal_id, TradeJournal.user_id == user.id))
    if not journal:
        raise AppError(code='journal_not_found', message='Trade journal not found', status_code=404)
    return journal



def create_journal(db: Session, user: User, payload: TradeJournalCreate) -> TradeJournal:
    profit_value, profit_rate = _compute_profit(payload.quantity, payload.entry_price, payload.exit_price)
    journal = TradeJournal(
        user_id=user.id,
        strategy_id=payload.strategy_id,
        stock_code=payload.stock_code,
        stock_name=payload.stock_name,
        trade_date=payload.trade_date,
        buy_reason=payload.buy_reason,
        quantity=payload.quantity,
        entry_price=payload.entry_price,
        exit_price=payload.exit_price,
        profit_value=float(profit_value),
        profit_rate=float(profit_rate),
        memo=payload.memo,
    )
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal



def update_journal(db: Session, journal: TradeJournal, payload: TradeJournalUpdate) -> TradeJournal:
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(journal, key, value)

    profit_value, profit_rate = _compute_profit(journal.quantity, float(journal.entry_price), float(journal.exit_price) if journal.exit_price else None)
    journal.profit_value = float(profit_value)
    journal.profit_rate = float(profit_rate)

    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal



def delete_journal(db: Session, journal: TradeJournal) -> None:
    db.delete(journal)
    db.commit()
