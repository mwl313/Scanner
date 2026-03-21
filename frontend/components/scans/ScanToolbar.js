import Popover from '../ui/Popover';
import PillButton from '../ui/PillButton';
import GhostButton from '../ui/GhostButton';

export default function ScanToolbar({
  strategies,
  selectedStrategyId,
  onChangeStrategy,
  runs,
  selectedRunId,
  onChangeRun,
  selectedGrades,
  onToggleAllGrades,
  onToggleGrade,
  onRunNow,
  onDownloadCsv,
  canDownload,
  gradeOptions,
}) {
  const allSelected = selectedGrades.length === gradeOptions.length;
  const gradeLabel = allSelected ? '전체 등급' : selectedGrades.length === 0 ? '등급 없음' : selectedGrades.join(', ');

  return (
    <section className="scan-toolbar">
      <div className="scan-toolbar-grid">
        <div>
          <label>전략</label>
          <select value={selectedStrategyId} onChange={(e) => onChangeStrategy(e.target.value)}>
            {strategies.map((strategy) => (
              <option key={strategy.id} value={strategy.id}>
                {strategy.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>스캔 Run</label>
          <select value={selectedRunId} onChange={(e) => onChangeRun(e.target.value)}>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                #{run.id} · {run.status} · matched {run.total_matched}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>등급 필터</label>
          <Popover triggerLabel={gradeLabel} triggerClassName="scan-grade-trigger" panelClassName="scan-grade-panel" ariaLabel="등급 필터 열기">
            <label className="checkbox-option">
              <input type="checkbox" checked={allSelected} onChange={(e) => onToggleAllGrades(e.target.checked)} />
              <span>전체</span>
            </label>
            {gradeOptions.map((grade) => (
              <label className="checkbox-option" key={grade}>
                <input type="checkbox" checked={selectedGrades.includes(grade)} onChange={(e) => onToggleGrade(grade, e.target.checked)} />
                <span>{grade}</span>
              </label>
            ))}
          </Popover>
        </div>
      </div>

      <div className="scan-toolbar-actions">
        <GhostButton onClick={onDownloadCsv} disabled={!canDownload}>
          결과 CSV 다운로드
        </GhostButton>
        <PillButton onClick={onRunNow}>수동 스캔 실행</PillButton>
      </div>
    </section>
  );
}
