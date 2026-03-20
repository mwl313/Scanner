from sqlalchemy import select
from starlette.requests import Request

from app.models.strategy import Strategy
from app.services.auth_service import authenticate_user, create_user_session, get_user_from_request, signup_user



def _build_request(cookie_header: str = '') -> Request:
    headers = []
    if cookie_header:
        headers.append((b'cookie', cookie_header.encode('utf-8')))
    scope = {'type': 'http', 'headers': headers, 'client': ('127.0.0.1', 12345)}
    return Request(scope)



def test_auth_signup_login_session_flow(db_session):
    user = signup_user(db_session, 'user@example.com', 'password123', 'password123')
    strategies = list(db_session.scalars(select(Strategy).where(Strategy.user_id == user.id)).all())
    assert len(strategies) == 1
    assert strategies[0].name == 'MVP 기본 전략'

    authed = authenticate_user(db_session, 'user@example.com', 'password123')
    assert authed.id == user.id

    token, _ = create_user_session(db_session, user, _build_request())
    req = _build_request(f'scanner_session={token}')
    current = get_user_from_request(db_session, req)
    assert current is not None
    assert current.email == 'user@example.com'
