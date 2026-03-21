import FadeIn from '../ui/FadeIn';
import SurfaceCard from '../ui/SurfaceCard';
import MetricCard from '../ui/MetricCard';
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
      <SurfaceCard className="scan-run-summary" tone="soft">
        <div className="scan-run-summary__header">
          <div>
            <p className="kicker">ACTIVE RUN</p>
            <h3>#{run.id} · {strategyName || `전략 ${run.strategy_id}`}</h3>
            <p className="helper">{formatDateTime(run.started_at)} · {run.run_type}</p>
          </div>
          <StatusChip label={run.status} tone={runStatusTone(run.status)} />
        </div>
        <div className="scan-run-summary__metrics">
          <MetricCard title="Scanned" value={run.total_scanned} />
          <MetricCard title="Matched" value={run.total_matched} tone="soft" />
          <MetricCard title="Failed" value={run.failed_count} tone="soft" />
        </div>
      </SurfaceCard>
    </FadeIn>
  );
}
