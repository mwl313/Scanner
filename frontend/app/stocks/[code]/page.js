"use client";

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';

import PageHeader from '../../../components/layout/PageHeader';
import MiniPriceChart from '../../../components/stocks/MiniPriceChart';
import StockHero from '../../../components/stocks/StockHero';
import SurfaceCard from '../../../components/ui/SurfaceCard';
import LoadingState from '../../../components/ui/LoadingState';
import EmptyState from '../../../components/ui/EmptyState';
import { useRequireAuth } from '../../../lib/auth';
import { apiRequest } from '../../../lib/api';
import {
  failReasonToPlainKorean,
  formatForeignValue,
  formatNumber,
  maStatus,
  reasonToPlainKorean,
} from '../../../lib/formatters';

export default function StockDetailPage() {
  const { loading } = useRequireAuth();
  const params = useParams();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (loading || !params.code) return;
    apiRequest(`/api/stocks/${params.code}`)
      .then(setDetail)
      .catch((err) => setError(err.message || '종목 상세를 불러오지 못했습니다.'));
  }, [loading, params.code]);

  const positivePoints = useMemo(() => {
    if (!detail) return [];
    return (detail.matched_reasons || []).map(reasonToPlainKorean).filter(Boolean);
  }, [detail]);

  const failedPoints = useMemo(() => {
    if (!detail) return [];
    return (detail.failed_reasons || []).map(failReasonToPlainKorean).filter(Boolean);
  }, [detail]);

  if (loading) return <LoadingState message="종목 상세를 불러오는 중..." />;
  if (error) return <EmptyState title="종목 정보를 가져오지 못했습니다." description={error} />;
  if (!detail) return <LoadingState message="지표를 준비하는 중..." />;

  return (
    <div className="page-stack">
      <PageHeader
        title="Stock Detail"
        subtitle="스캔 결과의 근거 지표와 외인 데이터 상태를 종목 단위로 확인합니다."
        actions={<Link href="/scans" className="btn btn-ghost">스캔 콘솔로</Link>}
      />

      <StockHero detail={detail} />

      <section className="stock-detail-grid">
        <SurfaceCard className="panel" tone="soft">
          <div className="panel-header">
            <h3>최근 종가 흐름</h3>
          </div>
          <MiniPriceChart values={detail.recent_closes} />
        </SurfaceCard>

        <SurfaceCard className="panel" tone="soft">
          <div className="panel-header">
            <h3>핵심 지표</h3>
          </div>
          <div className="detail-metric-grid">
            <p>RSI / Signal: {Number(detail.rsi).toFixed(2)} / {Number(detail.rsi_signal).toFixed(2)}</p>
            <p>MA5 / MA20 / MA60: {Number(detail.ma5).toFixed(2)} / {Number(detail.ma20).toFixed(2)} / {Number(detail.ma60).toFixed(2)}</p>
            <p>MA 상태: {maStatus(detail)}</p>
            <p>볼린저 하단: {Number(detail.bb_lower).toFixed(2)}</p>
            <p>현재가-하단 거리: {(((Number(detail.price) - Number(detail.bb_lower)) / Number(detail.bb_lower)) * 100).toFixed(2)}%</p>
            <p>외인 동향: {formatForeignValue(detail.foreign_net_buy_confirmed_value)}</p>
            <p>외인 장중 스냅샷: {formatForeignValue(detail.foreign_net_buy_snapshot_value)}</p>
            {(detail.foreign_recent_daily || []).length > 0 ? (
              <div className="detail-foreign-daily">
                <p className="metric-label">최근 3일 외인 동향</p>
                <ul className="reason-list">
                  {(detail.foreign_recent_daily || []).map((item) => (
                    <li key={item.trade_date}>
                      {item.trade_date}: {formatForeignValue(item.net_buy_qty)}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p>최근 3일 외인 동향: -</p>
            )}
            <p>외인 데이터 소스: {detail.foreign_data_source || '-'}</p>
            <p>가격: {formatNumber(detail.price)}</p>
            <p>거래대금: {formatNumber(detail.trading_value)}</p>
          </div>
        </SurfaceCard>
      </section>

      <section className="stock-insight-grid">
        <SurfaceCard className="panel" tone="soft">
          <div className="panel-header">
            <h3>긍정 포인트</h3>
          </div>
          {positivePoints.length === 0 ? (
            <p className="helper">긍정 포인트가 없습니다.</p>
          ) : (
            <ul className="reason-list">
              {positivePoints.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          )}
        </SurfaceCard>

        <SurfaceCard className="panel" tone="soft">
          <div className="panel-header">
            <h3>미충족 조건</h3>
          </div>
          {failedPoints.length === 0 ? (
            <p className="helper">미충족 조건이 없습니다.</p>
          ) : (
            <ul className="reason-list">
              {failedPoints.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          )}
        </SurfaceCard>
      </section>
    </div>
  );
}
