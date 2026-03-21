import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base


@pytest.fixture(autouse=True)
def isolate_test_settings(monkeypatch):
    from app.core.config import get_settings
    from app.providers.factory import get_market_data_provider

    monkeypatch.setenv('DATA_PROVIDER', 'mock')
    monkeypatch.setenv('FOREIGN_CONFIRMED_SOURCE', 'provider')
    monkeypatch.setenv('KIS_TOKEN_RETRY_COOLDOWN_SEC', '1')
    monkeypatch.setenv('FOREIGN_SYNC_BACKOFF_SECONDS', '1')

    get_settings.cache_clear()
    get_market_data_provider.cache_clear()
    yield
    get_settings.cache_clear()
    get_market_data_provider.cache_clear()


@pytest.fixture()
def db_session():
    engine = create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
