import Link from 'next/link';

import { buildTossInvestUrl, formatForeignValue, formatNumber } from '../../lib/formatters';
import GradeBadge from './GradeBadge';
import ScorePill from './ScorePill';
import GhostButton from '../ui/GhostButton';

export default function ScanResultRow({ item, positivePoints, onOpenDetail }) {
  const tossUrl = buildTossInvestUrl(item.stock_code);
  return (
    <article className="scan-row-card">
      <div className="scan-row-main">
        <div className="scan-row-identity">
          <p className="scan-stock-name">{item.stock_name}</p>
          <p className="scan-stock-code">{item.stock_code} · {item.market}</p>
        </div>

        <div className="scan-row-metrics">
          <div>
            <span className="metric-label">현재가</span>
            <strong>{formatNumber(item.price)}</strong>
          </div>
          <div>
            <span className="metric-label">거래대금</span>
            <strong>{formatNumber(item.trading_value)}</strong>
          </div>
          <div>
            <span className="metric-label">외인 확정합</span>
            <strong>{formatForeignValue(item.foreign_net_buy_confirmed_value)}</strong>
          </div>
        </div>
      </div>

      <div className="scan-row-points">
        <p className="metric-label">긍정 포인트</p>
        <ul>
          {positivePoints.map((point, idx) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </div>

      <div className="scan-row-side">
        <ScorePill score={item.score} />
        <GradeBadge grade={item.grade} />
        <div className="scan-row-actions">
          <GhostButton onClick={() => onOpenDetail(item.stock_code)}>상세</GhostButton>
          {tossUrl ? (
            <a className="btn btn-ghost" href={tossUrl} target="_blank" rel="noopener noreferrer">
              Toss
            </a>
          ) : (
            <button className="btn btn-ghost" disabled>
              Toss
            </button>
          )}
          <Link className="btn btn-ghost" href={`/stocks/${item.stock_code}`}>
            종목 페이지
          </Link>
        </div>
      </div>
    </article>
  );
}
