import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.strategy import Strategy
from app.models.user import User
from app.utils.security import hash_password


def create_admin(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user:
            user = User(email=email.lower().strip(), password_hash=hash_password(password))
            db.add(user)
            db.commit()
            db.refresh(user)

        existing_strategy = db.scalar(select(Strategy).where(Strategy.user_id == user.id).limit(1))
        if not existing_strategy:
            db.add(
                Strategy(
                    user_id=user.id,
                    name='기본 눌림목 전략',
                    description='문서 기본값 기반 템플릿',
                    is_active=True,
                    market='KOSPI',
                    min_market_cap=3000000000000,
                    min_trading_value=10000000000,
                    rsi_period=14,
                    rsi_signal_period=9,
                    rsi_min=30,
                    rsi_max=40,
                    bb_period=20,
                    bb_std=2,
                    use_ma5_filter=True,
                    use_ma20_filter=True,
                    foreign_net_buy_days=3,
                    scan_interval_type='eod',
                )
            )
            db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create initial admin user')
    parser.add_argument('--email', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()

    create_admin(args.email, args.password)
    print('Admin ensured')
