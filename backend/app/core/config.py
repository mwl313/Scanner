from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'KOSPI Swing Scanner'
    app_env: str = 'development'
    log_level: str = 'INFO'
    api_prefix: str = '/api'

    database_url: str = 'postgresql+psycopg://scanner:scanner@db:5432/scanner'

    secret_key: str = 'change-me-in-production'
    session_cookie_name: str = 'scanner_session'
    session_days: int = 30

    data_provider: str = 'mock'
    kis_base_url: str = 'https://openapi.koreainvestment.com:9443'
    kis_app_key: str | None = None
    kis_app_secret: str | None = None
    kis_account_no: str | None = None
    kis_request_timeout_sec: float = 10.0
    kis_request_interval_ms: int = 80
    kis_universe_limit: int = 120
    kis_universe_cache_hours: int = 24

    scheduler_enabled: bool = False
    scheduler_timezone: str = 'Asia/Seoul'
    scheduler_eod_hour: int = 16
    scheduler_eod_minute: int = 10

    default_strategy_market: str = 'KOSPI'

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == 'production'


@lru_cache
def get_settings() -> Settings:
    return Settings()
