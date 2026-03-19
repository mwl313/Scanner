"use client";

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { apiRequest } from '../lib/api';

const links = [
  { href: '/dashboard', label: '대시보드' },
  { href: '/strategies', label: '전략' },
  { href: '/scans', label: '스캔결과' },
];

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState(null);

  useEffect(() => {
    apiRequest('/api/auth/me')
      .then(setUser)
      .catch(() => setUser(null));
  }, [pathname]);

  const logout = async () => {
    await apiRequest('/api/auth/logout', { method: 'POST' });
    setUser(null);
    router.push('/login');
  };

  const hideNav = pathname === '/login' || pathname === '/signup';
  if (hideNav) {
    return null;
  }

  return (
    <header className="nav">
      <div className="nav-inner">
        <div className="row nav-links">
          {links.map((item) => (
            <Link key={item.href} href={item.href}>
              {item.label}
            </Link>
          ))}
        </div>
        <div className="row">
          <span className="helper">{user?.email || '비로그인'}</span>
          {user ? (
            <button className="secondary" onClick={logout}>로그아웃</button>
          ) : (
            <Link href="/login">로그인</Link>
          )}
        </div>
      </div>
    </header>
  );
}
