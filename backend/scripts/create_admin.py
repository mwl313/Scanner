import os
import sys
import argparse
import getpass

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.services.default_strategy_service import ensure_default_strategy
from app.utils.security import hash_password


def _resolve_password(password_env: str) -> str:
    from_env = os.getenv(password_env, '').strip()
    if from_env:
        return from_env

    first = getpass.getpass('Admin password: ')
    second = getpass.getpass('Confirm admin password: ')
    if first != second:
        raise SystemExit('Password confirmation does not match')
    if len(first) < 8:
        raise SystemExit('Password must be at least 8 characters')
    return first


def create_admin(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user:
            user = User(email=email.lower().strip(), password_hash=hash_password(password))
            db.add(user)
            db.flush()

        ensure_default_strategy(db, user, commit=False)
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create initial admin user')
    parser.add_argument('--email', required=True)
    parser.add_argument(
        '--password-env',
        default='ADMIN_PASSWORD',
        help='Environment variable to read password from (default: ADMIN_PASSWORD). '
        'If empty, prompt via hidden input.',
    )
    args = parser.parse_args()

    password = _resolve_password(args.password_env)
    create_admin(args.email, password)
    print('Admin ensured')
