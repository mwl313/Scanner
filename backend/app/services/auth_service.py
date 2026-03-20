from datetime import timedelta

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.session import Session as UserSession
from app.models.user import User
from app.services.default_strategy_service import ensure_default_strategy
from app.utils.datetime_utils import utcnow
from app.utils.security import create_session_token, hash_password, hash_session_token, verify_password



def signup_user(db: Session, email: str, password: str, password_confirm: str) -> User:
    if password != password_confirm:
        raise AppError(code='password_mismatch', message='Password confirmation does not match', status_code=400)

    existing = db.scalar(select(User).where(User.email == email.lower().strip()))
    if existing:
        raise AppError(code='email_exists', message='Email already registered', status_code=409)

    user = User(email=email.lower().strip(), password_hash=hash_password(password))
    db.add(user)
    db.flush()
    ensure_default_strategy(db, user, commit=False)
    db.commit()
    db.refresh(user)
    return user



def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if not user or not verify_password(password, user.password_hash):
        raise AppError(code='invalid_credentials', message='Invalid email or password', status_code=401)
    return user



def create_user_session(db: Session, user: User, request: Request | None = None) -> tuple[str, UserSession]:
    settings = get_settings()
    token = create_session_token()
    token_hash = hash_session_token(token)

    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=utcnow() + timedelta(days=settings.session_days),
        user_agent=(request.headers.get('user-agent') if request else None),
        ip_address=(request.client.host if request and request.client else None),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, session



def get_user_from_request(db: Session, request: Request) -> User | None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None

    token_hash = hash_session_token(token)
    session = db.scalar(
        select(UserSession)
        .where(UserSession.token_hash == token_hash)
        .where(UserSession.expires_at > utcnow())
    )
    if not session:
        return None
    return db.get(User, session.user_id)



def logout_current_session(db: Session, request: Request) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return

    token_hash = hash_session_token(token)
    session = db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))
    if session:
        db.delete(session)
        db.commit()
