from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Strategy(TimestampMixin, Base):
    __tablename__ = 'strategies'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    market: Mapped[str] = mapped_column(String(20), default='KOSPI', nullable=False)
    min_market_cap: Mapped[int] = mapped_column(BigInteger, default=3000000000000, nullable=False)
    min_trading_value: Mapped[int] = mapped_column(BigInteger, default=10000000000, nullable=False)

    rsi_period: Mapped[int] = mapped_column(default=14, nullable=False)
    rsi_signal_period: Mapped[int] = mapped_column(default=9, nullable=False)
    rsi_min: Mapped[float] = mapped_column(default=30.0, nullable=False)
    rsi_max: Mapped[float] = mapped_column(default=40.0, nullable=False)

    bb_period: Mapped[int] = mapped_column(default=20, nullable=False)
    bb_std: Mapped[float] = mapped_column(default=2.0, nullable=False)

    use_ma5_filter: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_ma20_filter: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    foreign_net_buy_days: Mapped[int] = mapped_column(default=3, nullable=False)
    scan_interval_type: Mapped[str] = mapped_column(String(20), default='eod', nullable=False)
    strategy_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    user = relationship('User', back_populates='strategies')
    scan_runs = relationship('ScanRun', back_populates='strategy', cascade='all, delete-orphan')
    scan_results = relationship('ScanResult', back_populates='strategy', cascade='all, delete-orphan')
