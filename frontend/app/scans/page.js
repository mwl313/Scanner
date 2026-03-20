"use client";

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

const MANDATORY_FAIL_PATTERNS = [
  'RSI 조건 미충족',
  '가격 vs MA20 미충족',
  'MA5 vs MA20 미충족',
  'MA20 vs MA60 미충족',
  '거래대금 기준 미달',
  '시장 필터 미충족',
  '시가총액 조건 미충족',
];

function compactReason(reason) {
  if (!reason) return '';
  if (reason.includes('RSI 상향 돌파 + 목표구간')) return 'RSI 조건 충족';
  if (reason.includes('볼린저 하단 근접')) return '볼밴 하단근접';
  if (reason.includes('가격 vs MA20 충족')) return '가격vsMA20';
  if (reason.includes('MA5 vs MA20 충족')) return 'MA5vsMA20';
  if (reason.includes('MA20 vs MA60 충족')) return 'MA20vsMA60';
  if (reason.includes('외국인 최근')) return '외인 순매수';
  if (reason.includes('외인 확정 데이터 없음')) return '외인 중립';
  if (reason.includes('외인 데이터 미확보지만')) return '외인 정책통과';
  if (reason.includes('시가총액 기준 통과')) return '시가총액 통과';
  if (reason.includes('거래대금 기준 통과')) return '거래대금 통과';
  return reason;
}

function maStatus(item) {
  const aboveMa20 = Number(item.price) >= Number(item.ma20);
  const ma5Above20 = Number(item.ma5) >= Number(item.ma20);
  if (aboveMa20 && ma5Above20) return '상승 유지';
  if (aboveMa20) return 'MA20 위';
  if ((Number(item.ma20) - Number(item.price)) / Number(item.ma20) <= 0.02) return 'MA20 근처';
  return '약세';
}

function formatForeignValue(value) {
  if (value === null || value === undefined) return '-';
  return Number(value).toLocaleString();
}

function foreignStatusLabel(item) {
  if (item.foreign_data_status === 'confirmed') {
    return (item.foreign_data_source || '').includes('krx_confirmed_daily') ? '확정(KRX)' : '확정';
  }
  if (item.foreign_net_buy_snapshot_value !== null && item.foreign_net_buy_snapshot_value !== undefined) {
    return '미확정(스냅샷)';
  }
  return '없음';
}

export default function ScansPage() {
  const { loading } = useRequireAuth();
  const [strategies, setStrategies] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState('');
  const [selectedRunId, setSelectedRunId] = useState('');
  const [results, setResults] = useState([]);
  const [gradeFilter, setGradeFilter] = useState('AB');
  const [sortBy, setSortBy] = useState('score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [error, setError] = useState('');

  const loadBase = async () => {
    const [strategyItems, runItems] = await Promise.all([
      apiRequest('/api/strategies'),
      apiRequest('/api/scans'),
    ]);
    setStrategies(strategyItems);
    setRuns(runItems);
    if (!selectedStrategyId && strategyItems.length > 0) {
      setSelectedStrategyId(String(strategyItems[0].id));
    }
    if (!selectedRunId && runItems.length > 0) {
      setSelectedRunId(String(runItems[0].id));
    }
  };

  const loadResults = async () => {
    if (!selectedRunId) {
      setResults([]);
      return;
    }
    const query = new URLSearchParams({
      sort_by: sortBy,
      sort_order: sortOrder,
    });
    if (gradeFilter) query.set('grade', gradeFilter);
    const data = await apiRequest(`/api/scans/${selectedRunId}/results?${query.toString()}`);
    setResults(data || []);
  };

  useEffect(() => {
    if (!loading) {
      loadBase().catch((err) => setError(err.message));
    }
  }, [loading]);

  useEffect(() => {
    if (!loading) {
      loadResults().catch((err) => setError(err.message));
    }
  }, [loading, selectedRunId, gradeFilter, sortBy, sortOrder]);

  const runScanNow = async () => {
    setError('');
    await apiRequest('/api/scans/run', {
      method: 'POST',
      body: JSON.stringify({ strategy_id: Number(selectedStrategyId), run_type: 'manual' }),
    });
    await loadBase();
  };

  const runMap = useMemo(() => {
    const map = {};
    runs.forEach((run) => {
      map[run.id] = run;
    });
    return map;
  }, [runs]);

  if (loading) return <p>로딩중...</p>;

  return (
    <div>
      <h2>스캔 결과</h2>

      <div className="card">
        <div className="row">
          <div style={{ minWidth: 240 }}>
            <label>전략 선택</label>
            <select value={selectedStrategyId} onChange={(e) => setSelectedStrategyId(e.target.value)}>
              {strategies.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <button onClick={runScanNow}>수동 스캔 실행</button>
        </div>
      </div>

      <div className="card">
        <h3>스캔 실행 기록</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>선택</th>
                <th>ID</th>
                <th>전략ID</th>
                <th>상태</th>
                <th>실행유형</th>
                <th>매칭수</th>
                <th>실패수</th>
                <th>시작시각</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td>
                    <input
                      type="radio"
                      checked={String(run.id) === selectedRunId}
                      onChange={() => setSelectedRunId(String(run.id))}
                    />
                  </td>
                  <td>{run.id}</td>
                  <td>{run.strategy_id}</td>
                  <td>{run.status}</td>
                  <td>{run.run_type}</td>
                  <td>{run.total_matched}</td>
                  <td>{run.failed_count}</td>
                  <td>{new Date(run.started_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="row">
          <div>
            <label>등급 필터</label>
            <select value={gradeFilter} onChange={(e) => setGradeFilter(e.target.value)}>
              <option value="AB">A/B (기본)</option>
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="">전체</option>
              <option value="EXCLUDED">EXCLUDED</option>
            </select>
          </div>
          <div>
            <label>정렬 기준</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="score">점수</option>
              <option value="trading_value">거래대금</option>
              <option value="rsi">RSI</option>
              <option value="foreign_net_buy">외인 순매수</option>
              <option value="created_at">생성시각</option>
            </select>
          </div>
          <div>
            <label>정렬 방향</label>
            <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
              <option value="desc">내림차순</option>
              <option value="asc">오름차순</option>
            </select>
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        <div className="table-wrap" style={{ marginTop: 10 }}>
          <table className="scan-result-table">
            <thead>
              <tr>
                <th>종목명</th>
                <th>코드</th>
                <th>가격</th>
                <th>RSI</th>
                <th>RSI Signal</th>
                <th>MA 상태</th>
                <th>볼밴 하단 거리</th>
                <th>외인 확정합</th>
                <th>장중 스냅샷</th>
                <th>외인 상태</th>
                <th>거래대금</th>
                <th>점수</th>
                <th>등급</th>
                <th>필수조건</th>
                <th className="reason-col">통과 이유</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {results.map((item) => {
                const bbDistance = ((Number(item.price) - Number(item.bb_lower)) / Number(item.bb_lower)) * 100;
                const mandatoryFailed = (item.failed_reasons_json || []).some((reason) =>
                  MANDATORY_FAIL_PATTERNS.some((pattern) => reason.includes(pattern))
                );
                const keyReasons = (item.matched_reasons_json || []).slice(0, 4).map(compactReason);
                return (
                  <tr key={item.id}>
                    <td>{item.stock_name}</td>
                    <td>{item.stock_code}</td>
                    <td>{Number(item.price).toLocaleString()}</td>
                    <td>{Number(item.rsi).toFixed(2)}</td>
                    <td>{Number(item.rsi_signal).toFixed(2)}</td>
                    <td>{maStatus(item)}</td>
                    <td>{bbDistance.toFixed(2)}%</td>
                    <td>{formatForeignValue(item.foreign_net_buy_confirmed_value)}</td>
                    <td>{formatForeignValue(item.foreign_net_buy_snapshot_value)}</td>
                    <td title={item.foreign_data_source || ''}>{foreignStatusLabel(item)}</td>
                    <td>{Number(item.trading_value).toLocaleString()}</td>
                    <td>{item.score}</td>
                    <td><span className={`badge ${item.grade}`}>{item.grade}</span></td>
                    <td>
                      <span className={`badge ${mandatoryFailed ? 'EXCLUDED' : 'A'}`}>
                        {mandatoryFailed ? '미충족' : '통과'}
                      </span>
                    </td>
                    <td className="reason-col">{keyReasons.join(' · ')}</td>
                    <td>
                      <Link href={`/stocks/${item.stock_code}`}>상세</Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {selectedRunId && runMap[selectedRunId] && (
          <p className="helper" style={{ marginTop: 8 }}>
            현재 run {selectedRunId}: scanned={runMap[selectedRunId].total_scanned}, matched={runMap[selectedRunId].total_matched}, failed={runMap[selectedRunId].failed_count}
          </p>
        )}
      </div>
    </div>
  );
}
