import GradeBadge from '../scans/GradeBadge';
import ScorePill from '../scans/ScorePill';
import StatusChip from '../ui/StatusChip';
import { foreignStatusLabel, formatForeignValue, formatNumber } from '../../lib/formatters';

export default function StockHero({ detail }) {
  return (
    <section className="surface-card stock-hero tone-stock">
      <div className="stock-hero-top">
        <div>
          <p className="kicker">STOCK BRIEF</p>
          <h2>{detail.stock_name}</h2>
          <p className="helper">{detail.stock_code} · {detail.market}</p>
        </div>
        <div className="stock-hero-grade">
          <ScorePill score={detail.score} grade={detail.grade} />
          <GradeBadge grade={detail.grade} />
        </div>
      </div>

      <div className="stock-hero-metrics">
        <div>
          <span className="metric-label">현재가</span>
          <strong>{formatNumber(detail.price)}</strong>
        </div>
        <div>
          <span className="metric-label">거래대금</span>
          <strong>{formatNumber(detail.trading_value)}</strong>
        </div>
        <div>
          <span className="metric-label">외인 동향</span>
          <strong>{formatForeignValue(detail.foreign_net_buy_confirmed_value)}</strong>
        </div>
        <div>
          <span className="metric-label">외인 상태</span>
          <strong>{foreignStatusLabel(detail)}</strong>
        </div>
      </div>

      <div className="row">
        <StatusChip label={`Run #${detail.scan_run_id}`} tone="neutral" />
        <StatusChip label={`전략 ${detail.strategy_id}`} tone="neutral" />
      </div>
    </section>
  );
}
