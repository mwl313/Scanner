from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.tasks.scheduler import scheduler_manager


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

    @app.get('/health')
    def health() -> dict:
        return {'status': 'ok'}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
