"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

import PageHeader from '../../../../components/layout/PageHeader';
import StrategyForm from '../../../../components/StrategyForm';
import LoadingState from '../../../../components/ui/LoadingState';
import EmptyState from '../../../../components/ui/EmptyState';
import { useRequireAuth } from '../../../../lib/auth';
import { apiRequest } from '../../../../lib/api';

export default function EditStrategyPage() {
  const { loading } = useRequireAuth();
  const params = useParams();
  const router = useRouter();
  const [strategy, setStrategy] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (loading || !params.id) return;
    apiRequest(`/api/strategies/${params.id}`)
      .then(setStrategy)
      .catch((err) => setError(err.message || '전략을 불러오지 못했습니다.'));
  }, [loading, params.id]);

  const onSubmit = async (form) => {
    await apiRequest(`/api/strategies/${params.id}`, {
      method: 'PATCH',
      body: JSON.stringify(form),
    });
    router.push('/strategies');
  };

  if (loading || !strategy) {
    if (error) {
      return <EmptyState title="전략 정보를 불러오지 못했습니다." description={error} />;
    }
    return <LoadingState message="전략 데이터를 불러오는 중..." />;
  }

  return (
    <div className="page-stack">
      <PageHeader title="Edit Strategy" subtitle="전략 조건을 수정하고 저장하면 다음 스캔부터 반영됩니다." />
      <StrategyForm
        initial={strategy}
        submitLabel="저장"
        onSubmit={onSubmit}
        onCancel={() => router.push('/strategies')}
      />
    </div>
  );
}
