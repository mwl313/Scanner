from datetime import datetime

from pydantic import BaseModel


class WatchlistCreate(BaseModel):
    stock_code: str
    stock_name: str
    strategy_id: int | None = None


class WatchlistOut(BaseModel):
    id: int
    user_id: int
    stock_code: str
    stock_name: str
    strategy_id: int | None
    created_at: datetime

    model_config = {'from_attributes': True}
