from datetime import datetime

from pydantic import BaseModel, Field


class StrategyBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    is_active: bool = True

    market: str = 'KOSPI'
    min_market_cap: int = 3000000000000
    min_trading_value: int = 10000000000

    rsi_period: int = 14
    rsi_signal_period: int = 9
    rsi_min: float = 30.0
    rsi_max: float = 40.0

    bb_period: int = 20
    bb_std: float = 2.0

    use_ma5_filter: bool = True
    use_ma20_filter: bool = True
    foreign_net_buy_days: int = 3
    scan_interval_type: str = 'eod'


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    is_active: bool | None = None

    market: str | None = None
    min_market_cap: int | None = None
    min_trading_value: int | None = None

    rsi_period: int | None = None
    rsi_signal_period: int | None = None
    rsi_min: float | None = None
    rsi_max: float | None = None

    bb_period: int | None = None
    bb_std: float | None = None

    use_ma5_filter: bool | None = None
    use_ma20_filter: bool | None = None
    foreign_net_buy_days: int | None = None
    scan_interval_type: str | None = None


class StrategyOut(StrategyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
