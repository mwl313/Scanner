import Link from 'next/link';

import Drawer from '../ui/Drawer';
import SurfaceCard from '../ui/SurfaceCard';
import GradeBadge from './GradeBadge';
import ScorePill from './ScorePill';
import {
  buildTossInvestUrl,
  failReasonToPlainKorean,
  foreignStatusLabel,
  formatForeignValue,
  formatNumber,
  maStatus,
  reasonToPlainKorean,
} from '../../lib/formatters';

export default function ScanResultDetailDrawer({ open, onClose, loading, error, detail }) {
  const tossUrl = buildTossInvestUrl(detail?.stock_code);
  const positivePoints = (detail?.matched_reasons || []).map(reasonToPlainKorean).filter(Boolean);
  const failedPoints = (detail?.failed_reasons || []).map(failReasonToPlainKorean).filter(Boolean);

  return (
    <Drawer open={open} onClose={onClose} title="종목 상세">
      {loading && <p className="helper">상세 정보를 불러오는 중...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && detail && (
        <div className="detail-stack">
          <SurfaceCard className="detail-hero" tone="soft">
            <div className="detail-hero-title">
              <div>
                <h3>{detail.stock_name}</h3>
                <p className="helper">{detail.stock_code} · {detail.market}</p>
              </div>
              <div className="detail-hero-side">
                <ScorePill score={detail.score} grade={detail.grade} />
                <GradeBadge grade={detail.grade} />
              </div>
            </div>
            <div className="detail-key-grid">
              <div><span className="metric-label">현재가</span><strong>{formatNumber(detail.price)}</strong></div>
              <div><span className="metric-label">거래대금</span><strong>{formatNumber(detail.trading_value)}</strong></div>
              <div><span className="metric-label">MA 상태</span><strong>{maStatus(detail)}</strong></div>
            </div>
            <div className="action-group detail-hero-actions">
              {tossUrl ? (
                <a className="btn btn-ghost" href={tossUrl} target="_blank" rel="noopener noreferrer">Toss</a>
              ) : (
                <button className="btn btn-ghost" disabled>Toss</button>
              )}
              <Link className="btn btn-ghost" href={`/stocks/${detail.stock_code}`}>종목 페이지</Link>
            </div>
          </SurfaceCard>

          <SurfaceCard>
            <h4>긍정 포인트</h4>
            <ul className="reason-list">
              {positivePoints.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </SurfaceCard>

          <SurfaceCard>
            <h4>핵심 지표</h4>
            <div className="detail-metric-grid">
              <p>RSI / Signal: {Number(detail.rsi).toFixed(2)} / {Number(detail.rsi_signal).toFixed(2)}</p>
              <p>MA5 / MA20 / MA60: {Number(detail.ma5).toFixed(2)} / {Number(detail.ma20).toFixed(2)} / {Number(detail.ma60).toFixed(2)}</p>
              <p>볼린저 하단 거리: {(((Number(detail.price) - Number(detail.bb_lower)) / Number(detail.bb_lower)) * 100).toFixed(2)}%</p>
              <p>외인 동향: {formatForeignValue(detail.foreign_net_buy_confirmed_value)}</p>
              <p>장중 외인 동향(스냅샷): {formatForeignValue(detail.foreign_net_buy_snapshot_value)}</p>
              {Array.isArray(detail.foreign_recent_daily) && detail.foreign_recent_daily.length > 0 ? (
                <div className="detail-foreign-daily">
                  <p className="metric-label">최근 3일 외인 동향</p>
                  <ul className="reason-list">
                    {detail.foreign_recent_daily.map((item) => (
                      <li key={item.trade_date}>
                        {item.trade_date}: {formatForeignValue(item.net_buy_qty)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p>최근 3일 외인 동향: -</p>
              )}
              <p>외인 상태: {foreignStatusLabel(detail)}</p>
            </div>
          </SurfaceCard>

          {failedPoints.length > 0 && (
            <SurfaceCard tone="soft">
              <h4>미충족 조건(참고)</h4>
              <ul className="reason-list">
                {failedPoints.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </SurfaceCard>
          )}
        </div>
      )}
    </Drawer>
  );
}
