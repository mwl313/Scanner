"use client";

import { formatDateTimeCompact } from '../../lib/formatters';

export default function ProfileScanRow({ run, strategyName, onOpen }) {
  return (
    <button
      type="button"
      className="profile-scan-row"
      onClick={() => onOpen(run.id)}
      aria-label={`Run #${run.id} 열기`}
    >
      <span className="profile-scan-cell profile-scan-id">Run #{run.id}</span>
      <span className="profile-scan-cell profile-scan-strategy">{strategyName || '-'}</span>
      <span className="profile-scan-cell profile-scan-date">{formatDateTimeCompact(run.started_at)}</span>
    </button>
  );
}
