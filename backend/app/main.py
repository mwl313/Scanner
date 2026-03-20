from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.tasks.scheduler import scheduler_manager
from app.utils.request_meta import is_https_request


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler_manager.start()
    try:
        yield
    finally:
        scheduler_manager.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_exception_handlers(app)

    @app.middleware('http')
    async def security_middleware(request, call_next):
        request_is_https = is_https_request(request)
        if settings.enforce_https and not request_is_https:
            redirect_url = request.url.replace(scheme='https')
            return RedirectResponse(url=str(redirect_url), status_code=308)

        response = await call_next(request)

        if settings.security_headers_enabled:
            response.headers.setdefault('X-Frame-Options', 'DENY')
            response.headers.setdefault('X-Content-Type-Options', 'nosniff')
            response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
            response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
            response.headers.setdefault(
                'Content-Security-Policy',
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'",
            )
            if request_is_https:
                response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')

        return response

    @app.get('/health')
    def health() -> dict:
        return {'status': 'ok'}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
