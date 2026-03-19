from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')
    strategies = relationship('Strategy', back_populates='user', cascade='all, delete-orphan')
    watchlist_items = relationship('WatchlistItem', back_populates='user', cascade='all, delete-orphan')
    trade_journals = relationship('TradeJournal', back_populates='user', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')
