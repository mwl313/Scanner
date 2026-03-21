import FadeIn from '../ui/FadeIn';
import SurfaceCard from '../ui/SurfaceCard';
import StatusChip from '../ui/StatusChip';
import { formatDateTime } from '../../lib/formatters';

function runStatusTone(status) {
  if (!status) return 'neutral';
  if (status.includes('completed')) return 'bull';
  if (status.includes('failed')) return 'bear';
  return 'neutral';
}

export default function ScanRunSummary({ run, strategyName }) {
  if (!run) return null;
  return (
    <FadeIn delay={50}>
      <SurfaceCard className="scan-run-summary scan-run-summary--compact" tone="soft">
        <div className="scan-run-summary__header">
          <div className="scan-run-summary__title-wrap">
            <div>
              <p className="kicker">ACTIVE RUN</p>
              <h3>#{run.id} · {strategyName || `전략 ${run.strategy_id}`}</h3>
              <p className="helper">{formatDateTime(run.started_at)} · {run.run_type}</p>
            </div>
            <div className="scan-run-summary__stats">
              <span className="status-chip status-chip--neutral">Scanned {run.total_scanned}</span>
              <span className="status-chip status-chip--neutral">Matched {run.total_matched}</span>
              <span className="status-chip status-chip--neutral">Failed {run.failed_count}</span>
            </div>
          </div>
          <StatusChip label={run.status} tone={runStatusTone(run.status)} />
        </div>
      </SurfaceCard>
    </FadeIn>
  );
}
