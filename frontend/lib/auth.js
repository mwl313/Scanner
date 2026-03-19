"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiRequest } from './api';

export function useRequireAuth() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    apiRequest('/api/auth/me')
      .then((me) => {
        setUser(me);
        setLoading(false);
      })
      .catch(() => {
        router.push('/login');
      });
  }, [router]);

  return { loading, user };
}
