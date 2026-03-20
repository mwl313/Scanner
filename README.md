# KOSPI Swing Scanner MVP (Scanner-First)

`doc/stock_scanner_mvp_detailed_ko.md`를 source of truth로 구현한 MVP입니다.
이번 단계에서는 제품 중심을 **스캐너 코어**(전략 → 스캔 → 결과 → 대시보드)로 재정렬했습니다.

## 핵심 범위
- 인증: 회원가입/로그인/로그아웃/현재 사용자
- 전략 관리: 생성/수정/삭제/복제/목록/상세
- 스캔 엔진: KOSPI 대상, 지표 계산, 조건 평가, 점수/등급, 결과 저장
- 스캔 결과: 정렬/필터(A/B 기본)/핵심 이유 표시
- 대시보드: 오늘 스캔 요약 + 전략별 최근 결과
- Provider abstraction: `MarketDataProvider` + `MockMarketDataProvider` + `KisMarketDataProvider`

## 전략 스키마 (Refactor)
전략은 `strategy_config` JSON 기반으로 동작합니다.

- 카테고리: `rsi`, `bollinger`, `ma`, `foreign`, `market_cap`, `trading_value`
- 공통 개념: `enabled`, `mandatory`, `weight`
- 점수: enabled 항목의 가중치 합 기준으로 정규화(0~100)
- mandatory 항목 미충족 시 `EXCLUDED`
- MA 기간은 고정(`5/20/60`), 해석만 설정 가능:
  - `price_vs_ma20`
  - `ma5_vs_ma20`
  - `ma20_vs_ma60`

### 레거시 필드 매핑
기존 저장 전략(legacy 컬럼 기반)은 자동 매핑되어 동작합니다.

- `market` -> `strategy_config.market`
- `rsi_period/rsi_signal_period/rsi_min/rsi_max` -> `categories.rsi`
- `bb_period/bb_std` -> `categories.bollinger`
- `use_ma20_filter` -> `categories.ma.price_vs_ma20.enabled/mandatory`
- `use_ma5_filter` -> `categories.ma.ma5_vs_ma20.enabled`
- `foreign_net_buy_days` -> `categories.foreign.days`
- `min_market_cap` -> `categories.market_cap.min_market_cap`
- `min_trading_value` -> `categories.trading_value.min_trading_value`

## 이번 단계 스코프 정리
- watchlist / journal 기능은 핵심 플로우에서 제외했습니다.
- 기존 라우트/테이블은 호환성 때문에 유지하되, 메인 네비게이션과 핵심 카피에서는 비노출/비강조 처리했습니다.

## 기술 스택
- Frontend: Next.js App Router
- Backend: FastAPI + SQLAlchemy 2.x + Alembic
- DB: PostgreSQL
- Infra: Docker Compose
- Reverse proxy: nginx (same-origin `/api` 프록시)

## 디렉토리 구조
- `backend/`: API 서버, 모델, 서비스, 마이그레이션, 테스트
- `frontend/`: Next.js UI
- `infra/nginx/`: reverse proxy 설정
- `doc/`: 제품 스펙 문서
- `docker-compose.yml`: 전체 서비스 실행

## 빠른 시작 (Docker Compose)
1. 환경변수 파일 준비
```bash
cp .env.example .env
```
2. 전체 서비스 실행
```bash
docker compose up --build
```
3. 접속
- 웹: `http://localhost:8080`
- API Health: `http://localhost:8080/health`

## 초기 관리자 생성
```bash
docker compose exec api python scripts/create_admin.py --email admin@example.com
```
비밀번호는 프롬프트(숨김 입력)로 받습니다.
자동화가 필요하면 환경변수로 전달:
```bash
docker compose exec -e ADMIN_PASSWORD='changeMe123!' api python scripts/create_admin.py --email admin@example.com
```

## Seed 데이터 주입
```bash
docker compose exec api python scripts/seed.py
```
`SEED_DEMO_PASSWORD` 미설정 시 시드 실행마다 1회성 랜덤 비밀번호가 생성되어 로그에 출력됩니다.
고정 비밀번호를 쓰려면:
```bash
docker compose exec -e SEED_DEMO_PASSWORD='demo1234' api python scripts/seed.py
```

## 마이그레이션
### 적용
```bash
docker compose exec api alembic upgrade head
```
### 롤백(1단계)
```bash
docker compose exec api alembic downgrade -1
```

## 로컬 개발 실행 (컨테이너 없이)
### 백엔드
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 프론트엔드
```bash
cd frontend
npm install
# BACKEND_ORIGIN=http://localhost:8000 설정 시 /api rewrite 동작
npm run dev
```

## 테스트
```bash
cd backend
pytest
```

## 인증 방식
- 이메일/비밀번호 회원가입
- 신규 계정 생성 시 기본 전략 1개 자동 생성(`MVP 기본 전략`)
- 비밀번호: Argon2id 해시 저장
- 로그인 시 랜덤 세션 토큰 발급
- DB에는 토큰 해시만 저장
- 브라우저: HttpOnly cookie
- 쿠키 옵션: `HttpOnly`, `SameSite=Lax`, `Secure=(APP_ENV=production)`
- 세션 만료: 기본 30일
- 로그아웃 시 세션/쿠키 삭제

## 데이터 Provider
### Mock (개발 기본)
- `DATA_PROVIDER=mock`
- API 키 없이 전체 플로우 테스트 가능

### KIS (실데이터)
- `DATA_PROVIDER=kis`
- 필수: `KIS_APP_KEY`, `KIS_APP_SECRET`
- 선택: `KIS_BASE_URL`, `KIS_REQUEST_TIMEOUT_SEC`, `KIS_REQUEST_INTERVAL_MS`, `KIS_UNIVERSE_LIMIT`, `KIS_UNIVERSE_CACHE_HOURS`

`KisMarketDataProvider` 구현 범위:
- `list_stocks(market)`
- `get_daily_bars(stock_code, days)`
- `get_latest_quote(stock_code)`
- `get_foreign_investor_intraday_snapshot(stock_code)`
- `get_foreign_investor_daily_confirmed(...)` (provider 호환용; 스코어링 경로는 KRX 확정 데이터 사용)

### 확정 외인 소스 선택
- `FOREIGN_CONFIRMED_SOURCE=auto|krx|provider` (기본: `auto`)
- `auto` 동작:
  - `DATA_PROVIDER=mock` -> mock provider 확정 데이터 사용
  - `DATA_PROVIDER=kis` -> KRX 확정 데이터 사용
- KRX 설정: `KRX_BASE_URL`, `KRX_REQUEST_TIMEOUT_SEC`

## 외인 데이터 모델 (Option A)
외국인 데이터는 2개 계층으로 분리합니다.

1. 장중 스냅샷 (`intraday snapshot`, KIS)
- 용도: 화면 정보성 표시(대시보드/종목 상세)
- 특징: 시점 데이터, 미확정

2. 일별 확정 데이터 (`daily confirmed`, KRX)
- 용도: 스캐너 점수/조건 평가의 기준 데이터
- 저장: `foreign_investor_daily` 테이블 (중복 안전: `stock_code + trade_date` unique)

핵심 규칙:
- 금액값(`value`)과 수량(`quantity`)을 섞지 않음
- 금액값이 없으면 `None`/unavailable로 처리 (수량 대체 금지)
- 스코어링은 **확정 데이터**만 사용
- 확정 데이터가 없으면 외인 조건은 **중립 처리** (스냅샷으로 점수 대체 금지)

### EOD 동기화 플로우
1. 스케줄러가 EOD 시각에 실행
2. KRX 확정 외인 데이터 동기화 (`foreign_investor_daily` upsert)
3. 활성 전략 EOD 스캔 실행
4. 스캔 점수는 DB의 확정 외인 집계를 사용

### 현재 KIS 유니버스 정의
- 소스: KIS `kospi_code.mst.zip` 마스터 파일
- 필터:
  - KOSPI 표기 종목
  - ETP/ELW/SPAC 제외
  - 거래정지/정리매매/관리종목 제외
- 정렬: 시가총액 내림차순
- 스캔 대상: 상위 `KIS_UNIVERSE_LIMIT`개 (기본 120)

## 스캔 결과 UX
- 기본 등급 필터: `A/B`
- `EXCLUDED`는 명시적으로 선택했을 때 조회
- 결과 행에 `필수조건 통과/미충족` 상태 표시
- 통과 이유는 2~4개 핵심 라벨로 축약 표시
- 외인 데이터는 `확정합 / 장중 스냅샷 / 상태`를 분리 표시

## 합리적 가정(문서 모호점 처리)
1. RSI 교차 타이밍: 당일 교차 또는 직전 1봉 교차(현재도 시그널 위)까지 허용.
2. MA20 근처 기준: MA20 대비 2% 이내 하회까지 `근처`로 인정.
3. 볼린저 하단 근접: 하단선과의 거리 3% 이내를 근접으로 정의.
4. 결과 저장: 필수조건 탈락 종목도 `EXCLUDED`로 저장해 복기 가능하도록 처리.
5. KIS 유니버스는 전종목 완전탐색보다 안정 실행 가능한 상위 N개 스캔을 우선.
6. 외인 확정 데이터는 KRX 기준으로 동기화하며, 실패 시 스코어링은 외인 항목을 중립 처리하고 KIS 스냅샷은 정보 표시용으로만 사용.

## 운영 메모 (Mac mini self-hosted)
- 운영에서는 `APP_ENV=production` + HTTPS 종단(TLS) 구성 필요
- `Secure` 쿠키는 HTTPS에서만 전달됨
- nginx 앞단 SSL 인증서 자동 갱신(예: certbot) 구성 권장
- DB 정기 백업 스케줄 별도 구성 권장

## 공개 배포 보안 설정
인터넷 공개 시 최소 권장값:
- `APP_ENV=production`
- `ENFORCE_HTTPS=true`
- `SECRET_KEY`를 충분히 긴 랜덤값으로 교체
- 회원가입 정책:
  - 공개 유지: `ALLOW_PUBLIC_SIGNUP=true` + rate limit 유지
  - 비공개/초대제: `ALLOW_PUBLIC_SIGNUP=false`

인증 rate limit 환경변수:
- `AUTH_LOGIN_RATE_LIMIT_IP_MAX` (기본 10)
- `AUTH_LOGIN_RATE_LIMIT_EMAIL_MAX` (기본 10)
- `AUTH_LOGIN_RATE_LIMIT_WINDOW_SEC` (기본 60)
- `AUTH_SIGNUP_RATE_LIMIT_IP_MAX` (기본 5)
- `AUTH_SIGNUP_RATE_LIMIT_EMAIL_MAX` (기본 3)
- `AUTH_SIGNUP_RATE_LIMIT_WINDOW_SEC` (기본 3600)

## 주요 API
- Auth: `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`
- Strategies: `/api/strategies`
- Scans: `/api/scans/run`, `/api/scans`, `/api/scans/{id}`, `/api/scans/{id}/results`
- Stocks: `/api/stocks/{code}`, `/api/stocks/{code}/indicators`, `/api/stocks/{code}/reasons`
- Dashboard: `/api/dashboard/summary`
