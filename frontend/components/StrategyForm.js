"use client";

import { useState } from 'react';

const defaultStrategy = {
  name: '',
  description: '',
  is_active: true,
  market: 'KOSPI',
  min_market_cap: 3000000000000,
  min_trading_value: 10000000000,
  rsi_period: 14,
  rsi_signal_period: 9,
  rsi_min: 30,
  rsi_max: 40,
  bb_period: 20,
  bb_std: 2,
  use_ma5_filter: true,
  use_ma20_filter: true,
  foreign_net_buy_days: 3,
  scan_interval_type: 'eod',
};

export default function StrategyForm({ initial, onSubmit, submitLabel }) {
  const [form, setForm] = useState({ ...defaultStrategy, ...(initial || {}) });

  const setValue = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <div className="grid-2">
        <div>
          <label>전략명</label>
          <input value={form.name} onChange={(e) => setValue('name', e.target.value)} required />
        </div>
        <div>
          <label>시장</label>
          <select value={form.market} onChange={(e) => setValue('market', e.target.value)}>
            <option value="KOSPI">KOSPI</option>
          </select>
        </div>
      </div>

      <div style={{ marginTop: 10 }}>
        <label>설명</label>
        <textarea value={form.description || ''} onChange={(e) => setValue('description', e.target.value)} rows={3} />
      </div>

      <div className="grid-3" style={{ marginTop: 10 }}>
        <div>
          <label>최소 시총</label>
          <input type="number" value={form.min_market_cap} onChange={(e) => setValue('min_market_cap', Number(e.target.value))} />
        </div>
        <div>
          <label>최소 거래대금</label>
          <input type="number" value={form.min_trading_value} onChange={(e) => setValue('min_trading_value', Number(e.target.value))} />
        </div>
        <div>
          <label>외인 순매수 일수</label>
          <input type="number" value={form.foreign_net_buy_days} onChange={(e) => setValue('foreign_net_buy_days', Number(e.target.value))} />
        </div>
      </div>

      <div className="grid-3" style={{ marginTop: 10 }}>
        <div>
          <label>RSI 기간</label>
          <input type="number" value={form.rsi_period} onChange={(e) => setValue('rsi_period', Number(e.target.value))} />
        </div>
        <div>
          <label>RSI 시그널 기간</label>
          <input type="number" value={form.rsi_signal_period} onChange={(e) => setValue('rsi_signal_period', Number(e.target.value))} />
        </div>
        <div>
          <label>RSI 범위</label>
          <div className="row">
            <input type="number" value={form.rsi_min} onChange={(e) => setValue('rsi_min', Number(e.target.value))} />
            <input type="number" value={form.rsi_max} onChange={(e) => setValue('rsi_max', Number(e.target.value))} />
          </div>
        </div>
      </div>

      <div className="grid-3" style={{ marginTop: 10 }}>
        <div>
          <label>볼린저 기간</label>
          <input type="number" value={form.bb_period} onChange={(e) => setValue('bb_period', Number(e.target.value))} />
        </div>
        <div>
          <label>볼린저 표준편차</label>
          <input type="number" step="0.1" value={form.bb_std} onChange={(e) => setValue('bb_std', Number(e.target.value))} />
        </div>
        <div>
          <label>스캔 인터벌</label>
          <select value={form.scan_interval_type} onChange={(e) => setValue('scan_interval_type', e.target.value)}>
            <option value="eod">eod</option>
            <option value="intraday_5m">intraday_5m</option>
            <option value="intraday_10m">intraday_10m</option>
          </select>
        </div>
      </div>

      <div className="row" style={{ marginTop: 12 }}>
        <label>
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setValue('is_active', e.target.checked)}
          />
          {' '}활성화
        </label>
        <label>
          <input
            type="checkbox"
            checked={form.use_ma5_filter}
            onChange={(e) => setValue('use_ma5_filter', e.target.checked)}
          />
          {' '}MA5 필터
        </label>
        <label>
          <input
            type="checkbox"
            checked={form.use_ma20_filter}
            onChange={(e) => setValue('use_ma20_filter', e.target.checked)}
          />
          {' '}MA20 필터
        </label>
      </div>

      <div style={{ marginTop: 16 }}>
        <button type="submit">{submitLabel}</button>
      </div>
    </form>
  );
}
