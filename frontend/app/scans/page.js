"use client";

import { useEffect, useMemo, useState } from 'react';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

const GRADE_OPTIONS = ['A', 'B', 'C', 'EXCLUDED'];

function reasonToPlainKorean(reason) {
  if (!reason) return '';
  if (reason.includes('RSI 상향 돌파 + 목표구간')) {
    return 'RSI가 최근 조건에서 상향 돌파했고 목표 구간을 유지하고 있습니다.';
  }
  if (reason.includes('볼린저 하단 근접')) {
    return '볼린저 하단 부근이라 눌림 구간으로 볼 수 있습니다.';
  }
  if (reason.includes('가격 vs MA20 충족')) {
    return '현재가가 20일선 위이거나 근처에서 버티고 있습니다.';
  }
  if (reason.includes('MA5 vs MA20 충족')) {
    return '단기 흐름(MA5)이 20일선 대비 회복된 상태입니다.';
  }
  if (reason.includes('MA20 vs MA60 충족')) {
    return '중기 흐름(MA20)이 장기 흐름(MA60)보다 강합니다.';
  }
  if (reason.includes('외국인 최근')) {
    const match = reason.match(/외국인 최근\s+(\d+)일/);
    const days = match ? match[1] : 'N';
    return `최근 ${days}일 외국인 확정 순매수가 양수입니다.`;
  }
  if (reason.includes('외인 확정 데이터 없음(중립 처리)')) {
    return '외국인 확정 데이터가 없어 이 항목은 중립 처리되었습니다.';
  }
  if (reason.includes('외인 데이터 미확보지만 정책상 통과')) {
    return '외국인 데이터가 없지만 현재 전략 설정상 통과로 처리됩니다.';
  }
  if (reason.includes('시가총액 기준 통과')) {
    return '시가총액이 전략 최소 기준 이상입니다.';
  }
  if (reason.includes('거래대금 기준 통과')) {
    return '거래대금이 전략 최소 기준 이상입니다.';
  }
  return reason;
}

function failReasonToPlainKorean(reason) {
  if (!reason) return '';
  if (reason.includes('RSI 조건 미충족')) return 'RSI 상향 돌파 또는 목표 구간 조건을 만족하지 못했습니다.';
  if (reason.includes('볼린저 하단 근접 미충족')) return '볼린저 하단 부근 조건을 만족하지 못했습니다.';
  if (reason.includes('가격 vs MA20 미충족')) return '현재가가 20일선 기준 조건을 만족하지 못했습니다.';
  if (reason.includes('MA5 vs MA20 미충족')) return '단기 흐름(MA5)이 MA20 조건을 만족하지 못했습니다.';
  if (reason.includes('MA20 vs MA60 미충족')) return '중기 흐름(MA20)이 MA60 대비 조건을 만족하지 못했습니다.';
  if (reason.includes('외국인 확정 순매수 조건 미충족')) return '외국인 최근 확정 순매수 조건이 충족되지 않았습니다.';
  if (reason.includes('외인 데이터 미확보(실패 정책)')) return '외국인 데이터가 없어 전략 설정상 실패 처리되었습니다.';
  if (reason.includes('시가총액 조건 미충족')) return '시가총액이 전략 최소 기준보다 낮습니다.';
  if (reason.includes('거래대금 기준 미달')) return '거래대금이 전략 최소 기준보다 낮습니다.';
  if (reason.includes('시장 필터 미충족')) return '현재 전략 시장 필터와 종목 시장이 맞지 않습니다.';
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

function buildTossInvestUrl(stockCode) {
  if (stockCode === null || stockCode === undefined) return null;
  const code = String(stockCode).trim();
  if (!/^\d{6}$/.test(code)) return null;
  return `https://www.tossinvest.com/stocks/A${code}/order`;
}

function buildPositivePoints(item) {
  const plainReasons = (item.matched_reasons_json || []).map(reasonToPlainKorean).filter(Boolean);
  if (plainReasons.length === 0) {
    return ['긍정 포인트 정보가 없습니다.'];
  }
  return plainReasons;
}

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
      sort_by: 'score',
      sort_order: 'desc',
    });
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
  }, [loading, selectedRunId]);

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

  const allGradesSelected = selectedGrades.length === GRADE_OPTIONS.length;

  const gradeFilterLabel = useMemo(() => {
    if (allGradesSelected) return '전체';
    if (selectedGrades.length === 0) return '선택 없음';
    return selectedGrades.join(', ');
  }, [allGradesSelected, selectedGrades]);

  const toggleAllGrades = (checked) => {
    setSelectedGrades(checked ? [...GRADE_OPTIONS] : []);
  };

  const toggleGrade = (grade, checked) => {
    setSelectedGrades((prev) => {
      if (checked) {
        return prev.includes(grade) ? prev : [...prev, grade];
      }
      return prev.filter((item) => item !== grade);
    });
  };

  const filteredResults = useMemo(() => {
    const ordered = [...results].sort((a, b) => Number(b.score) - Number(a.score));
    if (selectedGrades.length === 0) return [];
    return ordered.filter((item) => selectedGrades.includes(item.grade));
  }, [results, selectedGrades]);

  const detailTossUrl = buildTossInvestUrl(detail?.stock_code);

  const openDetail = async (stockCode) => {
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

  const closeDetail = () => {
    setDetailOpen(false);
    setDetail(null);
    setDetailError('');
    setDetailLoading(false);
  };

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
          <div className="filter-dropdown">
            <label>등급 필터</label>
            <details>
              <summary>{gradeFilterLabel}</summary>
              <div className="dropdown-panel">
                <label className="checkbox-option">
                  <input
                    type="checkbox"
                    checked={allGradesSelected}
                    onChange={(e) => toggleAllGrades(e.target.checked)}
                  />
                  <span>전체</span>
                </label>
                {GRADE_OPTIONS.map((grade) => (
                  <label className="checkbox-option" key={grade}>
                    <input
                      type="checkbox"
                      checked={selectedGrades.includes(grade)}
                      onChange={(e) => toggleGrade(grade, e.target.checked)}
                    />
                    <span>{grade}</span>
                  </label>
                ))}
              </div>
            </details>
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        <div className="table-wrap" style={{ marginTop: 10 }}>
          <table className="scan-result-table scan-result-compact">
            <thead>
              <tr>
                <th>종목명</th>
                <th>코드</th>
                <th>가격</th>
                <th>점수</th>
                <th>등급</th>
                <th className="reason-col">긍정 포인트</th>
                <th>상세</th>
              </tr>
            </thead>
            <tbody>
              {filteredResults.map((item) => {
                const positivePoints = buildPositivePoints(item).slice(0, 2);
                const tossUrl = buildTossInvestUrl(item.stock_code);
                return (
                  <tr key={item.id}>
                    <td>{item.stock_name}</td>
                    <td style={{ fontFamily: 'monospace' }}>{item.stock_code}</td>
                    <td>{Number(item.price).toLocaleString()}</td>
                    <td>{item.score}</td>
                    <td><span className={`badge ${item.grade}`}>{item.grade}</span></td>
                    <td className="reason-col">
                      <ul className="reason-list compact">
                        {positivePoints.map((point, idx) => (
                          <li key={idx}>{point}</li>
                        ))}
                      </ul>
                    </td>
                    <td>
                      <div className="action-group">
                        <button className="secondary" onClick={() => openDetail(item.stock_code)}>상세</button>
                        {tossUrl ? (
                          <a
                            className="button-link secondary"
                            href={tossUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Toss
                          </a>
                        ) : (
                          <button className="secondary" disabled>Toss</button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {filteredResults.length === 0 && (
                <tr>
                  <td colSpan={7} className="helper">선택한 등급에 해당하는 결과가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {selectedRunId && runMap[selectedRunId] && (
          <p className="helper" style={{ marginTop: 8 }}>
            현재 run {selectedRunId}: scanned={runMap[selectedRunId].total_scanned}, matched={runMap[selectedRunId].total_matched}, failed={runMap[selectedRunId].failed_count}
          </p>
        )}
      </div>

      {detailOpen && (
        <div className="detail-overlay" onClick={closeDetail}>
          <aside className="detail-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0 }}>종목 상세</h3>
              <div className="action-group">
                {detailTossUrl ? (
                  <a
                    className="button-link secondary"
                    href={detailTossUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Toss
                  </a>
                ) : (
                  <button className="secondary" disabled>Toss</button>
                )}
                <button className="secondary" onClick={closeDetail}>닫기</button>
              </div>
            </div>

            {detailLoading && <p style={{ marginTop: 12 }}>상세 정보를 불러오는 중...</p>}
            {detailError && <p className="error" style={{ marginTop: 12 }}>{detailError}</p>}

            {!detailLoading && !detailError && detail && (
              <div style={{ marginTop: 12 }}>
                <div className="card">
                  <h3 style={{ marginTop: 0, marginBottom: 6 }}>{detail.stock_name}</h3>
                  <p className="helper" style={{ marginTop: 0 }}>
                    {detail.stock_code} · {detail.market}
                  </p>
                  <div className="row" style={{ justifyContent: 'space-between', marginTop: 8 }}>
                    <div>
                      <label>현재가</label>
                      <p style={{ marginTop: 4 }}>{Number(detail.price).toLocaleString()}</p>
                    </div>
                    <div>
                      <label>점수</label>
                      <p style={{ marginTop: 4 }}>{detail.score}</p>
                    </div>
                    <div>
                      <label>등급</label>
                      <p style={{ marginTop: 4 }}><span className={`badge ${detail.grade}`}>{detail.grade}</span></p>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h4 style={{ marginTop: 0 }}>긍정 포인트</h4>
                  <ul className="reason-list" style={{ marginTop: 8 }}>
                    {((detail.matched_reasons || []).map(reasonToPlainKorean).filter(Boolean)).map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                </div>

                <div className="card">
                  <h4 style={{ marginTop: 0 }}>상세 지표</h4>
                  <div className="grid-2">
                    <p>가격: {Number(detail.price).toLocaleString()}</p>
                    <p>거래대금: {Number(detail.trading_value).toLocaleString()}</p>
                    <p>MA 상태: {maStatus(detail)}</p>
                    <p>
                      볼린저 하단 거리: {(
                        ((Number(detail.price) - Number(detail.bb_lower)) / Number(detail.bb_lower)) * 100
                      ).toFixed(2)}%
                    </p>
                    <p>외인 확정합: {formatForeignValue(detail.foreign_net_buy_confirmed_value)}</p>
                    <p>장중 스냅샷: {formatForeignValue(detail.foreign_net_buy_snapshot_value)}</p>
                    <p>외인 상태: {foreignStatusLabel(detail)}</p>
                    <p>RSI / Signal: {Number(detail.rsi).toFixed(2)} / {Number(detail.rsi_signal).toFixed(2)}</p>
                  </div>
                </div>

                {(detail.failed_reasons || []).length > 0 && (
                  <div className="card">
                    <h4 style={{ marginTop: 0 }}>미충족 조건(참고)</h4>
                    <ul style={{ marginTop: 8 }}>
                      {detail.failed_reasons.map((reason, idx) => (
                        <li key={idx}>{failReasonToPlainKorean(reason)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
