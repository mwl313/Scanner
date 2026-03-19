# KOSPI Swing Scanner MVP

`doc/stock_scanner_mvp_detailed_ko.md`를 source of truth로 구현한 MVP입니다.

## 구현 범위
- 인증: 회원가입/로그인/로그아웃/현재 사용자
- 전략 관리: 생성/수정/삭제/복제/목록/상세
- 스캔 엔진: KOSPI 대상, 지표 계산, 조건 평가, 점수/등급, 결과 저장
- 스캔 결과 화면: 정렬/필터/이유 표시
- 관심종목: 추가/제거/목록
- 매매일지: CRUD + 수익/수익률 자동 계산
- 대시보드: 오늘 요약/A등급/전략별 최근 결과/관심종목 변화/최근 일지
- Provider abstraction: `MarketDataProvider` + `MockMarketDataProvider` + `KisMarketDataProvider`

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
docker compose exec api python scripts/create_admin.py --email admin@example.com --password 'changeMe123!'
```

## Seed 데이터 주입
```bash
docker compose exec api python scripts/seed.py
```
기본 데모 계정: `demo@example.com / demo1234`

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
- 비밀번호: Argon2id 해시 저장
- 로그인 시 랜덤 세션 토큰 발급
- DB에는 토큰 해시만 저장
- 브라우저: HttpOnly cookie
- 쿠키 옵션: `HttpOnly`, `SameSite=Lax`, `Secure=(APP_ENV=production)`
- 세션 만료: 기본 30일
- 로그아웃 시 세션/쿠키 삭제

## Provider 교체
- 기본: `DATA_PROVIDER=mock`
- KIS 사용: `DATA_PROVIDER=kis` + `KIS_APP_KEY`, `KIS_APP_SECRET` 설정

현재 `KisMarketDataProvider`는 인터페이스/뼈대만 제공하며, 실제 KIS 엔드포인트 매핑은 운영 확장 단계에서 추가하도록 분리했습니다.

## 합리적 가정(문서 모호점 처리)
1. RSI 교차 타이밍: 당일 교차 또는 직전 1봉 교차(현재도 시그널 위)까지 허용.
2. MA20 근처 기준: MA20 대비 2% 이내 하회까지 `근처`로 인정.
3. 볼린저 하단 근접: 하단선과의 거리 3% 이내를 근접으로 정의.
4. 결과 저장: 필수조건 탈락 종목도 `EXCLUDED`로 저장해 상세/복기 가능하도록 처리.
5. 알림: DB 테이블은 구현했지만 MVP API/화면 범위에는 포함하지 않음.
6. 장중 스캔: `scan_interval_type` 구조(`intraday_5m`, `intraday_10m`)는 열어두고, 실제 주기 실행은 EOD 스케줄 우선.

## 운영 메모 (Mac mini self-hosted)
- 운영에서는 `APP_ENV=production` + HTTPS 종단(TLS) 구성 필요
- `Secure` 쿠키는 HTTPS에서만 전달됨
- nginx 앞단에서 SSL 인증서 자동 갱신(예: certbot) 구성 권장
- DB 정기 백업 스케줄 별도 구성 권장

## 주요 API
- Auth: `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`
- Strategies: `/api/strategies`
- Scans: `/api/scans/run`, `/api/scans`, `/api/scans/{id}`, `/api/scans/{id}/results`
- Stocks: `/api/stocks/{code}`, `/api/stocks/{code}/indicators`, `/api/stocks/{code}/reasons`
- Watchlist: `/api/watchlist`
- Journals: `/api/journals`
- Dashboard: `/api/dashboard/summary`
