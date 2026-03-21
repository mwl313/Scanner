import { buildTossInvestUrl, formatForeignValue, formatNumber } from '../../lib/formatters';
import GradeBadge from './GradeBadge';
import ScorePill from './ScorePill';
import GhostButton from '../ui/GhostButton';

export default function ScanResultRow({ item, positivePoints, onOpenDetail, selected = false }) {
  const tossUrl = buildTossInvestUrl(item.stock_code);
  return (
    <article className={`scan-row-card ${selected ? 'is-selected' : ''}`.trim()}>
      <div className="scan-row-main">
        <div className="scan-row-identity">
          <p className="scan-stock-name">{item.stock_name}</p>
          <p className="scan-stock-code">{item.stock_code} · {item.market}</p>
        </div>
        <div className="scan-row-signal">
          <ScorePill score={item.score} grade={item.grade} />
          <GradeBadge grade={item.grade} />
        </div>
      </div>

      <div className="scan-row-key-metrics">
        <div className="scan-row-key-item">
          <span className="metric-label">현재가</span>
          <strong>{formatNumber(item.price)}</strong>
        </div>
        <div className="scan-row-key-item">
          <span className="metric-label">외인 확정합</span>
          <strong>{formatForeignValue(item.foreign_net_buy_confirmed_value)}</strong>
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
        <div className="scan-row-actions scan-row-actions--stack">
          <GhostButton className="scan-action-btn scan-action-btn--detail" onClick={() => onOpenDetail(item.stock_code)}>상세</GhostButton>
          {tossUrl ? (
            <a className="btn btn-ghost scan-action-btn scan-action-btn--toss" href={tossUrl} target="_blank" rel="noopener noreferrer">
              Toss
            </a>
          ) : (
            <button className="btn btn-ghost scan-action-btn scan-action-btn--toss" disabled>
              Toss
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
