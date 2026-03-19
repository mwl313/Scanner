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
    <div className="card" style={{ maxWidth: 420, margin: '40px auto' }}>
      <h2>회원가입</h2>
      <form onSubmit={onSubmit}>
        <label>이메일</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label style={{ marginTop: 10 }}>비밀번호</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />

        <label style={{ marginTop: 10 }}>비밀번호 확인</label>
        <input type="password" value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} required minLength={8} />

        {error && <p className="error">{error}</p>}

        <button type="submit" style={{ marginTop: 12 }}>가입</button>
      </form>
      <p className="helper" style={{ marginTop: 12 }}>
        이미 계정이 있다면 <Link href="/login">로그인</Link>
      </p>
    </div>
  );
}
