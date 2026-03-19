from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class WatchlistItem(TimestampMixin, Base):
    __tablename__ = 'watchlist_items'
    __table_args__ = (UniqueConstraint('user_id', 'stock_code', name='uq_watchlist_user_stock'),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(120), nullable=False)
    strategy_id: Mapped[int | None] = mapped_column(ForeignKey('strategies.id', ondelete='SET NULL'), nullable=True, index=True)

    user = relationship('User', back_populates='watchlist_items')
