"use client";

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { useRequireAuth } from '../../../lib/auth';
import { apiRequest } from '../../../lib/api';

export default function StockDetailPage() {
  const { loading } = useRequireAuth();
  const params = useParams();
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!loading && params.code) {
      apiRequest(`/api/stocks/${params.code}`)
        .then(setDetail);
    }
  }, [loading, params.code]);

  if (loading || !detail) return <p>로딩중...</p>;
  const foreignStatusLabel = detail.foreign_data_status === 'confirmed'
    ? ((detail.foreign_data_source || '').includes('krx_confirmed_daily') ? '확정(KRX)' : '확정')
    : (detail.foreign_net_buy_snapshot_value == null ? '없음' : '미확정(스냅샷)');

  return (
    <div>
      <h2>{detail.stock_name} ({detail.stock_code})</h2>

      <div className="grid-3">
        <div className="card"><h4>가격</h4><p>{Number(detail.price).toLocaleString()}</p></div>
        <div className="card"><h4>점수/등급</h4><p>{detail.score} / {detail.grade}</p></div>
        <div className="card"><h4>거래대금</h4><p>{Number(detail.trading_value).toLocaleString()}</p></div>
      </div>

      <div className="card">
        <h3>지표</h3>
        <div className="grid-3">
          <p>MA5: {Number(detail.ma5).toFixed(2)}</p>
          <p>MA20: {Number(detail.ma20).toFixed(2)}</p>
          <p>MA60: {Number(detail.ma60).toFixed(2)}</p>
          <p>BB Upper: {Number(detail.bb_upper).toFixed(2)}</p>
          <p>BB Mid: {Number(detail.bb_mid).toFixed(2)}</p>
          <p>BB Lower: {Number(detail.bb_lower).toFixed(2)}</p>
          <p>RSI: {Number(detail.rsi).toFixed(2)}</p>
          <p>RSI Signal: {Number(detail.rsi_signal).toFixed(2)}</p>
          <p>외인 최근 확정합: {detail.foreign_net_buy_confirmed_value == null ? '-' : Number(detail.foreign_net_buy_confirmed_value).toLocaleString()}</p>
          <p>외인 장중 스냅샷: {detail.foreign_net_buy_snapshot_value == null ? '-' : Number(detail.foreign_net_buy_snapshot_value).toLocaleString()}</p>
          <p>외인 데이터 상태: {foreignStatusLabel}</p>
          <p>외인 데이터 소스: {detail.foreign_data_source || '-'}</p>
        </div>
      </div>

      <div className="card">
        <h3>최근 종가(간단 차트)</h3>
        <div className="row" style={{ alignItems: 'flex-end', gap: 2, minHeight: 120 }}>
          {detail.recent_closes.map((value, idx) => {
            const min = Math.min(...detail.recent_closes);
            const max = Math.max(...detail.recent_closes);
            const ratio = max > min ? (value - min) / (max - min) : 0.5;
            return (
              <div
                key={idx}
                title={value.toLocaleString()}
                style={{
                  width: 6,
                  height: `${Math.max(8, ratio * 100)}px`,
                  background: '#0b6da8',
                  borderRadius: 2,
                }}
              />
            );
          })}
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>통과 조건</h3>
          <ul>
            {detail.matched_reasons.map((reason, idx) => <li key={idx}>{reason}</li>)}
          </ul>
        </div>
        <div className="card">
          <h3>미충족 조건</h3>
          <ul>
            {detail.failed_reasons.map((reason, idx) => <li key={idx}>{reason}</li>)}
          </ul>
        </div>
      </div>
    </div>
  );
}
