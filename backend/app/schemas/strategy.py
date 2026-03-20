from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ScoringConfig(BaseModel):
    normalize_to_percent: bool = True


class RSIConfig(BaseModel):
    enabled: bool = True
    mandatory: bool = True
    weight: int = 30
    period: int = 14
    signal_period: int = 9
    cross_lookback_bars: int = 1
    min: float = 30.0
    max: float = 40.0


class BollingerConfig(BaseModel):
    enabled: bool = True
    mandatory: bool = False
    weight: int = 20
    period: int = 20
    std: float = 2.0
    lower_proximity_pct: float = 0.03


class PriceVsMA20Config(BaseModel):
    enabled: bool = True
    mandatory: bool = True
    weight: int = 15
    mode: Literal['above_only', 'near_or_above'] = 'near_or_above'
    tolerance_pct: float = 0.02


class MA5VsMA20Config(BaseModel):
    enabled: bool = True
    mandatory: bool = False
    weight: int = 10
    mode: Literal['ma5_above_ma20', 'ma5_equal_or_above_ma20'] = 'ma5_equal_or_above_ma20'


class MA20VsMA60Config(BaseModel):
    enabled: bool = False
    mandatory: bool = False
    weight: int = 10
    mode: Literal['ma20_above_ma60', 'ma20_equal_or_above_ma60'] = 'ma20_equal_or_above_ma60'


class MAConfig(BaseModel):
    price_vs_ma20: PriceVsMA20Config = Field(default_factory=PriceVsMA20Config)
    ma5_vs_ma20: MA5VsMA20Config = Field(default_factory=MA5VsMA20Config)
    ma20_vs_ma60: MA20VsMA60Config = Field(default_factory=MA20VsMA60Config)


class ForeignConfig(BaseModel):
    enabled: bool = True
    mandatory: bool = False
    weight: int = 20
    days: int = 3
    unavailable_policy: Literal['neutral', 'fail', 'pass'] = 'neutral'


class MarketCapConfig(BaseModel):
    enabled: bool = True
    mandatory: bool = True
    weight: int = 0
    min_market_cap: int = 3000000000000


class TradingValueConfig(BaseModel):
    enabled: bool = True
    mandatory: bool = True
    weight: int = 10
    min_trading_value: int = 10000000000


class StrategyCategoriesConfig(BaseModel):
    rsi: RSIConfig = Field(default_factory=RSIConfig)
    bollinger: BollingerConfig = Field(default_factory=BollingerConfig)
    ma: MAConfig = Field(default_factory=MAConfig)
    foreign: ForeignConfig = Field(default_factory=ForeignConfig)
    market_cap: MarketCapConfig = Field(default_factory=MarketCapConfig)
    trading_value: TradingValueConfig = Field(default_factory=TradingValueConfig)


class StrategyConfig(BaseModel):
    version: int = 1
    market: str = 'KOSPI'
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    categories: StrategyCategoriesConfig = Field(default_factory=StrategyCategoriesConfig)

    @field_validator('market')
    @classmethod
    def validate_market(cls, value: str) -> str:
        if value.upper() != 'KOSPI':
            raise ValueError('Only KOSPI market is supported in current strategy schema')
        return 'KOSPI'


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
    strategy_config: StrategyConfig | None = None


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
    strategy_config: StrategyConfig | None = None


class StrategyOut(StrategyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
