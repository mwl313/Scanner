"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { apiRequest } from '../../lib/api';

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await apiRequest('/api/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, password_confirm: passwordConfirm }),
      });
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
      <h2>회원가입</h2>
      <form onSubmit={onSubmit} className="auth-form">
        <label>이메일</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label className="auth-field-label">비밀번호</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />

        <label className="auth-field-label">비밀번호 확인</label>
        <input type="password" value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} required minLength={8} />

        {error && <p className="error">{error}</p>}

        <button type="submit" className="auth-submit-btn">가입</button>
      </form>
      <p className="helper auth-footer">
        이미 계정이 있다면 <Link href="/login">로그인</Link>
      </p>
    </div>
  );
}
