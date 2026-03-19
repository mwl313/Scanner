from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_from_request


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_user_from_request(db, request)
    if user is None:
        raise AppError(code='unauthorized', message='Authentication required', status_code=401)
    return user
