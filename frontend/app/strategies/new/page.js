"use client";

import { useRouter } from 'next/navigation';
import StrategyForm from '../../../components/StrategyForm';
import { useRequireAuth } from '../../../lib/auth';
import { apiRequest } from '../../../lib/api';

export default function NewStrategyPage() {
  const { loading } = useRequireAuth();
  const router = useRouter();

  const onSubmit = async (form) => {
    await apiRequest('/api/strategies', {
      method: 'POST',
      body: JSON.stringify(form),
    });
    router.push('/strategies');
  };

  if (loading) {
    return <p>로딩중...</p>;
  }

  return (
    <div>
      <h2>전략 생성</h2>
      <StrategyForm submitLabel="저장" onSubmit={onSubmit} />
    </div>
  );
}
