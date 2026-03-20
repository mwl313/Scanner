from datetime import date

from sqlalchemy import BIGINT, Boolean, Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class ForeignInvestorDaily(TimestampMixin, Base):
    __tablename__ = 'foreign_investor_daily'
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_foreign_investor_daily_stock_trade_date'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    net_buy_value: Mapped[int] = mapped_column(BIGINT, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
