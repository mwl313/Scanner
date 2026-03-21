import { formatNumber } from '../../lib/formatters';

export default function MiniPriceChart({ values = [] }) {
  if (!values.length) {
    return <p className="helper">최근 종가 데이터가 없습니다.</p>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const latest = values[values.length - 1];

  return (
    <div className="mini-chart-panel">
      <div className="mini-chart-bars" aria-label="최근 종가 시각화">
        {values.map((value, idx) => {
          const ratio = max > min ? (value - min) / (max - min) : 0.5;
          const height = Math.max(14, ratio * 100);
          return (
            <span
              className="mini-bar"
              key={`${idx}-${value}`}
              title={formatNumber(value)}
              style={{ height: `${height}%` }}
            />
          );
        })}
      </div>
      <div className="mini-chart-meta">
        <p><span>최저</span><strong>{formatNumber(min)}</strong></p>
        <p><span>최신</span><strong>{formatNumber(latest)}</strong></p>
        <p><span>최고</span><strong>{formatNumber(max)}</strong></p>
      </div>
    </div>
  );
}
