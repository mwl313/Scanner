from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class TradeJournal(TimestampMixin, Base):
    __tablename__ = 'trade_journals'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    strategy_id: Mapped[int | None] = mapped_column(ForeignKey('strategies.id', ondelete='SET NULL'), nullable=True, index=True)

    stock_code: Mapped[str] = mapped_column(String(20), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(120), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    buy_reason: Mapped[str] = mapped_column(Text, nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    profit_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    profit_rate: Mapped[float] = mapped_column(Numeric(8, 4), default=0, nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship('User', back_populates='trade_journals')
