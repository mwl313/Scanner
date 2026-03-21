import SurfaceCard from './SurfaceCard';

export default function MetricCard({ title, value, hint, tone = 'default' }) {
  return (
    <SurfaceCard className={`metric-card metric-card--${tone}`}>
      <p className="metric-card__title">{title}</p>
      <p className="metric-card__value">{value}</p>
      {hint && <p className="metric-card__hint">{hint}</p>}
    </SurfaceCard>
  );
}
