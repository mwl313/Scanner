"use client";

import { useEffect, useState } from 'react';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

export default function DashboardPage() {
  const { loading } = useRequireAuth();
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!loading) {
      apiRequest('/api/dashboard/summary').then(setSummary).catch(() => {});
    }
  }, [loading]);

  if (loading || !summary) {
    return <p>로딩중...</p>;
  }

  return (
    <div>
      <h2>대시보드</h2>
      <div className="grid-3">
        <div className="card">
          <h4>오늘 스캔 실행</h4>
          <p>{summary.today_scan_runs}회</p>
        </div>
        <div className="card">
          <h4>오늘 매칭 종목</h4>
          <p>{summary.today_matched}개</p>
        </div>
        <div className="card">
          <h4>A등급</h4>
          <p>{summary.today_a_grade_count}개</p>
        </div>
      </div>

      <div className="card">
        <h3>전략별 최근 결과</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>전략</th>
                <th>최근 실행</th>
                <th>상태</th>
                <th>매칭</th>
                <th>A등급</th>
              </tr>
            </thead>
            <tbody>
              {summary.recent_by_strategy.map((item) => (
                <tr key={item.strategy_id}>
                  <td>{item.strategy_name}</td>
                  <td>{item.latest_run_id ?? '-'}</td>
                  <td>{item.latest_run_status ?? '-'}</td>
                  <td>{item.latest_matched}</td>
                  <td>{item.latest_a_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3>스캐너 코어 흐름</h3>
        <p className="helper">전략 설정 → 스캔 실행 → 결과 검토 → 대시보드 복기로 운영하는 scanner-first 버전입니다.</p>
      </div>
    </div>
  );
}
