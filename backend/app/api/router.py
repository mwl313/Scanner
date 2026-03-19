from fastapi import APIRouter

from app.api.routes import auth, dashboard, journals, scans, stocks, strategies, watchlist

api_router = APIRouter()
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(strategies.router, prefix='/strategies', tags=['strategies'])
api_router.include_router(scans.router, prefix='/scans', tags=['scans'])
api_router.include_router(stocks.router, prefix='/stocks', tags=['stocks'])
api_router.include_router(watchlist.router, prefix='/watchlist', tags=['watchlist'])
api_router.include_router(journals.router, prefix='/journals', tags=['journals'])
api_router.include_router(dashboard.router, prefix='/dashboard', tags=['dashboard'])
