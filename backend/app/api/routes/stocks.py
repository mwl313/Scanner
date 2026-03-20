from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User
from app.providers.factory import get_market_data_provider
from app.schemas.scan import StockDetailOut
from app.services.scan_service import get_latest_stock_result

router = APIRouter()


@router.get('/{stock_code}', response_model=StockDetailOut)
def stock_detail(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockDetailOut:
    result = get_latest_stock_result(db, current_user, stock_code)
    if not result:
        raise AppError(code='stock_not_found', message='No scan data for stock', status_code=404)
    provider = get_market_data_provider()
    bars = provider.get_daily_bars(stock_code, 30)
    recent_closes = [float(bar.close_price) for bar in bars]
    snapshot_value = result.foreign_net_buy_snapshot_value
    snapshot_source = result.foreign_data_source
    try:
        snapshot = provider.get_foreign_investor_intraday_snapshot(stock_code)
        snapshot_value = snapshot.net_buy_value
        snapshot_source = f'{result.foreign_data_source}|{snapshot.source}' if result.foreign_data_source else snapshot.source
    except Exception:
        pass

    return StockDetailOut(
        stock_code=result.stock_code,
        stock_name=result.stock_name,
        market=result.market,
        price=float(result.price),
        ma5=float(result.ma5),
        ma20=float(result.ma20),
        ma60=float(result.ma60),
        bb_upper=float(result.bb_upper),
        bb_mid=float(result.bb_mid),
        bb_lower=float(result.bb_lower),
        rsi=float(result.rsi),
        rsi_signal=float(result.rsi_signal),
        foreign_net_buy_value=int(result.foreign_net_buy_value),
        foreign_net_buy_confirmed_value=(
            int(result.foreign_net_buy_confirmed_value) if result.foreign_net_buy_confirmed_value is not None else None
        ),
        foreign_net_buy_snapshot_value=(int(snapshot_value) if snapshot_value is not None else None),
        foreign_data_status=result.foreign_data_status or 'unavailable',
        foreign_data_source=snapshot_source,
        trading_value=int(result.trading_value),
        score=result.score,
        grade=result.grade,
        matched_reasons=result.matched_reasons_json,
        failed_reasons=result.failed_reasons_json,
        recent_closes=recent_closes,
        scan_run_id=result.scan_run_id,
        strategy_id=result.strategy_id,
        created_at=result.created_at,
    )


@router.get('/{stock_code}/indicators', response_model=dict)
def stock_indicators(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = get_latest_stock_result(db, current_user, stock_code)
    if not result:
        raise AppError(code='stock_not_found', message='No scan data for stock', status_code=404)
    return {
        'stock_code': result.stock_code,
        'ma5': float(result.ma5),
        'ma20': float(result.ma20),
        'ma60': float(result.ma60),
        'bb_upper': float(result.bb_upper),
        'bb_mid': float(result.bb_mid),
        'bb_lower': float(result.bb_lower),
        'rsi': float(result.rsi),
        'rsi_signal': float(result.rsi_signal),
        'foreign_net_buy_value': int(result.foreign_net_buy_value),
        'foreign_net_buy_confirmed_value': (
            int(result.foreign_net_buy_confirmed_value) if result.foreign_net_buy_confirmed_value is not None else None
        ),
        'foreign_net_buy_snapshot_value': (
            int(result.foreign_net_buy_snapshot_value) if result.foreign_net_buy_snapshot_value is not None else None
        ),
        'foreign_data_status': result.foreign_data_status or 'unavailable',
        'foreign_data_source': result.foreign_data_source,
    }


@router.get('/{stock_code}/reasons', response_model=dict)
def stock_reasons(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = get_latest_stock_result(db, current_user, stock_code)
    if not result:
        raise AppError(code='stock_not_found', message='No scan data for stock', status_code=404)
    return {
        'stock_code': result.stock_code,
        'score': result.score,
        'grade': result.grade,
        'matched_reasons': result.matched_reasons_json,
        'failed_reasons': result.failed_reasons_json,
    }
