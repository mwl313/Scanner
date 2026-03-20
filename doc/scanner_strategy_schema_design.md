# Scanner Strategy Schema Design

## 목적
기존 하드코딩 기반 스캐닝 전략을 더 커스터마이징 가능한 구조로 확장한다.

핵심 방향:
- 각 카테고리는 `enabled`, `mandatory`, `weight`, `params`를 가진다
- 점수는 enabled 된 카테고리들의 weight 총합 기준 백분율로 계산한다
- mandatory=true 인 조건이 미충족이면 EXCLUDED 처리한다
- 시장은 당분간 KOSPI만 지원한다
- MA 기간은 자유화하지 않고 5 / 20 / 60 고정으로 유지한다
- 대신 MA 해석 방식만 파라미터화한다

---

## 공통 설계 원칙

### 카테고리 공통 필드
- `enabled`: 이 카테고리를 점수 계산에 포함할지 여부
- `mandatory`: 조건 미충족 시 바로 제외할지 여부
- `weight`: 해당 카테고리의 점수 기여 비중
- `params`: 카테고리별 세부 파라미터

### 점수 계산
- enabled=true 인 카테고리의 weight 총합을 계산
- 충족한 카테고리 weight 합 / 총 enabled weight 합 * 100
- mandatory=true 인 항목 중 하나라도 미충족이면 grade=EXCLUDED

---

## 카테고리 설계

### 1. RSI
필드:
- enabled
- mandatory
- weight
- period
- signal_period
- cross_lookback_bars
- min
- max

의미:
- `cross_lookback_bars`: 며칠 전까지의 RSI 상향 크로스를 인정할지

추천 기본값:
- enabled: true
- mandatory: true
- weight: 30
- period: 14
- signal_period: 9
- cross_lookback_bars: 1
- min: 30
- max: 40

### 2. Bollinger
필드:
- enabled
- mandatory
- weight
- period
- std
- lower_proximity_pct

의미:
- `lower_proximity_pct`: 볼린저 하단선에서 몇 % 이내면 근접으로 볼지

추천 기본값:
- enabled: true
- mandatory: false
- weight: 20
- period: 20
- std: 2.0
- lower_proximity_pct: 0.03

### 3. MA
MA는 3개의 하위 조건으로 나눈다.

#### 3-1. Price vs MA20
필드:
- enabled
- mandatory
- weight
- mode
- tolerance_pct

mode 후보:
- `above_only`
- `near_or_above`

의미:
- above_only: 가격이 MA20 위여야 함
- near_or_above: MA20 아래여도 tolerance_pct 이내면 허용

추천 기본값:
- enabled: true
- mandatory: true
- weight: 15
- mode: near_or_above
- tolerance_pct: 0.02

#### 3-2. MA5 vs MA20
필드:
- enabled
- mandatory
- weight
- mode

mode 후보:
- `ma5_above_ma20`
- `ma5_equal_or_above_ma20`

추천 기본값:
- enabled: true
- mandatory: false
- weight: 10
- mode: ma5_equal_or_above_ma20

#### 3-3. MA20 vs MA60
필드:
- enabled
- mandatory
- weight
- mode

mode 후보:
- `ma20_above_ma60`
- `ma20_equal_or_above_ma60`

추천 기본값:
- enabled: false
- mandatory: false
- weight: 10
- mode: ma20_equal_or_above_ma60

설명:
- 기존 기본 전략과 가장 비슷하게 유지하려면 처음에는 이 조건을 비활성화한다.

### 4. Foreign
필드:
- enabled
- mandatory
- weight
- days
- unavailable_policy

추천 기본값:
- enabled: true
- mandatory: false
- weight: 20
- days: 3
- unavailable_policy: neutral

### 5. Market Cap
필드:
- enabled
- mandatory
- weight
- min_market_cap

추천 기본값:
- enabled: true
- mandatory: true
- weight: 0
- min_market_cap: 3000000000000

### 6. Trading Value
필드:
- enabled
- mandatory
- weight
- min_trading_value

추천 기본값:
- enabled: true
- mandatory: true
- weight: 10
- min_trading_value: 10000000000

---

## 시장
- 당분간 `market = "KOSPI"`만 사용
- 코스닥은 추후 확장 대상

---

## 기본 전략 (기존 전략과 최대한 유사)
```json
{
  "market": "KOSPI",
  "scoring": {
    "normalize_to_percent": true
  },
  "categories": {
    "rsi": {
      "enabled": true,
      "mandatory": true,
      "weight": 30,
      "period": 14,
      "signal_period": 9,
      "cross_lookback_bars": 1,
      "min": 30,
      "max": 40
    },
    "bollinger": {
      "enabled": true,
      "mandatory": false,
      "weight": 20,
      "period": 20,
      "std": 2.0,
      "lower_proximity_pct": 0.03
    },
    "ma": {
      "price_vs_ma20": {
        "enabled": true,
        "mandatory": true,
        "weight": 15,
        "mode": "near_or_above",
        "tolerance_pct": 0.02
      },
      "ma5_vs_ma20": {
        "enabled": true,
        "mandatory": false,
        "weight": 10,
        "mode": "ma5_equal_or_above_ma20"
      },
      "ma20_vs_ma60": {
        "enabled": false,
        "mandatory": false,
        "weight": 10,
        "mode": "ma20_equal_or_above_ma60"
      }
    },
    "foreign": {
      "enabled": true,
      "mandatory": false,
      "weight": 20,
      "days": 3,
      "unavailable_policy": "neutral"
    },
    "market_cap": {
      "enabled": true,
      "mandatory": true,
      "weight": 0,
      "min_market_cap": 3000000000000
    },
    "trading_value": {
      "enabled": true,
      "mandatory": true,
      "weight": 10,
      "min_trading_value": 10000000000
    }
  }
}
```

---

## UI 설계 원칙
- 각 카테고리는 카드 단위로 보여준다
- 각 카드에는 `Enabled` 체크박스가 있다
- Enabled를 체크해야 나머지 필드가 해금된다
- Enabled가 false면:
  - Mandatory 체크 비활성화
  - Weight 입력 비활성화
  - 세부 파라미터 비활성화
- Mandatory는 사용자에게 `미충족 시 탈락`으로 설명한다
- Enabled는 사용자에게 `점수에 반영`으로 설명한다

### MA UI 표현 권장
섹션 제목:
- 이동평균선 (MA)

하위 조건:
- 가격 vs MA20
- MA5 vs MA20
- MA20 vs MA60

체크박스 라벨:
- 점수에 반영
- 미충족 시 탈락

설명:
- 가격 vs MA20: 현재가가 20일 평균선 근처에서 버티는지 봅니다
- MA5 vs MA20: 짧은 흐름이 다시 살아나는지 봅니다
- MA20 vs MA60: 중간 흐름이 큰 흐름보다 좋은지 봅니다
