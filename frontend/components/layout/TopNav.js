"use client";

import Link from 'next/link';

export default function TopNav({ links, pathname, userEmail, onLogout, onOpenSettings }) {
  return (
    <header className="top-nav-shell">
      <div className="top-nav-inner">
        <div className="top-nav-brand-wrap">
          <Link href="/dashboard" className="top-nav-brand">
            Informed Curator
          </Link>
          <nav className="top-nav-links" aria-label="주요 메뉴">
            {links.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link key={item.href} href={item.href} className={active ? 'is-active' : ''}>
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="top-nav-actions">
          <div className="live-chip">
            <span className="live-dot" />
            <span>KOSPI Scanner</span>
          </div>
          <button type="button" className="btn btn-ghost nav-icon-btn" onClick={onOpenSettings} aria-label="설정 열기">
            설정
          </button>
          <div className="top-user-block">
            <span className="helper">{userEmail || '비로그인'}</span>
            {userEmail ? (
              <button type="button" className="btn btn-ghost" onClick={onLogout}>
                로그아웃
              </button>
            ) : (
              <Link href="/login" className="btn btn-ghost">
                로그인
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
