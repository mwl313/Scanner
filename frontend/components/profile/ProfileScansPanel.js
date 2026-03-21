"use client";

import SurfaceCard from '../ui/SurfaceCard';
import EmptyState from '../ui/EmptyState';
import ProfileScanRow from './ProfileScanRow';

export default function ProfileScansPanel({ runs, strategyById, onOpenRun }) {
  return (
    <SurfaceCard className="panel profile-panel profile-scans-panel" tone="soft">
      <div className="panel-header">
        <div>
          <h3>스캔 기록</h3>
          <p className="helper">지금까지 실행한 스캔을 확인하고 다시 열 수 있습니다.</p>
        </div>
      </div>

      {runs.length === 0 ? (
        <EmptyState title="스캔 이력이 없습니다." description="스캔 콘솔에서 수동 스캔을 실행해 주세요." />
      ) : (
        <div className="profile-scans-table-wrap">
          <div className="profile-scans-head" role="row">
            <span>스캔 번호</span>
            <span>사용 전략명</span>
            <span>스캔 날짜/시간</span>
          </div>
          <div className="profile-scans-body">
            {runs.map((run) => (
              <ProfileScanRow
                key={run.id}
                run={run}
                strategyName={strategyById[run.strategy_id]?.name}
                onOpen={onOpenRun}
              />
            ))}
          </div>
        </div>
      )}
    </SurfaceCard>
  );
}
