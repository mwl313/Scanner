from datetime import timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.scan_result import ScanResult
from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.models.trade_journal import TradeJournal
from app.models.user import User
from app.models.watchlist_item import WatchlistItem
from app.schemas.dashboard import DashboardSummaryOut
from app.utils.datetime_utils import utcnow



def get_dashboard_summary(db: Session, user: User) -> DashboardSummaryOut:
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    run_base = (
        select(ScanRun)
        .join(Strategy, Strategy.id == ScanRun.strategy_id)
        .where(
            and_(
                Strategy.user_id == user.id,
                ScanRun.started_at >= today_start,
                ScanRun.started_at < tomorrow_start,
            )
        )
        .subquery()
    )

    today_scan_runs = db.scalar(select(func.count()).select_from(run_base)) or 0
    today_matched = db.scalar(select(func.coalesce(func.sum(run_base.c.total_matched), 0))) or 0

    today_a_grade_count = (
        db.scalar(
            select(func.count())
            .select_from(ScanResult)
            .join(ScanRun, ScanRun.id == ScanResult.scan_run_id)
            .join(Strategy, Strategy.id == ScanRun.strategy_id)
            .where(
                and_(
                    Strategy.user_id == user.id,
                    ScanRun.started_at >= today_start,
                    ScanRun.started_at < tomorrow_start,
                    ScanResult.grade == 'A',
                )
            )
        )
        or 0
    )

    recent_by_strategy = []
    strategies = db.scalars(select(Strategy).where(Strategy.user_id == user.id).order_by(Strategy.updated_at.desc())).all()
    for strategy in strategies:
        latest_run = db.scalar(
            select(ScanRun).where(ScanRun.strategy_id == strategy.id).order_by(ScanRun.started_at.desc()).limit(1)
        )
        latest_a_count = 0
        if latest_run:
            latest_a_count = (
                db.scalar(
                    select(func.count()).where(
                        and_(ScanResult.scan_run_id == latest_run.id, ScanResult.grade == 'A')
                    )
                )
                or 0
            )
        recent_by_strategy.append(
            {
                'strategy_id': strategy.id,
                'strategy_name': strategy.name,
                'latest_run_id': latest_run.id if latest_run else None,
                'latest_run_status': latest_run.status if latest_run else None,
                'latest_matched': latest_run.total_matched if latest_run else 0,
                'latest_a_count': latest_a_count,
            }
        )

    watchlist_added_7d = (
        db.scalar(
            select(func.count()).select_from(WatchlistItem).where(
                and_(
                    WatchlistItem.user_id == user.id,
                    WatchlistItem.created_at >= now - timedelta(days=7),
                )
            )
        )
        or 0
    )

    recent_journals_q = db.scalars(
        select(TradeJournal)
        .where(TradeJournal.user_id == user.id)
        .order_by(TradeJournal.trade_date.desc(), TradeJournal.created_at.desc())
        .limit(5)
    ).all()

    recent_journals = [
        {
            'id': item.id,
            'trade_date': item.trade_date,
            'stock_code': item.stock_code,
            'stock_name': item.stock_name,
            'profit_value': float(item.profit_value),
            'profit_rate': float(item.profit_rate),
        }
        for item in recent_journals_q
    ]

    return DashboardSummaryOut(
        today_scan_runs=today_scan_runs,
        today_matched=int(today_matched),
        today_a_grade_count=today_a_grade_count,
        recent_by_strategy=recent_by_strategy,
        watchlist_added_7d=watchlist_added_7d,
        recent_journals=recent_journals,
    )
