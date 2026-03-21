"use client";

import Link from 'next/link';

import SurfaceCard from '../ui/SurfaceCard';
import StatusChip from '../ui/StatusChip';

function resolveMarket(item) {
  return item?.strategy_config?.market || item?.market || 'KOSPI';
}

function resolveRangeLabel(item) {
  const value = Number(item?.scan_universe_limit);
  if (value === 0) return '전체';
  if (Number.isFinite(value) && value > 0) return String(value);
  return '300';
}

export default function ProfileActiveStrategyCard({ strategy }) {
  if (!strategy) {
    return (
      <SurfaceCard className="profile-mini-card" tone="glass">
        <p className="kicker">ACTIVE STRATEGY</p>
        <h4>현재 액티브 전략</h4>
        <p className="helper">활성 전략이 없습니다. 전략 페이지에서 활성화해 주세요.</p>
        <div className="profile-mini-actions">
          <Link href="/strategies" className="btn btn-ghost">전략 보기</Link>
        </div>
      </SurfaceCard>
    );
  }

  return (
    <SurfaceCard className="profile-mini-card" tone="glass">
      <p className="kicker">ACTIVE STRATEGY</p>
      <div className="profile-strategy-head">
        <h4>현재 액티브 전략</h4>
        <StatusChip label="ACTIVE" tone="bull" />
      </div>
      <p className="profile-strategy-name">{strategy.name}</p>
      <p className="helper">{strategy.description || '설명 없음'}</p>

      <div className="profile-strategy-meta">
        <span>시장 {resolveMarket(strategy)}</span>
        <span>범위 {resolveRangeLabel(strategy)}</span>
        <span>인터벌 {strategy.scan_interval_type || 'eod'}</span>
      </div>

      <div className="profile-mini-actions">
        <Link href={`/strategies/${strategy.id}/edit`} className="btn btn-ghost">전략 편집</Link>
      </div>
    </SurfaceCard>
  );
}
