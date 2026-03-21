"use client";

import { useState } from 'react';

import Popover from './ui/Popover';

const defaultStrategyConfig = {
  version: 1,
  market: 'KOSPI',
  scoring: { normalize_to_percent: true },
  categories: {
    rsi: {
      enabled: true,
      mandatory: true,
      weight: 30,
      period: 14,
      signal_period: 9,
      cross_lookback_bars: 1,
      min: 30,
      max: 40,
    },
    bollinger: {
      enabled: true,
      mandatory: false,
      weight: 20,
      period: 20,
      std: 2.0,
      lower_proximity_pct: 0.03,
    },
    ma: {
      price_vs_ma20: {
        enabled: true,
        mandatory: true,
        weight: 15,
        mode: 'near_or_above',
        tolerance_pct: 0.02,
      },
      ma5_vs_ma20: {
        enabled: true,
        mandatory: false,
        weight: 10,
        mode: 'ma5_equal_or_above_ma20',
      },
      ma20_vs_ma60: {
        enabled: false,
        mandatory: false,
        weight: 10,
        mode: 'ma20_equal_or_above_ma60',
      },
    },
    foreign: {
      enabled: true,
      mandatory: false,
      weight: 20,
      days: 3,
      unavailable_policy: 'neutral',
    },
    market_cap: {
      enabled: true,
      mandatory: true,
      weight: 0,
      min_market_cap: 3000000000000,
    },
    trading_value: {
      enabled: true,
      mandatory: true,
      weight: 10,
      min_trading_value: 10000000000,
    },
  },
};

const defaultStrategy = {
  name: '',
  description: '',
  is_active: true,
  market: 'KOSPI',
  scan_interval_type: 'eod',
  scan_universe_limit: 300,
  strategy_config: defaultStrategyConfig,
};

const scanUniverseOptions = [
  { value: 120, label: '120' },
  { value: 200, label: '200' },
  { value: 300, label: '300' },
  { value: 500, label: '500' },
  { value: 0, label: '전체' },
];

function deepMerge(base, override) {
  if (!override || typeof override !== 'object') return base;
  const out = { ...base };
  Object.keys(override).forEach((key) => {
    const value = override[key];
    if (value && typeof value === 'object' && !Array.isArray(value) && out[key] && typeof out[key] === 'object') {
      out[key] = deepMerge(out[key], value);
    } else {
      out[key] = value;
    }
  });
  return out;
}

function normalizeInitial(initial) {
  if (!initial) return { ...defaultStrategy };
  const merged = { ...defaultStrategy, ...initial };
  merged.scan_universe_limit = Number.isFinite(Number(initial.scan_universe_limit))
    ? Number(initial.scan_universe_limit)
    : defaultStrategy.scan_universe_limit;
  merged.strategy_config = deepMerge(defaultStrategyConfig, initial.strategy_config || {});
  return merged;
}

function InfoPopover({ title, description }) {
  return (
    <Popover
      align="right"
      panelClassName="info-panel"
      ariaLabel={`${title} 설명 보기`}
      trigger={({ onClick, open, ...rest }) => (
        <button type="button" className="info-trigger" onClick={onClick} data-open={open ? 'true' : 'false'} {...rest}>
          i
        </button>
      )}
    >
      <div role="dialog" aria-label={`${title} 설명`}>
        <div className="info-panel-inner">
          <p className="info-title">{title}</p>
          <p>{description}</p>
        </div>
      </div>
    </Popover>
  );
}

function SwitchControl({ checked, onChange, label, disabled = false }) {
  return (
    <label className={`switch-control ${disabled ? 'is-disabled' : ''}`}>
      <input type="checkbox" checked={checked} onChange={onChange} disabled={disabled} />
      <span className="switch-track" aria-hidden="true">
        <span className="switch-thumb" />
      </span>
      <span className="switch-label">{label}</span>
    </label>
  );
}

function RuleMetaRow({ enabled, mandatory, weight, onEnabledChange, onMandatoryChange, onWeightChange }) {
  return (
    <div className="strategy-meta-row">
      <div className="strategy-meta-item">
        <label>점수 반영</label>
        <SwitchControl checked={enabled} onChange={onEnabledChange} label={enabled ? 'ON' : 'OFF'} />
      </div>
      <div className="strategy-meta-item">
        <label>가중치</label>
        <input type="number" value={weight} onChange={onWeightChange} disabled={!enabled} />
      </div>
      <div className="strategy-meta-item">
        <label>필수</label>
        <SwitchControl checked={mandatory} onChange={onMandatoryChange} label={mandatory ? 'ON' : 'OFF'} disabled={!enabled} />
      </div>
    </div>
  );
}

function RuleCard({
  title,
  description,
  tone,
  enabled,
  mandatory,
  weight,
  onEnabledChange,
  onMandatoryChange,
  onWeightChange,
  children,
  isSub = false,
}) {
  return (
    <div className={`strategy-section strategy-section--${tone} ${isSub ? 'is-sub' : ''} ${enabled ? '' : 'is-disabled'}`}>
      <div className="strategy-section-header">
        <div className="strategy-section-title">
          <h3>{title}</h3>
          <InfoPopover title={title} description={description} />
        </div>
        <div className="strategy-section-header-right">
          {mandatory && <span className="status-chip status-chip--neutral">필수</span>}
          <SwitchControl checked={enabled} onChange={onEnabledChange} label="사용" />
        </div>
      </div>

      <RuleMetaRow
        enabled={enabled}
        mandatory={mandatory}
        weight={weight}
        onEnabledChange={onEnabledChange}
        onMandatoryChange={onMandatoryChange}
        onWeightChange={onWeightChange}
      />

      <fieldset className="strategy-fields-wrap" disabled={!enabled}>
        {children}
      </fieldset>
    </div>
  );
}

export default function StrategyForm({ initial, onSubmit, submitLabel, onCancel }) {
  const [form, setForm] = useState(normalizeInitial(initial));

  const setValue = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const setConfigValue = (path, value) => {
    setForm((prev) => {
      const next = JSON.parse(JSON.stringify(prev));
      let cursor = next.strategy_config;
      for (let i = 0; i < path.length - 1; i += 1) {
        cursor = cursor[path[i]];
      }
      cursor[path[path.length - 1]] = value;
      return next;
    });
  };

  const cfg = form.strategy_config.categories;
  const maAnyEnabled = Boolean(
    cfg.ma.price_vs_ma20.enabled || cfg.ma.ma5_vs_ma20.enabled || cfg.ma.ma20_vs_ma60.enabled,
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form className="strategy-form" onSubmit={handleSubmit}>
      <section className="strategy-section strategy-section--neutral">
        <div className="strategy-section-header">
          <div className="strategy-section-title">
            <h3>전략 기본 정보</h3>
            <InfoPopover
              title="전략 기본 정보"
              description="전략 이름, 시장, 설명, 활성화 여부, 스캔 주기를 설정합니다. 이 설정은 전략 단위의 기본 동작을 결정합니다."
            />
          </div>
        </div>

        <div className="strategy-fields-grid cols-2">
          <div>
            <label>전략명</label>
            <input value={form.name} onChange={(e) => setValue('name', e.target.value)} required />
          </div>
          <div>
            <label>시장</label>
            <select value={form.market} onChange={(e) => setValue('market', e.target.value)} disabled>
              <option value="KOSPI">KOSPI</option>
            </select>
          </div>
        </div>

        <div className="strategy-mt-md">
          <label>설명</label>
          <textarea value={form.description || ''} onChange={(e) => setValue('description', e.target.value)} rows={3} />
        </div>

        <div className="strategy-fields-grid cols-3 strategy-mt-md">
          <div>
            <label>활성화</label>
            <SwitchControl checked={form.is_active} onChange={(e) => setValue('is_active', e.target.checked)} label={form.is_active ? '사용' : '미사용'} />
          </div>
          <div>
            <label>스캔 인터벌</label>
            <select value={form.scan_interval_type} onChange={(e) => setValue('scan_interval_type', e.target.value)}>
              <option value="eod">eod</option>
              <option value="intraday_5m">intraday_5m</option>
              <option value="intraday_10m">intraday_10m</option>
            </select>
          </div>
          <div>
            <label>스캔 범위</label>
            <select
              value={String(form.scan_universe_limit)}
              onChange={(e) => setValue('scan_universe_limit', Number(e.target.value))}
            >
              {scanUniverseOptions.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="helper">선택한 범위만큼 상위 종목을 스캔합니다.</p>
          </div>
        </div>
      </section>

      <RuleCard
        title="RSI"
        description="RSI와 RSI 시그널의 상향 돌파 여부, 그리고 목표 RSI 구간을 함께 봅니다. 눌림 이후 반등 초입을 찾는 데 사용됩니다."
        tone="rsi"
        enabled={cfg.rsi.enabled}
        mandatory={cfg.rsi.mandatory}
        weight={cfg.rsi.weight}
        onEnabledChange={(e) => setConfigValue(['categories', 'rsi', 'enabled'], e.target.checked)}
        onMandatoryChange={(e) => setConfigValue(['categories', 'rsi', 'mandatory'], e.target.checked)}
        onWeightChange={(e) => setConfigValue(['categories', 'rsi', 'weight'], Number(e.target.value))}
      >
        <div className="strategy-fields-grid cols-3">
          <div>
            <label>RSI 기간</label>
            <input type="number" value={cfg.rsi.period} onChange={(e) => setConfigValue(['categories', 'rsi', 'period'], Number(e.target.value))} />
          </div>
          <div>
            <label>RSI 시그널 기간</label>
            <input type="number" value={cfg.rsi.signal_period} onChange={(e) => setConfigValue(['categories', 'rsi', 'signal_period'], Number(e.target.value))} />
          </div>
          <div>
            <label>크로스 허용 봉 수</label>
            <input type="number" value={cfg.rsi.cross_lookback_bars} onChange={(e) => setConfigValue(['categories', 'rsi', 'cross_lookback_bars'], Number(e.target.value))} />
          </div>
        </div>
        <div className="strategy-fields-grid cols-2 strategy-mt-sm">
          <div>
            <label>RSI 최소</label>
            <input type="number" value={cfg.rsi.min} onChange={(e) => setConfigValue(['categories', 'rsi', 'min'], Number(e.target.value))} />
          </div>
          <div>
            <label>RSI 최대</label>
            <input type="number" value={cfg.rsi.max} onChange={(e) => setConfigValue(['categories', 'rsi', 'max'], Number(e.target.value))} />
          </div>
        </div>
      </RuleCard>

      <RuleCard
        title="Bollinger"
        description="현재가가 볼린저 하단에 얼마나 가까운지 확인합니다. 눌림 구간에서 재반등 가능성이 있는지 보조 신호로 사용합니다."
        tone="bollinger"
        enabled={cfg.bollinger.enabled}
        mandatory={cfg.bollinger.mandatory}
        weight={cfg.bollinger.weight}
        onEnabledChange={(e) => setConfigValue(['categories', 'bollinger', 'enabled'], e.target.checked)}
        onMandatoryChange={(e) => setConfigValue(['categories', 'bollinger', 'mandatory'], e.target.checked)}
        onWeightChange={(e) => setConfigValue(['categories', 'bollinger', 'weight'], Number(e.target.value))}
      >
        <div className="strategy-fields-grid cols-3">
          <div>
            <label>기간</label>
            <input type="number" value={cfg.bollinger.period} onChange={(e) => setConfigValue(['categories', 'bollinger', 'period'], Number(e.target.value))} />
          </div>
          <div>
            <label>표준편차</label>
            <input type="number" step="0.1" value={cfg.bollinger.std} onChange={(e) => setConfigValue(['categories', 'bollinger', 'std'], Number(e.target.value))} />
          </div>
          <div>
            <label>하단 근접 비율</label>
            <input
              type="number"
              step="0.001"
              value={cfg.bollinger.lower_proximity_pct}
              onChange={(e) => setConfigValue(['categories', 'bollinger', 'lower_proximity_pct'], Number(e.target.value))}
            />
          </div>
        </div>
      </RuleCard>

      <section className="strategy-section strategy-section--ma">
        <div className="strategy-section-header">
          <div className="strategy-section-title">
            <h3>이동평균선 (MA)</h3>
            <InfoPopover
              title="이동평균선 (MA)"
              description="MA는 5/20/60일선을 고정으로 사용합니다. 각 하위 규칙에서 어떤 비교를 사용할지 선택해 추세 정합성을 판단합니다."
            />
          </div>
          <SwitchControl
            checked={maAnyEnabled}
            onChange={(e) => {
              const next = e.target.checked;
              setConfigValue(['categories', 'ma', 'price_vs_ma20', 'enabled'], next);
              setConfigValue(['categories', 'ma', 'ma5_vs_ma20', 'enabled'], next);
              setConfigValue(['categories', 'ma', 'ma20_vs_ma60', 'enabled'], next);
            }}
            label="사용"
          />
        </div>

        <div className="strategy-meta-row strategy-meta-row--readonly">
          <div className="strategy-meta-item">
            <label>점수 반영</label>
            <p className="strategy-meta-value">하위 규칙별 설정</p>
          </div>
          <div className="strategy-meta-item">
            <label>가중치</label>
            <p className="strategy-meta-value">하위 규칙별 설정</p>
          </div>
          <div className="strategy-meta-item">
            <label>필수</label>
            <p className="strategy-meta-value">하위 규칙별 설정</p>
          </div>
        </div>

        <div className="strategy-subcards">
          <RuleCard
            title="가격 vs MA20"
            description="현재가가 20일선 위인지, 또는 설정한 허용 오차 내에서 근처인지 확인합니다."
            tone="ma"
            isSub
            enabled={cfg.ma.price_vs_ma20.enabled}
            mandatory={cfg.ma.price_vs_ma20.mandatory}
            weight={cfg.ma.price_vs_ma20.weight}
            onEnabledChange={(e) => setConfigValue(['categories', 'ma', 'price_vs_ma20', 'enabled'], e.target.checked)}
            onMandatoryChange={(e) => setConfigValue(['categories', 'ma', 'price_vs_ma20', 'mandatory'], e.target.checked)}
            onWeightChange={(e) => setConfigValue(['categories', 'ma', 'price_vs_ma20', 'weight'], Number(e.target.value))}
          >
            <div className="strategy-fields-grid cols-2">
              <div>
                <label>모드</label>
                <select
                  value={cfg.ma.price_vs_ma20.mode}
                  onChange={(e) => setConfigValue(['categories', 'ma', 'price_vs_ma20', 'mode'], e.target.value)}
                >
                  <option value="above_only">위에만 허용</option>
                  <option value="near_or_above">근처 또는 위</option>
                </select>
              </div>
              <div>
                <label>허용 오차(%)</label>
                <input
                  type="number"
                  step="0.001"
                  value={cfg.ma.price_vs_ma20.tolerance_pct}
                  onChange={(e) => setConfigValue(['categories', 'ma', 'price_vs_ma20', 'tolerance_pct'], Number(e.target.value))}
                />
              </div>
            </div>
          </RuleCard>

          <RuleCard
            title="MA5 vs MA20"
            description="단기선(MA5)이 중기선(MA20) 위에 있는지 확인해 단기 흐름 회복 여부를 봅니다."
            tone="ma"
            isSub
            enabled={cfg.ma.ma5_vs_ma20.enabled}
            mandatory={cfg.ma.ma5_vs_ma20.mandatory}
            weight={cfg.ma.ma5_vs_ma20.weight}
            onEnabledChange={(e) => setConfigValue(['categories', 'ma', 'ma5_vs_ma20', 'enabled'], e.target.checked)}
            onMandatoryChange={(e) => setConfigValue(['categories', 'ma', 'ma5_vs_ma20', 'mandatory'], e.target.checked)}
            onWeightChange={(e) => setConfigValue(['categories', 'ma', 'ma5_vs_ma20', 'weight'], Number(e.target.value))}
          >
            <div className="strategy-fields-grid cols-1">
              <div>
                <label>모드</label>
                <select value={cfg.ma.ma5_vs_ma20.mode} onChange={(e) => setConfigValue(['categories', 'ma', 'ma5_vs_ma20', 'mode'], e.target.value)}>
                  <option value="ma5_above_ma20">MA5 &gt; MA20</option>
                  <option value="ma5_equal_or_above_ma20">MA5 &gt;= MA20</option>
                </select>
              </div>
            </div>
          </RuleCard>

          <RuleCard
            title="MA20 vs MA60"
            description="중기선(MA20)이 장기선(MA60)보다 강한지 확인해 큰 추세 방향과의 정합성을 확인합니다."
            tone="ma"
            isSub
            enabled={cfg.ma.ma20_vs_ma60.enabled}
            mandatory={cfg.ma.ma20_vs_ma60.mandatory}
            weight={cfg.ma.ma20_vs_ma60.weight}
            onEnabledChange={(e) => setConfigValue(['categories', 'ma', 'ma20_vs_ma60', 'enabled'], e.target.checked)}
            onMandatoryChange={(e) => setConfigValue(['categories', 'ma', 'ma20_vs_ma60', 'mandatory'], e.target.checked)}
            onWeightChange={(e) => setConfigValue(['categories', 'ma', 'ma20_vs_ma60', 'weight'], Number(e.target.value))}
          >
            <div className="strategy-fields-grid cols-1">
              <div>
                <label>모드</label>
                <select value={cfg.ma.ma20_vs_ma60.mode} onChange={(e) => setConfigValue(['categories', 'ma', 'ma20_vs_ma60', 'mode'], e.target.value)}>
                  <option value="ma20_above_ma60">MA20 &gt; MA60</option>
                  <option value="ma20_equal_or_above_ma60">MA20 &gt;= MA60</option>
                </select>
              </div>
            </div>
          </RuleCard>
        </div>
      </section>

      <RuleCard
        title="Foreign"
        description="최근 N일 외국인 확정 순매수 흐름을 확인합니다. 데이터 미확보 시 중립/실패/통과 정책으로 처리합니다."
        tone="foreign"
        enabled={cfg.foreign.enabled}
        mandatory={cfg.foreign.mandatory}
        weight={cfg.foreign.weight}
        onEnabledChange={(e) => setConfigValue(['categories', 'foreign', 'enabled'], e.target.checked)}
        onMandatoryChange={(e) => setConfigValue(['categories', 'foreign', 'mandatory'], e.target.checked)}
        onWeightChange={(e) => setConfigValue(['categories', 'foreign', 'weight'], Number(e.target.value))}
      >
        <div className="strategy-fields-grid cols-2">
          <div>
            <label>최근 일수</label>
            <input type="number" value={cfg.foreign.days} onChange={(e) => setConfigValue(['categories', 'foreign', 'days'], Number(e.target.value))} />
          </div>
          <div>
            <label>데이터 없음 처리</label>
            <select value={cfg.foreign.unavailable_policy} onChange={(e) => setConfigValue(['categories', 'foreign', 'unavailable_policy'], e.target.value)}>
              <option value="neutral">중립</option>
              <option value="fail">실패</option>
              <option value="pass">통과</option>
            </select>
          </div>
        </div>
      </RuleCard>

      <RuleCard
        title="Market Cap"
        description="시가총액이 최소 기준 이상인지 확인합니다. 유동성과 안정성을 위한 기본 필터로 사용합니다."
        tone="market-cap"
        enabled={cfg.market_cap.enabled}
        mandatory={cfg.market_cap.mandatory}
        weight={cfg.market_cap.weight}
        onEnabledChange={(e) => setConfigValue(['categories', 'market_cap', 'enabled'], e.target.checked)}
        onMandatoryChange={(e) => setConfigValue(['categories', 'market_cap', 'mandatory'], e.target.checked)}
        onWeightChange={(e) => setConfigValue(['categories', 'market_cap', 'weight'], Number(e.target.value))}
      >
        <div className="strategy-fields-grid cols-1">
          <div>
            <label>최소 시가총액</label>
            <input
              type="number"
              value={cfg.market_cap.min_market_cap}
              onChange={(e) => setConfigValue(['categories', 'market_cap', 'min_market_cap'], Number(e.target.value))}
            />
          </div>
        </div>
      </RuleCard>

      <RuleCard
        title="Trading Value"
        description="거래대금이 최소 기준 이상인지 확인합니다. 체결 유동성이 낮은 종목을 제외하기 위한 필터입니다."
        tone="trading-value"
        enabled={cfg.trading_value.enabled}
        mandatory={cfg.trading_value.mandatory}
        weight={cfg.trading_value.weight}
        onEnabledChange={(e) => setConfigValue(['categories', 'trading_value', 'enabled'], e.target.checked)}
        onMandatoryChange={(e) => setConfigValue(['categories', 'trading_value', 'mandatory'], e.target.checked)}
        onWeightChange={(e) => setConfigValue(['categories', 'trading_value', 'weight'], Number(e.target.value))}
      >
        <div className="strategy-fields-grid cols-1">
          <div>
            <label>최소 거래대금</label>
            <input
              type="number"
              value={cfg.trading_value.min_trading_value}
              onChange={(e) => setConfigValue(['categories', 'trading_value', 'min_trading_value'], Number(e.target.value))}
            />
          </div>
        </div>
      </RuleCard>

      <div className="strategy-actions">
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            취소
          </button>
        )}
        <button type="submit">{submitLabel}</button>
      </div>
    </form>
  );
}
