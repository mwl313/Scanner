from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ScanRun(Base):
    __tablename__ = 'scan_runs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False, index=True)
    run_type: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    total_scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_target: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    strategy = relationship('Strategy', back_populates='scan_runs')
    results = relationship('ScanResult', back_populates='scan_run', cascade='all, delete-orphan')
