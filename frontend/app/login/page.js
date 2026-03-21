"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { apiRequest } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('demo1234');
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await apiRequest('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      router.push('/dashboard');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="card auth-card">
      <h2>로그인</h2>
      <form onSubmit={onSubmit} className="auth-form">
        <label>이메일</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label className="auth-field-label">비밀번호</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />

        {error && <p className="error">{error}</p>}

        <button type="submit" className="auth-submit-btn">로그인</button>
      </form>
      <p className="helper auth-footer">
        계정이 없다면 <Link href="/signup">회원가입</Link>
      </p>
    </div>
  );
}
