"use client";

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import PageHeader from '../../components/layout/PageHeader';
import MetricCard from '../../components/ui/MetricCard';
import SurfaceCard from '../../components/ui/SurfaceCard';
import StatusChip from '../../components/ui/StatusChip';
import LoadingState from '../../components/ui/LoadingState';
import EmptyState from '../../components/ui/EmptyState';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';
import { formatDateTime, formatNumber } from '../../lib/formatters';

function getRunTone(status) {
  if (!status) return 'neutral';
  if (status.includes('completed')) return 'bull';
  if (status.includes('failed')) return 'bear';
  return 'neutral';
}

export default function DashboardPage() {
  const { loading } = useRequireAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (loading) return;
    apiRequest('/api/dashboard/summary')
      .then(setSummary)
      .catch((err) => setError(err.message || '대시보드를 불러오지 못했습니다.'));
  }, [loading]);

  const totalRecentMatched = useMemo(() => {
    if (!summary) return 0;
    return summary.recent_by_strategy.reduce((acc, item) => acc + Number(item.latest_matched || 0), 0);
  }, [summary]);

  if (loading) {
    return <LoadingState message="대시보드를 준비하는 중..." />;
  }

  if (error) {
    return <EmptyState title="대시보드를 불러오지 못했습니다." description={error} />;
  }

  if (!summary) {
    return <LoadingState message="요약 데이터를 로딩하는 중..." />;
  }

  return (
    <div className="page-stack">
      <PageHeader title="Dashboard" subtitle="오늘 신호 흐름과 전략별 최근 실행 상태를 한 화면에서 확인합니다." />

      <div className="dashboard-hero-wrap">
        <SurfaceCard className="dashboard-hero" tone="glass">
          <div>
            <p className="kicker">TODAY OVERVIEW</p>
            <h2>KOSPI Swing Scan Brief</h2>
            <p className="helper">전략 저장 → 실행 → 결과 검토 흐름을 중심으로 운영되는 scanner-first 대시보드입니다.</p>
          </div>
          <div className="dashboard-hero-actions">
            <StatusChip label="LIVE READY" tone="neutral" />
            <Link href="/scans" className="btn btn-primary">스캔 콘솔 열기</Link>
          </div>
        </SurfaceCard>

        <div className="dashboard-metric-grid">
          <MetricCard title="Today Runs" value={formatNumber(summary.today_scan_runs)} hint="오늘 실행 횟수" />
          <MetricCard title="Today Matched" value={formatNumber(summary.today_matched)} hint="오늘 매칭 종목" tone="soft" />
          <MetricCard title="A Grade" value={formatNumber(summary.today_a_grade_count)} hint="강한 신호" tone="soft" />
          <MetricCard title="Recent Matched" value={formatNumber(totalRecentMatched)} hint="전략별 최근 합계" tone="soft" />
        </div>
      </div>

      <div className="dashboard-panels">
        <SurfaceCard className="panel" tone="soft">
          <div className="panel-header">
            <h3>전략별 최근 결과</h3>
            <Link href="/strategies" className="btn btn-ghost">전략 관리</Link>
          </div>

          {summary.recent_by_strategy.length === 0 ? (
            <EmptyState title="전략 실행 이력이 없습니다." description="전략을 만든 뒤 수동 스캔을 실행해 주세요." />
          ) : (
            <div className="strategy-list">
              {summary.recent_by_strategy.map((item) => (
                <article className="strategy-list-item" key={item.strategy_id}>
                  <div>
                    <p className="strategy-name">{item.strategy_name}</p>
                    <p className="helper">Run #{item.latest_run_id ?? '-'} · 매칭 {formatNumber(item.latest_matched)}개</p>
                  </div>
                  <div className="row">
                    <StatusChip label={item.latest_run_status || '-'} tone={getRunTone(item.latest_run_status)} />
                    <StatusChip label={`A ${formatNumber(item.latest_a_count)}`} tone="neutral" />
                  </div>
                </article>
              ))}
            </div>
          )}
        </SurfaceCard>

        <div className="page-stack">
          <SurfaceCard className="panel" tone="soft">
            <div className="panel-header">
              <h3>최근 매매일지</h3>
            </div>
            {summary.recent_journals.length === 0 ? (
              <p className="helper">최근 매매일지 데이터가 없습니다.</p>
            ) : (
              <div className="journal-list">
                {summary.recent_journals.map((item) => {
                  const positive = Number(item.profit_value) >= 0;
                  return (
                    <article className="journal-item" key={item.id}>
                      <div>
                        <p className="journal-stock">{item.stock_name} ({item.stock_code})</p>
                        <p className="helper">{formatDateTime(item.trade_date)}</p>
                      </div>
                      <p className={positive ? 'value-positive' : 'value-negative'}>
                        {formatNumber(item.profit_value)}
                        <span>{Number(item.profit_rate).toFixed(2)}%</span>
                      </p>
                    </article>
                  );
                })}
              </div>
            )}
          </SurfaceCard>

          <SurfaceCard className="panel" tone="soft">
            <div className="panel-header">
              <h3>관심종목 변화</h3>
              <StatusChip label="7D" tone="neutral" />
            </div>
            <p className="metric-card__value">{formatNumber(summary.watchlist_added_7d)}</p>
            <p className="helper">최근 7일 신규 추가된 관심종목 수</p>
          </SurfaceCard>
        </div>
      </div>
    </div>
  );
}
