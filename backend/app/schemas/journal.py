from datetime import date, datetime

from pydantic import BaseModel, Field


class TradeJournalBase(BaseModel):
    strategy_id: int | None = None
    stock_code: str = Field(min_length=1, max_length=20)
    stock_name: str = Field(min_length=1, max_length=120)
    trade_date: date
    buy_reason: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    entry_price: float = Field(gt=0)
    exit_price: float | None = Field(default=None, gt=0)
    memo: str | None = None


class TradeJournalCreate(TradeJournalBase):
    pass


class TradeJournalUpdate(BaseModel):
    strategy_id: int | None = None
    stock_code: str | None = Field(default=None, min_length=1, max_length=20)
    stock_name: str | None = Field(default=None, min_length=1, max_length=120)
    trade_date: date | None = None
    buy_reason: str | None = Field(default=None, min_length=1)
    quantity: int | None = Field(default=None, gt=0)
    entry_price: float | None = Field(default=None, gt=0)
    exit_price: float | None = Field(default=None, gt=0)
    memo: str | None = None


class TradeJournalOut(TradeJournalBase):
    id: int
    user_id: int
    profit_value: float
    profit_rate: float
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
