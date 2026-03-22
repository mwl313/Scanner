from datetime import date

from sqlalchemy import BIGINT, Boolean, Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class StockDailyBar(TimestampMixin, Base):
    __tablename__ = 'stock_daily_bars'
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_stock_daily_bars_stock_trade_date'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    high_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    low_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    close_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BIGINT, nullable=False)
    trading_value: Mapped[int] = mapped_column(BIGINT, nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
