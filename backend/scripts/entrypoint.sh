#!/usr/bin/env sh
set -e

cd /app
export PYTHONPATH=/app

python - <<'PY'
import time
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)

for _ in range(60):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready')
        break
    except Exception as exc:
        print(f'Waiting for database: {exc}')
        time.sleep(2)
else:
    raise RuntimeError('Database connection timeout')
PY

alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
