"use client";

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

export default function StrategiesPage() {
  const { loading } = useRequireAuth();
  const [items, setItems] = useState([]);

  const load = () => apiRequest('/api/strategies').then(setItems);

  useEffect(() => {
    if (!loading) {
      load();
    }
  }, [loading]);

  const remove = async (id) => {
    await apiRequest(`/api/strategies/${id}`, { method: 'DELETE' });
    load();
  };

  const duplicate = async (id) => {
    await apiRequest(`/api/strategies/${id}/duplicate`, { method: 'POST' });
    load();
  };

  if (loading) {
    return <p>로딩중...</p>;
  }

  return (
    <div>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h2>전략 목록</h2>
        <Link href="/strategies/new"><button>새 전략</button></Link>
      </div>

      {items.map((item) => {
        const cfg = item.strategy_config?.categories;
        const market = item.strategy_config?.market || item.market;
        const rsiRange = cfg?.rsi ? `${cfg.rsi.min}~${cfg.rsi.max}` : `${item.rsi_min}~${item.rsi_max}`;
        const bbText = cfg?.bollinger ? `${cfg.bollinger.period}/${cfg.bollinger.std}` : `${item.bb_period}/${item.bb_std}`;
        return (
        <div className="card" key={item.id}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <div>
              <h3>{item.name}</h3>
              <p className="helper">{item.description || '설명 없음'}</p>
            </div>
            <div className="row">
              <Link href={`/strategies/${item.id}/edit`}><button className="secondary">편집</button></Link>
              <button onClick={() => duplicate(item.id)}>복제</button>
              <button className="danger" onClick={() => remove(item.id)}>삭제</button>
            </div>
          </div>
          <p className="helper">
            market={market}, RSI={rsiRange}, BB={bbText}, interval={item.scan_interval_type}
          </p>
        </div>
        );
      })}
    </div>
  );
}
