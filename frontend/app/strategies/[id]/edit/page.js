"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import StrategyForm from '../../../../components/StrategyForm';
import { useRequireAuth } from '../../../../lib/auth';
import { apiRequest } from '../../../../lib/api';

export default function EditStrategyPage() {
  const { loading } = useRequireAuth();
  const params = useParams();
  const router = useRouter();
  const [strategy, setStrategy] = useState(null);

  useEffect(() => {
    if (!loading && params.id) {
      apiRequest(`/api/strategies/${params.id}`).then(setStrategy);
    }
  }, [loading, params.id]);

  const onSubmit = async (form) => {
    await apiRequest(`/api/strategies/${params.id}`, {
      method: 'PATCH',
      body: JSON.stringify(form),
    });
    router.push('/strategies');
  };

  if (loading || !strategy) {
    return <p>로딩중...</p>;
  }

  return (
    <div>
      <h2>전략 수정</h2>
      <StrategyForm initial={strategy} submitLabel="저장" onSubmit={onSubmit} />
    </div>
  );
}
