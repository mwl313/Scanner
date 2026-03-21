"use client";

import Link from 'next/link';
import { useEffect, useState } from 'react';

import PageHeader from '../../components/layout/PageHeader';
import SurfaceCard from '../../components/ui/SurfaceCard';
import StatusChip from '../../components/ui/StatusChip';
import LoadingState from '../../components/ui/LoadingState';
import EmptyState from '../../components/ui/EmptyState';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

function buildStrategySummary(item) {
  const cfg = item.strategy_config?.categories;
  const market = item.strategy_config?.market || item.market;
  const rsiRange = cfg?.rsi ? `${cfg.rsi.min} ~ ${cfg.rsi.max}` : `${item.rsi_min} ~ ${item.rsi_max}`;
  const foreignDays = cfg?.foreign?.days || item.foreign_net_buy_days || '-';
  const tradingValue = cfg?.trading_value?.min_trading_value || item.min_trading_value;
  const universeLimitLabel = Number(item.scan_universe_limit) === 0 ? '전체' : String(item.scan_universe_limit || 300);

  return [
    `시장 ${market}`,
    `범위 ${universeLimitLabel}`,
    `RSI ${rsiRange}`,
    `외인 ${foreignDays}일`,
    `거래대금 ${Number(tradingValue || 0).toLocaleString('ko-KR')}`,
  ];
}

export default function StrategiesPage() {
  const { loading } = useRequireAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');

  const load = () => apiRequest('/api/strategies').then(setItems);

  useEffect(() => {
    if (loading) return;
    load().catch((err) => setError(err.message || '전략 목록을 불러오지 못했습니다.'));
  }, [loading]);

  const remove = async (id) => {
    await apiRequest(`/api/strategies/${id}`, { method: 'DELETE' });
    await load();
  };

  const duplicate = async (id) => {
    await apiRequest(`/api/strategies/${id}/duplicate`, { method: 'POST' });
    await load();
  };

  if (loading) {
    return <LoadingState message="전략 목록을 불러오는 중..." />;
  }

  if (error) {
    return <EmptyState title="전략 목록을 가져오지 못했습니다." description={error} />;
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Strategies"
        subtitle="스캔 전략 템플릿을 관리하고 복제/수정하여 빠르게 실험할 수 있습니다."
        actions={<Link href="/strategies/new" className="btn btn-primary">새 전략</Link>}
      />

      {items.length === 0 ? (
        <EmptyState title="저장된 전략이 없습니다." description="첫 전략을 생성한 뒤 스캔 콘솔에서 실행해 주세요." />
      ) : (
        <div className="strategy-list-grid">
          {items.map((item) => {
            const summary = buildStrategySummary(item);
            return (
              <SurfaceCard key={item.id} className="strategy-list-card" tone="soft">
                <div className="strategy-list-head">
                  <div>
                    <h3>{item.name}</h3>
                    <p className="helper">{item.description || '설명 없음'}</p>
                  </div>
                  <StatusChip label={item.is_active ? 'ACTIVE' : 'PAUSED'} tone={item.is_active ? 'bull' : 'neutral'} />
                </div>

                <div className="strategy-inline-metrics">
                  {summary.map((text) => (
                    <span key={text}>{text}</span>
                  ))}
                </div>

                <div className="strategy-list-actions">
                  <Link href={`/strategies/${item.id}/edit`} className="btn btn-ghost">편집</Link>
                  <button type="button" className="btn btn-ghost" onClick={() => duplicate(item.id)}>복제</button>
                  <button type="button" className="btn btn-danger" onClick={() => remove(item.id)}>삭제</button>
                </div>
              </SurfaceCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
