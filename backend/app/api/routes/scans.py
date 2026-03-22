import logging
import threading

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import AppError
from app.db.session import SessionLocal, get_db
from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.scan import ScanResultOut, ScanRunOut, ScanRunRequest
from app.services.scan_service import (
    delete_scan_run,
    get_scan_run_or_404,
    list_scan_results,
    list_scan_runs,
    run_scan,
)
from app.services.strategy_service import get_strategy_or_404

router = APIRouter()
logger = logging.getLogger(__name__)


def _run_scan_background(strategy_id: int, run_type: str) -> None:
    db = SessionLocal()
    try:
        strategy = db.get(Strategy, strategy_id)
        if strategy is None:
            logger.warning('Background scan skipped: strategy not found (strategy_id=%s)', strategy_id)
            return
        run_scan(db, strategy, run_type)
    except Exception as exc:
        logger.exception('Background manual scan failed (strategy_id=%s): %s', strategy_id, exc)
    finally:
        db.close()


@router.post('/run', status_code=status.HTTP_202_ACCEPTED, response_class=Response)
def run_scan_endpoint(
    payload: ScanRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    strategy = get_strategy_or_404(db, current_user, payload.strategy_id)
    existing_running = db.scalar(
        select(ScanRun)
        .where(ScanRun.strategy_id == strategy.id, ScanRun.status == 'running')
        .order_by(ScanRun.started_at.desc())
    )
    if existing_running is not None:
        raise AppError(
            code='scan_already_running',
            message='해당 전략의 스캔이 이미 실행 중입니다. 잠시 후 다시 시도해 주세요.',
            status_code=409,
        )

    worker = threading.Thread(
        target=_run_scan_background,
        args=(strategy.id, payload.run_type),
        daemon=True,
        name=f'manual-scan-{strategy.id}',
    )
    worker.start()
    return Response(status_code=status.HTTP_202_ACCEPTED)


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


@router.delete('/{run_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_scan_run_endpoint(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        delete_scan_run(db, current_user, run_id)
    except ValueError as exc:
        raise AppError(code='scan_not_found', message=str(exc), status_code=404) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
