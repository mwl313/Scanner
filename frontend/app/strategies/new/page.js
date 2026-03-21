"use client";

import { useRouter } from 'next/navigation';

import PageHeader from '../../../components/layout/PageHeader';
import StrategyForm from '../../../components/StrategyForm';
import LoadingState from '../../../components/ui/LoadingState';
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
    return <LoadingState message="전략 생성 화면을 준비하는 중..." />;
  }

  return (
    <div className="page-stack">
      <PageHeader title="New Strategy" subtitle="스캐너 규칙을 저장해 반복 가능한 스캔 템플릿을 만듭니다." />
      <StrategyForm submitLabel="저장" onSubmit={onSubmit} onCancel={() => router.push('/strategies')} />
    </div>
  );
}
