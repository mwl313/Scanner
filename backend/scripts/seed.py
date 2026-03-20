import os
import sys
import secrets
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.scan_result import ScanResult
from app.models.scan_run import ScanRun
from app.models.strategy import Strategy
from app.models.trade_journal import TradeJournal
from app.models.user import User
from app.services.scan_service import run_scan
from app.utils.security import hash_password


def seed() -> None:
    db = SessionLocal()
    try:
        email = 'demo@example.com'
        demo_password = os.getenv('SEED_DEMO_PASSWORD', '').strip()
        if not demo_password:
            demo_password = secrets.token_urlsafe(12)
            print(
                '[seed] SEED_DEMO_PASSWORD is not set. Generated one-time demo password '
                f'for this run: {demo_password}'
            )
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(email=email, password_hash=hash_password(demo_password))
            db.add(user)
            db.commit()
            db.refresh(user)

        strategy = db.scalar(select(Strategy).where(Strategy.user_id == user.id).limit(1))
        if not strategy:
            strategy = Strategy(
                user_id=user.id,
                name='MVP 기본 전략',
                description='눌림 후 반등 후보 자동 탐색',
                is_active=True,
                market='KOSPI',
                min_market_cap=3000000000000,
                min_trading_value=10000000000,
                rsi_period=14,
                rsi_signal_period=9,
                rsi_min=30,
                rsi_max=45,
                bb_period=20,
                bb_std=2,
                use_ma5_filter=True,
                use_ma20_filter=True,
                foreign_net_buy_days=3,
                scan_interval_type='eod',
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)

        last_run = db.scalar(select(ScanRun).where(ScanRun.strategy_id == strategy.id).order_by(ScanRun.id.desc()))
        if not last_run:
            run_scan(db, strategy, run_type='scheduled')

        journal = db.scalar(select(TradeJournal).where(TradeJournal.user_id == user.id).limit(1))
        if not journal:
            journal = TradeJournal(
                user_id=user.id,
                strategy_id=strategy.id,
                stock_code='005930',
                stock_name='삼성전자',
                trade_date=date.today(),
                buy_reason='RSI 반등 + MA20 지지 확인',
                quantity=10,
                entry_price=70000,
                exit_price=72800,
                profit_value=28000,
                profit_rate=0.04,
                memo='seed 데이터',
            )
            db.add(journal)
            db.commit()

        count = db.scalar(select(ScanResult).where(ScanResult.strategy_id == strategy.id).limit(1))
        print('Seed complete', 'has_scan_result' if count else 'no_scan_result')
    finally:
        db.close()


if __name__ == '__main__':
    seed()
