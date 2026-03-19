"use client";

import { useRequireAuth } from '../../lib/auth';

export default function JournalsPage() {
  const { loading } = useRequireAuth();
  if (loading) return <p>로딩중...</p>;

  return (
    <div className="card">
      <h2>매매일지</h2>
      <p className="helper">이 기능은 현재 임시 비활성화되었습니다.</p>
    </div>
  );
}
