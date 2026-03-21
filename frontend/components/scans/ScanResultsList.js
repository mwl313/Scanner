import FadeIn from '../ui/FadeIn';
import EmptyState from '../ui/EmptyState';
import ScanResultRow from './ScanResultRow';

export default function ScanResultsList({ items, buildPositivePoints, onOpenDetail, selectedStockCode }) {
  if (items.length === 0) {
    return <EmptyState title="표시할 결과가 없습니다." description="필터 조건을 조정하거나 다른 run을 선택해 보세요." />;
  }

  return (
    <div className="scan-results-list">
      {items.map((item, idx) => (
        <FadeIn key={item.id} delay={Math.min(idx * 14, 110)}>
          <ScanResultRow
            item={item}
            positivePoints={buildPositivePoints(item).slice(0, 3)}
            onOpenDetail={onOpenDetail}
            selected={selectedStockCode === item.stock_code}
          />
        </FadeIn>
      ))}
    </div>
  );
}
