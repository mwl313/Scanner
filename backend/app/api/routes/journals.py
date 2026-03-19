from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.journal import TradeJournalCreate, TradeJournalOut, TradeJournalUpdate
from app.services.journal_service import (
    create_journal,
    delete_journal,
    get_journal_or_404,
    list_journals,
    update_journal,
)

router = APIRouter()


@router.get('', response_model=list[TradeJournalOut])
def get_journals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TradeJournalOut]:
    items = list_journals(db, current_user)
    return [TradeJournalOut.model_validate(item) for item in items]


@router.post('', response_model=TradeJournalOut)
def post_journal(
    payload: TradeJournalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradeJournalOut:
    journal = create_journal(db, current_user, payload)
    return TradeJournalOut.model_validate(journal)


@router.get('/{journal_id}', response_model=TradeJournalOut)
def get_journal(
    journal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradeJournalOut:
    journal = get_journal_or_404(db, current_user, journal_id)
    return TradeJournalOut.model_validate(journal)


@router.patch('/{journal_id}', response_model=TradeJournalOut)
def patch_journal(
    journal_id: int,
    payload: TradeJournalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradeJournalOut:
    journal = get_journal_or_404(db, current_user, journal_id)
    journal = update_journal(db, journal, payload)
    return TradeJournalOut.model_validate(journal)


@router.delete('/{journal_id}', status_code=204)
def remove_journal(
    journal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    journal = get_journal_or_404(db, current_user, journal_id)
    delete_journal(db, journal)
