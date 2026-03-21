from sqlalchemy import BIGINT, JSON, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class ScanResult(TimestampMixin, Base):
    __tablename__ = 'scan_results'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_run_id: Mapped[int] = mapped_column(ForeignKey('scan_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False, index=True)

    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str] = mapped_column(String(120), nullable=False)
    market: Mapped[str] = mapped_column(String(20), nullable=False)

    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    ma5: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    ma20: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    ma60: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    bb_upper: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    bb_mid: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    bb_lower: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    rsi: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    rsi_signal: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    foreign_net_buy_value: Mapped[int] = mapped_column(BIGINT, nullable=False)
    foreign_net_buy_confirmed_value: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    foreign_net_buy_snapshot_value: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    foreign_data_status: Mapped[str] = mapped_column(String(20), nullable=False, default='unavailable')
    foreign_data_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    foreign_unavailable_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)
    foreign_coverage_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    foreign_required_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trading_value: Mapped[int] = mapped_column(BIGINT, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    matched_reasons_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    failed_reasons_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    scan_run = relationship('ScanRun', back_populates='results')
    strategy = relationship('Strategy', back_populates='scan_results')
