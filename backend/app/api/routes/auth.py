from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.auth import LoginRequest, MessageOut, SignupRequest, UserOut
from app.services.rate_limit_service import clear_login_rate_limit, enforce_login_rate_limit, enforce_signup_rate_limit
from app.services.auth_service import authenticate_user, create_user_session, logout_current_session, signup_user
from app.api.deps import get_current_user
from app.models.user import User
from app.utils.request_meta import is_https_request

router = APIRouter()


@router.post('/signup', response_model=UserOut)
def signup(payload: SignupRequest, request: Request, db: Session = Depends(get_db)) -> UserOut:
    settings = get_settings()
    if not settings.allow_public_signup:
        raise AppError(code='signup_disabled', message='Public signup is disabled', status_code=403)
    enforce_signup_rate_limit(request, payload.email)
    user = signup_user(db, payload.email, payload.password, payload.password_confirm)
    return UserOut.model_validate(user)


@router.post('/login', response_model=UserOut)
def login(payload: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> UserOut:
    settings = get_settings()
    enforce_login_rate_limit(request, payload.email)
    user = authenticate_user(db, payload.email, payload.password)
    clear_login_rate_limit(request, payload.email)
    token, _ = create_user_session(db, user, request)

    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=(settings.is_production or is_https_request(request)),
        samesite='lax',
        max_age=settings.session_days * 24 * 60 * 60,
        path='/',
    )
    return UserOut.model_validate(user)


@router.post('/logout', response_model=MessageOut)
def logout(response: Response, request: Request, db: Session = Depends(get_db)) -> MessageOut:
    settings = get_settings()
    logout_current_session(db, request)
    response.delete_cookie(key=settings.session_cookie_name, path='/')
    return MessageOut(message='Logged out')


@router.get('/me', response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
