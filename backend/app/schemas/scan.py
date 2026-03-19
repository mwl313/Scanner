from datetime import datetime

from pydantic import BaseModel


class ScanRunRequest(BaseModel):
    strategy_id: int
    run_type: str = 'manual'


class ScanRunOut(BaseModel):
    id: int
    strategy_id: int
    run_type: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    total_scanned: int
    total_matched: int
    failed_count: int

    model_config = {'from_attributes': True}


class ScanResultOut(BaseModel):
    id: int
    scan_run_id: int
    strategy_id: int
    stock_code: str
    stock_name: str
    market: str
    price: float
    ma5: float
    ma20: float
    ma60: float
    bb_upper: float
    bb_mid: float
    bb_lower: float
    rsi: float
    rsi_signal: float
    foreign_net_buy_value: int
    trading_value: int
    score: int
    grade: str
    matched_reasons_json: list[str]
    failed_reasons_json: list[str]
    created_at: datetime

    model_config = {'from_attributes': True}


class StockDetailOut(BaseModel):
    stock_code: str
    stock_name: str
    market: str
    price: float
    ma5: float
    ma20: float
    ma60: float
    bb_upper: float
    bb_mid: float
    bb_lower: float
    rsi: float
    rsi_signal: float
    foreign_net_buy_value: int
    trading_value: int
    score: int
    grade: str
    matched_reasons: list[str]
    failed_reasons: list[str]
    recent_closes: list[float]
    scan_run_id: int
    strategy_id: int
    created_at: datetime
