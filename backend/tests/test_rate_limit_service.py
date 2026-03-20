from starlette.requests import Request

from app.services.rate_limit_service import clear_login_rate_limit, enforce_login_rate_limit, enforce_signup_rate_limit


def _build_request(ip: str = '127.0.0.1') -> Request:
    headers = [(b'x-forwarded-for', ip.encode('utf-8')), (b'x-forwarded-proto', b'https')]
    scope = {'type': 'http', 'headers': headers, 'client': (ip, 12345), 'scheme': 'https'}
    return Request(scope)


def test_login_rate_limit_blocks_after_threshold(monkeypatch):
    from app.core.config import get_settings
    from app.core.exceptions import AppError

    monkeypatch.setenv('AUTH_LOGIN_RATE_LIMIT_IP_MAX', '1')
    monkeypatch.setenv('AUTH_LOGIN_RATE_LIMIT_EMAIL_MAX', '1')
    monkeypatch.setenv('AUTH_LOGIN_RATE_LIMIT_WINDOW_SEC', '60')
    get_settings.cache_clear()

    req = _build_request('10.10.10.10')
    enforce_login_rate_limit(req, 'user1@example.com')
    try:
        enforce_login_rate_limit(req, 'user1@example.com')
        assert False, 'expected rate limit'
    except AppError as exc:
        assert exc.status_code == 429
        assert exc.code == 'rate_limit_exceeded'


def test_login_rate_limit_can_be_cleared(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv('AUTH_LOGIN_RATE_LIMIT_IP_MAX', '1')
    monkeypatch.setenv('AUTH_LOGIN_RATE_LIMIT_EMAIL_MAX', '1')
    monkeypatch.setenv('AUTH_LOGIN_RATE_LIMIT_WINDOW_SEC', '60')
    get_settings.cache_clear()

    req = _build_request('10.10.10.11')
    enforce_login_rate_limit(req, 'user2@example.com')
    clear_login_rate_limit(req, 'user2@example.com')
    enforce_login_rate_limit(req, 'user2@example.com')


def test_signup_rate_limit_blocks_after_threshold(monkeypatch):
    from app.core.config import get_settings
    from app.core.exceptions import AppError

    monkeypatch.setenv('AUTH_SIGNUP_RATE_LIMIT_IP_MAX', '1')
    monkeypatch.setenv('AUTH_SIGNUP_RATE_LIMIT_EMAIL_MAX', '1')
    monkeypatch.setenv('AUTH_SIGNUP_RATE_LIMIT_WINDOW_SEC', '60')
    get_settings.cache_clear()

    req = _build_request('10.10.10.12')
    enforce_signup_rate_limit(req, 'user3@example.com')
    try:
        enforce_signup_rate_limit(req, 'user3@example.com')
        assert False, 'expected rate limit'
    except AppError as exc:
        assert exc.status_code == 429
        assert exc.code == 'rate_limit_exceeded'

