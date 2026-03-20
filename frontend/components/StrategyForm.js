"use client";

import { useState } from 'react';

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
  strategy_config: defaultStrategyConfig,
};

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
  merged.strategy_config = deepMerge(defaultStrategyConfig, initial.strategy_config || {});
  return merged;
}

function SectionTitle({ title, subtitle }) {
  return (
    <div style={{ marginTop: 16 }}>
      <h3 style={{ marginBottom: 4 }}>{title}</h3>
      {subtitle && <p className="helper" style={{ marginTop: 0 }}>{subtitle}</p>}
    </div>
  );
}

export default function StrategyForm({ initial, onSubmit, submitLabel }) {
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

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(form);
  };

  const renderToggleRow = (basePath, enabled) => (
    <div className="row" style={{ gap: 16 }}>
      <label>
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setConfigValue([...basePath, 'enabled'], e.target.checked)}
        />
        {' '}점수에 반영
      </label>
      <label>
        <input
          type="checkbox"
          checked={Boolean(basePath.reduce((acc, key) => acc[key], form.strategy_config).mandatory)}
          onChange={(e) => setConfigValue([...basePath, 'mandatory'], e.target.checked)}
          disabled={!enabled}
        />
        {' '}미충족 시 탈락
      </label>
      <div>
        <label>가중치</label>
        <input
          type="number"
          value={basePath.reduce((acc, key) => acc[key], form.strategy_config).weight}
          onChange={(e) => setConfigValue([...basePath, 'weight'], Number(e.target.value))}
          disabled={!enabled}
        />
      </div>
    </div>
  );

  return (
    <form className="card" onSubmit={handleSubmit}>
      <div className="grid-2">
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

      <div style={{ marginTop: 10 }}>
        <label>설명</label>
        <textarea value={form.description || ''} onChange={(e) => setValue('description', e.target.value)} rows={3} />
      </div>

      <div className="grid-2" style={{ marginTop: 10 }}>
        <label>
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setValue('is_active', e.target.checked)}
          />
          {' '}활성화
        </label>
        <div>
          <label>스캔 인터벌</label>
          <select value={form.scan_interval_type} onChange={(e) => setValue('scan_interval_type', e.target.value)}>
            <option value="eod">eod</option>
            <option value="intraday_5m">intraday_5m</option>
            <option value="intraday_10m">intraday_10m</option>
          </select>
        </div>
      </div>

      <SectionTitle title="RSI" />
      {renderToggleRow(['categories', 'rsi'], cfg.rsi.enabled)}
      <div className="grid-3" style={{ marginTop: 8 }}>
        <div>
          <label>RSI 기간</label>
          <input
            type="number"
            value={cfg.rsi.period}
            onChange={(e) => setConfigValue(['categories', 'rsi', 'period'], Number(e.target.value))}
            disabled={!cfg.rsi.enabled}
          />
        </div>
        <div>
          <label>RSI 시그널 기간</label>
          <input
            type="number"
            value={cfg.rsi.signal_period}
            onChange={(e) => setConfigValue(['categories', 'rsi', 'signal_period'], Number(e.target.value))}
            disabled={!cfg.rsi.enabled}
          />
        </div>
        <div>
          <label>크로스 허용 봉 수</label>
          <input
            type="number"
            value={cfg.rsi.cross_lookback_bars}
            onChange={(e) => setConfigValue(['categories', 'rsi', 'cross_lookback_bars'], Number(e.target.value))}
            disabled={!cfg.rsi.enabled}
          />
        </div>
      </div>
      <div className="row" style={{ marginTop: 8 }}>
        <div>
          <label>RSI 최소</label>
          <input
            type="number"
            value={cfg.rsi.min}
            onChange={(e) => setConfigValue(['categories', 'rsi', 'min'], Number(e.target.value))}
            disabled={!cfg.rsi.enabled}
          />
        </div>
        <div>
          <label>RSI 최대</label>
          <input
            type="number"
            value={cfg.rsi.max}
            onChange={(e) => setConfigValue(['categories', 'rsi', 'max'], Number(e.target.value))}
            disabled={!cfg.rsi.enabled}
          />
        </div>
      </div>

      <SectionTitle title="Bollinger" />
      {renderToggleRow(['categories', 'bollinger'], cfg.bollinger.enabled)}
      <div className="grid-3" style={{ marginTop: 8 }}>
        <div>
          <label>기간</label>
          <input
            type="number"
            value={cfg.bollinger.period}
            onChange={(e) => setConfigValue(['categories', 'bollinger', 'period'], Number(e.target.value))}
            disabled={!cfg.bollinger.enabled}
          />
        </div>
        <div>
          <label>표준편차</label>
          <input
            type="number"
            step="0.1"
            value={cfg.bollinger.std}
            onChange={(e) => setConfigValue(['categories', 'bollinger', 'std'], Number(e.target.value))}
            disabled={!cfg.bollinger.enabled}
          />
        </div>
        <div>
          <label>하단 근접 비율</label>
          <input
            type="number"
            step="0.001"
            value={cfg.bollinger.lower_proximity_pct}
            onChange={(e) => setConfigValue(['categories', 'bollinger', 'lower_proximity_pct'], Number(e.target.value))}
            disabled={!cfg.bollinger.enabled}
          />
        </div>
      </div>

      <SectionTitle title="이동평균선 (MA)" />

      <div className="card" style={{ marginTop: 8 }}>
        <h4>가격 vs MA20</h4>
        <p className="helper">현재가가 20일 평균선 근처에서 버티는지 봅니다</p>
        {renderToggleRow(['categories', 'ma', 'price_vs_ma20'], cfg.ma.price_vs_ma20.enabled)}
        <div className="grid-2" style={{ marginTop: 8 }}>
          <div>
            <label>모드</label>
            <select
              value={cfg.ma.price_vs_ma20.mode}
              onChange={(e) => setConfigValue(['categories', 'ma', 'price_vs_ma20', 'mode'], e.target.value)}
              disabled={!cfg.ma.price_vs_ma20.enabled}
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
              disabled={!cfg.ma.price_vs_ma20.enabled}
            />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 8 }}>
        <h4>MA5 vs MA20</h4>
        <p className="helper">짧은 흐름이 다시 살아나는지 봅니다</p>
        {renderToggleRow(['categories', 'ma', 'ma5_vs_ma20'], cfg.ma.ma5_vs_ma20.enabled)}
        <div style={{ marginTop: 8 }}>
          <label>모드</label>
          <select
            value={cfg.ma.ma5_vs_ma20.mode}
            onChange={(e) => setConfigValue(['categories', 'ma', 'ma5_vs_ma20', 'mode'], e.target.value)}
            disabled={!cfg.ma.ma5_vs_ma20.enabled}
          >
            <option value="ma5_above_ma20">MA5 &gt; MA20</option>
            <option value="ma5_equal_or_above_ma20">MA5 &gt;= MA20</option>
          </select>
        </div>
      </div>

      <div className="card" style={{ marginTop: 8 }}>
        <h4>MA20 vs MA60</h4>
        <p className="helper">중간 흐름이 큰 흐름보다 좋은지 봅니다</p>
        {renderToggleRow(['categories', 'ma', 'ma20_vs_ma60'], cfg.ma.ma20_vs_ma60.enabled)}
        <div style={{ marginTop: 8 }}>
          <label>모드</label>
          <select
            value={cfg.ma.ma20_vs_ma60.mode}
            onChange={(e) => setConfigValue(['categories', 'ma', 'ma20_vs_ma60', 'mode'], e.target.value)}
            disabled={!cfg.ma.ma20_vs_ma60.enabled}
          >
            <option value="ma20_above_ma60">MA20 &gt; MA60</option>
            <option value="ma20_equal_or_above_ma60">MA20 &gt;= MA60</option>
          </select>
        </div>
      </div>

      <SectionTitle title="Foreign" />
      {renderToggleRow(['categories', 'foreign'], cfg.foreign.enabled)}
      <div className="grid-2" style={{ marginTop: 8 }}>
        <div>
          <label>최근 일수</label>
          <input
            type="number"
            value={cfg.foreign.days}
            onChange={(e) => setConfigValue(['categories', 'foreign', 'days'], Number(e.target.value))}
            disabled={!cfg.foreign.enabled}
          />
        </div>
        <div>
          <label>데이터 없음 처리</label>
          <select
            value={cfg.foreign.unavailable_policy}
            onChange={(e) => setConfigValue(['categories', 'foreign', 'unavailable_policy'], e.target.value)}
            disabled={!cfg.foreign.enabled}
          >
            <option value="neutral">중립</option>
            <option value="fail">실패</option>
            <option value="pass">통과</option>
          </select>
        </div>
      </div>

      <SectionTitle title="Market Cap" />
      {renderToggleRow(['categories', 'market_cap'], cfg.market_cap.enabled)}
      <div style={{ marginTop: 8 }}>
        <label>최소 시가총액</label>
        <input
          type="number"
          value={cfg.market_cap.min_market_cap}
          onChange={(e) => setConfigValue(['categories', 'market_cap', 'min_market_cap'], Number(e.target.value))}
          disabled={!cfg.market_cap.enabled}
        />
      </div>

      <SectionTitle title="Trading Value" />
      {renderToggleRow(['categories', 'trading_value'], cfg.trading_value.enabled)}
      <div style={{ marginTop: 8 }}>
        <label>최소 거래대금</label>
        <input
          type="number"
          value={cfg.trading_value.min_trading_value}
          onChange={(e) => setConfigValue(['categories', 'trading_value', 'min_trading_value'], Number(e.target.value))}
          disabled={!cfg.trading_value.enabled}
        />
      </div>

      <div style={{ marginTop: 16 }}>
        <button type="submit">{submitLabel}</button>
      </div>
    </form>
  );
}

