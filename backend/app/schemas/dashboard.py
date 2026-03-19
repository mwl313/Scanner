from datetime import date

from pydantic import BaseModel


class DashboardRecentStrategy(BaseModel):
    strategy_id: int
    strategy_name: str
    latest_run_id: int | None
    latest_run_status: str | None
    latest_matched: int
    latest_a_count: int


class DashboardRecentJournal(BaseModel):
    id: int
    trade_date: date
    stock_code: str
    stock_name: str
    profit_value: float
    profit_rate: float


class DashboardSummaryOut(BaseModel):
    today_scan_runs: int
    today_matched: int
    today_a_grade_count: int
    recent_by_strategy: list[DashboardRecentStrategy]
    watchlist_added_7d: int
    recent_journals: list[DashboardRecentJournal]
