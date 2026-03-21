"use client";

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

import PageHeader from '../../components/layout/PageHeader';
import LoadingState from '../../components/ui/LoadingState';
import EmptyState from '../../components/ui/EmptyState';
import SurfaceCard from '../../components/ui/SurfaceCard';
import ProfileScansPanel from '../../components/profile/ProfileScansPanel';
import ProfileIdentityCard from '../../components/profile/ProfileIdentityCard';
import ProfileActiveStrategyCard from '../../components/profile/ProfileActiveStrategyCard';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

function sortRunsLatest(items) {
  return [...items].sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
}

function resolveActiveStrategy(strategies, sortedRuns) {
  const activeStrategies = strategies.filter((item) => item.is_active);
  if (activeStrategies.length === 0) return null;
  const activeById = Object.fromEntries(activeStrategies.map((item) => [item.id, item]));

  for (const run of sortedRuns) {
    if (activeById[run.strategy_id]) return activeById[run.strategy_id];
  }
  return activeStrategies[0];
}

export default function DashboardPage() {
  const { loading, user } = useRequireAuth();
  const router = useRouter();

  const [runs, setRuns] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (loading) return;
    Promise.all([apiRequest('/api/scans'), apiRequest('/api/strategies')])
      .then(([scanRuns, strategyItems]) => {
        setRuns(scanRuns || []);
        setStrategies(strategyItems || []);
      })
      .catch((err) => setError(err.message || '프로필 데이터를 불러오지 못했습니다.'));
  }, [loading]);

  const sortedRuns = useMemo(() => sortRunsLatest(runs), [runs]);
  const strategyById = useMemo(() => Object.fromEntries(strategies.map((item) => [item.id, item])), [strategies]);
  const activeStrategy = useMemo(() => resolveActiveStrategy(strategies, sortedRuns), [strategies, sortedRuns]);

  if (loading) {
    return <LoadingState message="프로필 페이지를 준비하는 중..." />;
  }

  if (error) {
    return <EmptyState title="프로필 정보를 불러오지 못했습니다." description={error} />;
  }

  return (
    <div className="page-stack">
      <PageHeader title="프로필" subtitle="내 계정 정보와 스캔 기록을 빠르게 확인하고 스캔 콘솔로 바로 이동할 수 있습니다." />

      <div className="profile-layout">
        <ProfileScansPanel
          runs={sortedRuns}
          strategyById={strategyById}
          onOpenRun={(runId) => router.push(`/scans?runId=${runId}`)}
        />

        <SurfaceCard className="panel profile-panel profile-summary-panel" tone="soft">
          <div className="panel-header">
            <h3>프로필 요약</h3>
          </div>
          <div className="profile-summary-grid">
            <ProfileIdentityCard email={user?.email} />
            <ProfileActiveStrategyCard strategy={activeStrategy} />
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
