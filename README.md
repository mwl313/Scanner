# KOSPI Swing Scanner MVP (Scanner-First)

`doc/stock_scanner_mvp_detailed_ko.md`를 source of truth로 구현한 MVP입니다.
이번 단계에서는 제품 중심을 **스캐너 코어**(전략 → 스캔 → 결과 → 대시보드)로 재정렬했습니다.

## 핵심 범위
- 인증: 회원가입/로그인/로그아웃/현재 사용자
- 전략 관리: 생성/수정/삭제/복제/목록/상세
- 스캔 엔진: KOSPI 대상, 지표 계산, 조건 평가, 점수/등급, 결과 저장
- 스캔 결과: 점수 내림차순 고정 + 등급 다중 필터 + 긍정 포인트 표시
- 대시보드: 오늘 스캔 요약 + 전략별 최근 결과
- Provider abstraction: `MarketDataProvider` + `MockMarketDataProvider` + `KisMarketDataProvider`

## 전략 스키마 (Refactor)
전략은 `strategy_config` JSON 기반으로 동작합니다.

- 카테고리: `rsi`, `bollinger`, `ma`, `foreign`, `market_cap`, `trading_value`
- 공통 개념: `enabled`, `mandatory`, `weight`
- 점수: enabled 항목의 가중치 합 기준으로 정규화(0~100)
- mandatory 항목 미충족 시 `EXCLUDED`
- 전략 기본 설정에 `scan_universe_limit`(120/200/300/500/전체[0]) 지원
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

## 스캔 성능 벤치마크 (Pre-screen + 단계적 측정)
코스피 전체 스캔을 바로 확장하기 전에, universe 크기별 처리량을 비교하기 위한 벤치마크 스크립트를 제공합니다.

핵심 포인트:
- 병렬화 없이 현재 순차 스캔 구조 기준으로 측정
- pre-screen ON/OFF 비교 지원
- `universe_limit` 단계별(예: 120/200/300/500) 실행
- 결과를 Markdown + CSV 리포트로 저장
- `limit=0`(전체)는 안전 플래그 없으면 실행 차단

실행 예시:

1) 빠른 smoke test (mock):
```bash
docker compose exec api python scripts/run_scan_benchmark.py --preset mock-smoke
```

2) 실제 KIS baseline (pre-screen OFF):
```bash
docker compose exec api python scripts/run_scan_benchmark.py \
  --preset kis-baseline \
  --strategy-id 1
```

3) 실제 KIS pre-screen 비교 (pre-screen ON):
```bash
docker compose exec api python scripts/run_scan_benchmark.py \
  --preset kis-prescreen \
  --strategy-id 1
```

4) 실제 KIS 스케일링 비교 (ON/OFF 동시):
```bash
docker compose exec api python scripts/run_scan_benchmark.py \
  --preset kis-scaling \
  --strategy-id 1
```

5) full universe 가드 실행:
```bash
docker compose exec api python scripts/run_scan_benchmark.py \
  --preset kis-scaling \
  --strategy-id 1 \
  --include-full-universe \
  --allow-full-universe
```

리포트 출력:
- 기본 저장 경로: `backend/reports/`
- 파일 예시:
  - `scan-benchmark-YYYYMMDD-HHMMSS.md`
  - `scan-benchmark-YYYYMMDD-HHMMSS.csv`

벤치마크 시 수집 지표(샘플별):
- start/end time
- total_elapsed_seconds
- provider_fetch_elapsed_seconds
- universe_build_elapsed_seconds
- scan_loop_elapsed_seconds
- persistence_elapsed_seconds
- provider, universe_limit, pre_screen_enabled
- original universe, pre-screen filtered universe
- total_scanned / total_matched / failed_count
- success_rate, scanned/sec, avg sec/stock
- grade 분포(A/B/C/EXCLUDED), run_status

공정성/신뢰도 강화 포인트:
- provider universe warmup 1회 수행 후 케이스 실행(초회 캐시 페널티 완화)
- repeat마다 ON/OFF 순서를 교차해 순서 편향 완화
- suspicious findings 섹션에서 이상 편차 자동 표시

Pre-screen 동작:
- 일반 스캔(manual/scheduled)은 전략의 `scan_universe_limit`로 자동 결정
  - `120/200/300` => pre-screen OFF
  - `500/전체(0)` => pre-screen ON
- benchmark는 기존처럼 `universe_limit`/`pre_screen_enabled`를 직접 지정 가능
- pre-screen ON일 때 universe 준비 단계에서 시가총액 기준 1차 필터 적용
- 적용 위치: provider `list_stocks()` 직후, 무거운 지표 계산 이전

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
- 선택: `KIS_BASE_URL`, `KIS_REQUEST_TIMEOUT_SEC`, `KIS_REQUEST_INTERVAL_MS`, `KIS_TOKEN_RETRY_COOLDOWN_SEC`, `KIS_UNIVERSE_LIMIT`, `KIS_UNIVERSE_CACHE_HOURS`

`KisMarketDataProvider` 구현 범위:
- `list_stocks(market)`
- `get_daily_bars(stock_code, days)`
- `get_latest_quote(stock_code)`
- `get_foreign_investor_intraday_snapshot(stock_code)`
- `get_foreign_investor_daily_confirmed(...)` (확정 외인 canonical 소스)

### 확정 외인 소스 선택
- 권장값: `FOREIGN_CONFIRMED_SOURCE=provider` (기본값)
- 호환 모드: `auto`, `krx` (레거시)
- 운영 권장: KIS 실데이터에서는 `provider` 경로 사용
- KRX 설정(`KRX_BASE_URL`, `KRX_REQUEST_TIMEOUT_SEC`)은 레거시/비권장 fallback 용도

## 외인 데이터 모델 (Option A)
외국인 데이터는 2개 계층으로 분리합니다.

1. 장중 스냅샷 (`intraday snapshot`, KIS)
- 용도: 화면 정보성 표시(대시보드/종목 상세)
- 특징: 시점 데이터, 미확정

2. 일별 확정 데이터 (`daily confirmed`, KIS provider)
- 용도: 스캐너 점수/조건 평가의 기준 데이터
- 저장: `foreign_investor_daily` 테이블 (중복 안전: `stock_code + trade_date` unique)

핵심 규칙:
- 금액값(`value`)과 수량(`quantity`)을 섞지 않음
- 금액값이 없으면 `None`/unavailable로 처리 (수량 대체 금지)
- 스코어링은 **확정 데이터**만 사용
- 확정 데이터가 없으면 외인 조건은 **중립 처리** (스냅샷으로 점수 대체 금지)

### EOD 동기화 플로우
1. 스케줄러가 EOD 시각에 실행
   - 주말(토/일, `Asia/Seoul` 기준)은 스캔을 건너뜁니다.
2. KIS provider 기반 확정 외인 데이터 동기화 (`foreign_investor_daily` upsert)
3. 활성 전략 EOD 스캔 실행
4. 스캔 점수는 DB의 확정 외인 집계를 사용

추가 안정화 포인트:
- 토큰 실패/레이트리밋 시 짧은 cooldown 적용 (`KIS_TOKEN_RETRY_COOLDOWN_SEC`)
- 동기화 실패 시 전 종목 즉시 재시도 폭주를 막는 백오프 (`FOREIGN_SYNC_BACKOFF_SECONDS`)

현재 제한:
- 한국 공휴일 휴장일은 아직 반영하지 않습니다(주말만 skip).
- 향후 확장 시 거래일 캘린더 테이블/휴장일 소스를 추가해 `is_korean_trading_day`에 연결하면 됩니다.

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
- 등급 필터: 다중 체크 드롭다운(`전체`, `A`, `B`, `C`, `EXCLUDED`)
- 정렬: 항상 점수 내림차순 고정
- 메인 리스트는 핵심 필드만 표시:
  - 종목명 / 코드 / 현재가 / 점수 / 등급 / 긍정 포인트 / 상세 / Toss
- `긍정 포인트`는 내부 문자열을 평이한 한국어로 변환해 불릿으로 노출
- `Toss` 버튼은 유효한 6자리 코드일 때 `https://www.tossinvest.com/stocks/A{code}/order`를 새 탭으로 엽니다.
- `상세` 버튼 클릭 시 드로어에서 심화 정보 표시:
  - 점수/등급
  - 긍정 포인트(불릿)
  - 가격/거래대금
  - MA 상태
  - 볼린저 하단 거리
  - 외인 확정합/장중 스냅샷/상태/커버리지

## 합리적 가정(문서 모호점 처리)
1. RSI 교차 타이밍: 당일 교차 또는 직전 1봉 교차(현재도 시그널 위)까지 허용.
2. MA20 근처 기준: MA20 대비 2% 이내 하회까지 `근처`로 인정.
3. 볼린저 하단 근접: 하단선과의 거리 3% 이내를 근접으로 정의.
4. 결과 저장: 필수조건 탈락 종목도 `EXCLUDED`로 저장해 복기 가능하도록 처리.
5. KIS 유니버스는 전종목 완전탐색보다 안정 실행 가능한 상위 N개 스캔을 우선.
6. 외인 확정 데이터는 KIS provider 기준으로 동기화하며, 실패 시 스코어링은 외인 항목을 중립 처리하고 KIS 스냅샷은 정보 표시용으로만 사용.

## 외인 상태 코드 (운영 참고)
- `foreign_data_status`: `confirmed | unavailable`
- `foreign_unavailable_reason`:
  - `token_rate_limited`: 토큰 발급 제한/쿨다운
  - `api_empty`: provider 응답이 비어 있음
  - `insufficient_days`: 전략 요구일수 대비 커버리지 부족
  - `provider_error`: 네트워크/HTTP/API 오류
  - `parse_none`: 값 파싱 결과 유효한 금액이 없음
  - `unknown`: 분류되지 않은 예외
- `foreign_coverage_days`: 실제 확보된 확정 일수
- `foreign_required_days`: 전략이 요구한 확정 일수

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
