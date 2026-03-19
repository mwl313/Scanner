from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User
from app.schemas.scan import ScanResultOut, ScanRunOut, ScanRunRequest
from app.services.scan_service import (
    get_scan_run_or_404,
    list_scan_results,
    list_scan_runs,
    run_scan,
)
from app.services.strategy_service import get_strategy_or_404

router = APIRouter()


@router.post('/run', response_model=ScanRunOut)
def run_scan_endpoint(
    payload: ScanRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanRunOut:
    strategy = get_strategy_or_404(db, current_user, payload.strategy_id)
    run = run_scan(db, strategy, payload.run_type)
    return ScanRunOut.model_validate(run)


@router.get('', response_model=list[ScanRunOut])
def get_scan_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ScanRunOut]:
    runs = list_scan_runs(db, current_user)
    return [ScanRunOut.model_validate(item) for item in runs]


@router.get('/{run_id}', response_model=ScanRunOut)
def get_scan_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanRunOut:
    try:
        run = get_scan_run_or_404(db, current_user, run_id)
    except ValueError as exc:
        raise AppError(code='scan_not_found', message=str(exc), status_code=404) from exc
    return ScanRunOut.model_validate(run)


@router.get('/{run_id}/results', response_model=list[ScanResultOut])
def get_scan_results(
    run_id: int,
    grade: str | None = Query(default=None),
    sort_by: str = Query(default='score'),
    sort_order: str = Query(default='desc'),
    watchlist_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ScanResultOut]:
    try:
        results = list_scan_results(
            db,
            current_user,
            run_id,
            grade=grade,
            sort_by=sort_by,
            sort_order=sort_order,
            watchlist_only=watchlist_only,
        )
    except ValueError as exc:
        raise AppError(code='scan_not_found', message=str(exc), status_code=404) from exc
    return [ScanResultOut.model_validate(item) for item in results]
