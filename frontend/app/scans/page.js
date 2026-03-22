"use client";

import { useEffect, useMemo, useState } from 'react';

import PageHeader from '../../components/layout/PageHeader';
import ScanResultDetailDrawer from '../../components/scans/ScanResultDetailDrawer';
import ScanResultsList from '../../components/scans/ScanResultsList';
import ScanRunSummary from '../../components/scans/ScanRunSummary';
import ScanToolbar from '../../components/scans/ScanToolbar';
import EmptyState from '../../components/ui/EmptyState';
import LoadingState from '../../components/ui/LoadingState';
import SurfaceCard from '../../components/ui/SurfaceCard';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';
import { buildCsvFilename, convertScanResultsToCsv, downloadCsv } from '../../lib/csv';
import { buildPositivePoints, formatScanRunLabel } from '../../lib/formatters';

const GRADE_OPTIONS = ['A', 'B', 'C', 'EXCLUDED'];

export default function ScansPage() {
  const { loading } = useRequireAuth();
  const [strategies, setStrategies] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState('');
  const [selectedRunId, setSelectedRunId] = useState('');
  const [results, setResults] = useState([]);
  const [selectedGrades, setSelectedGrades] = useState(['A', 'B']);
  const [error, setError] = useState('');
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [detail, setDetail] = useState(null);
  const [selectedStockCode, setSelectedStockCode] = useState('');
  const [isRunningScan, setIsRunningScan] = useState(false);

  const loadBase = async () => {
    const [strategyItems, runItems] = await Promise.all([apiRequest('/api/strategies'), apiRequest('/api/scans')]);
    setStrategies(strategyItems || []);
    setRuns(runItems || []);
    const strategyIds = new Set((strategyItems || []).map((item) => String(item.id)));
    const runIds = new Set((runItems || []).map((item) => String(item.id)));

    if (strategyItems?.length > 0) {
      if (!selectedStrategyId || !strategyIds.has(String(selectedStrategyId))) {
        setSelectedStrategyId(String(strategyItems[0].id));
      }
    } else if (selectedStrategyId) {
      setSelectedStrategyId('');
    }

    if (runItems?.length > 0) {
      const deepLinkRunId = typeof window !== 'undefined'
        ? new URLSearchParams(window.location.search).get('runId')
        : null;
      const normalizedDeepLinkRunId = deepLinkRunId && /^\d+$/.test(deepLinkRunId) ? deepLinkRunId : '';

      if (normalizedDeepLinkRunId && runIds.has(normalizedDeepLinkRunId)) {
        setSelectedRunId(normalizedDeepLinkRunId);
      } else if (!selectedRunId || !runIds.has(String(selectedRunId))) {
        setSelectedRunId(String(runItems[0].id));
      }
    } else if (selectedRunId) {
      setSelectedRunId('');
    }
  };

  const loadResults = async () => {
    if (!selectedRunId) {
      setResults([]);
      return;
    }
    const query = new URLSearchParams({ sort_by: 'score', sort_order: 'desc' });
    const data = await apiRequest(`/api/scans/${selectedRunId}/results?${query.toString()}`);
    setResults(data || []);
  };

  useEffect(() => {
    if (!loading) loadBase().catch((err) => setError(err.message));
  }, [loading]);

  useEffect(() => {
    if (!loading) loadResults().catch((err) => setError(err.message));
  }, [loading, selectedRunId]);

  useEffect(() => {
    if (loading) return undefined;
    const hasRunningRun = runs.some((item) => item.status === 'running');
    if (!hasRunningRun) return undefined;

    const interval = window.setInterval(() => {
      loadBase().catch((err) => setError(err.message));
      if (selectedRunId) {
        loadResults().catch((err) => setError(err.message));
      }
    }, 5000);

    return () => window.clearInterval(interval);
  }, [loading, runs, selectedRunId]);

  useEffect(() => {
    setSelectedStockCode('');
  }, [selectedRunId]);

  const runScanNow = async () => {
    if (!selectedStrategyId || isRunningScan) return;
    setError('');
    setIsRunningScan(true);
    try {
      await apiRequest('/api/scans/run', {
        method: 'POST',
        body: JSON.stringify({ strategy_id: Number(selectedStrategyId), run_type: 'manual' }),
      });
      await new Promise((resolve) => setTimeout(resolve, 300));
      await loadBase();
      if (selectedRunId) {
        await loadResults();
      }
    } catch (err) {
      setError(err.message || '수동 스캔 실행에 실패했습니다.');
    } finally {
      setIsRunningScan(false);
    }
  };

  const deleteSelectedRun = async () => {
    if (!selectedRunId) return;
    if (!window.confirm(`Run #${selectedRunId}를 삭제할까요? 이 작업은 되돌릴 수 없습니다.`)) return;

    setError('');
    await apiRequest(`/api/scans/${selectedRunId}`, { method: 'DELETE' });
    setResults([]);
    setDetailOpen(false);
    setDetail(null);
    setDetailError('');
    setDetailLoading(false);
    setSelectedStockCode('');
    await loadBase();
  };

  const runMap = useMemo(() => {
    const map = {};
    runs.forEach((run) => {
      map[run.id] = run;
    });
    return map;
  }, [runs]);

  const strategyMap = useMemo(() => {
    const map = {};
    strategies.forEach((item) => {
      map[item.id] = item;
    });
    return map;
  }, [strategies]);

  const selectedRun = selectedRunId ? runMap[Number(selectedRunId)] || runMap[selectedRunId] : null;
  const selectedStrategy = selectedStrategyId ? strategyMap[Number(selectedStrategyId)] || strategyMap[selectedStrategyId] : null;

  const filteredResults = useMemo(() => {
    const ordered = [...results].sort((a, b) => Number(b.score) - Number(a.score));
    if (selectedGrades.length === 0) return [];
    return ordered.filter((item) => selectedGrades.includes(item.grade));
  }, [results, selectedGrades]);

  const toggleAllGrades = (checked) => {
    setSelectedGrades(checked ? [...GRADE_OPTIONS] : []);
  };

  const toggleGrade = (grade, checked) => {
    setSelectedGrades((prev) => {
      if (checked) return prev.includes(grade) ? prev : [...prev, grade];
      return prev.filter((item) => item !== grade);
    });
  };

  const openDetail = async (stockCode) => {
    setSelectedStockCode(stockCode);
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailError('');
    setDetail(null);
    try {
      const data = await apiRequest(`/api/stocks/${stockCode}`);
      setDetail(data);
    } catch (err) {
      setDetailError(err.message || '상세 정보를 불러오지 못했습니다.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDownloadCsv = () => {
    if (filteredResults.length === 0) return;
    const rowsForExport = filteredResults.map((item) => ({
      ...item,
      status: item.grade === 'EXCLUDED' ? '제외' : '통과',
      positive_points: buildPositivePoints(item).join(' | '),
    }));
    const csvText = convertScanResultsToCsv(rowsForExport);
    downloadCsv(csvText, buildCsvFilename('scan-results'));
  };

  if (loading) return <LoadingState message="스캔 콘솔을 준비하는 중..." />;

  return (
    <div className="page-stack">
      <PageHeader title="Scan Console" subtitle="활성 전략의 실행 Run을 선택하고 후보 종목 브리프를 빠르게 검토할 수 있습니다." />

      <ScanToolbar
        strategies={strategies}
        selectedStrategyId={selectedStrategyId}
        onChangeStrategy={setSelectedStrategyId}
        runs={runs}
        selectedRunId={selectedRunId}
        onChangeRun={setSelectedRunId}
        selectedGrades={selectedGrades}
        onToggleAllGrades={toggleAllGrades}
        onToggleGrade={toggleGrade}
        onRunNow={runScanNow}
        onDeleteRun={deleteSelectedRun}
        onDownloadCsv={handleDownloadCsv}
        canDownload={filteredResults.length > 0}
        canDeleteRun={Boolean(selectedRunId)}
        gradeOptions={GRADE_OPTIONS}
        formatRunLabel={formatScanRunLabel}
        isRunningScan={isRunningScan}
        canRunNow={Boolean(selectedStrategyId)}
      />

      {error && <SurfaceCard className="error-block"><p className="error">{error}</p></SurfaceCard>}

      <ScanRunSummary run={selectedRun} strategyName={selectedStrategy?.name} />

      <SurfaceCard className="results-console" tone="soft">
        <div className="panel-header">
          <h3>결과 브리프</h3>
          <div className="scan-summary-chips">
            <span className="status-chip status-chip--neutral">정렬: 점수 높은 순</span>
            <span className="status-chip status-chip--neutral">표시 {filteredResults.length}건</span>
          </div>
        </div>
        {!selectedRunId ? (
          <EmptyState title="선택된 run이 없습니다." description="스캔 실행 기록에서 run을 선택해 주세요." />
        ) : (
          <ScanResultsList
            items={filteredResults}
            buildPositivePoints={buildPositivePoints}
            onOpenDetail={openDetail}
            selectedStockCode={selectedStockCode}
          />
        )}
      </SurfaceCard>

      <ScanResultDetailDrawer
        open={detailOpen}
        onClose={() => {
          setDetailOpen(false);
          setDetail(null);
          setDetailError('');
          setDetailLoading(false);
          setSelectedStockCode('');
        }}
        loading={detailLoading}
        error={detailError}
        detail={detail}
      />
    </div>
  );
}
