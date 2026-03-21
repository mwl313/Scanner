"use client";

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

export default function TopNav({ links, pathname, userEmail, onLogout, onOpenSettings }) {
  const navRef = useRef(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0, visible: false });

  useEffect(() => {
    const updateIndicator = () => {
      const root = navRef.current;
      if (!root) return;
      const active = root.querySelector('.top-nav-link.is-active');
      if (!active) {
        setIndicator((prev) => ({ ...prev, visible: false }));
        return;
      }
      const rootRect = root.getBoundingClientRect();
      const activeRect = active.getBoundingClientRect();
      setIndicator({
        left: activeRect.left - rootRect.left,
        width: activeRect.width,
        visible: true,
      });
    };

    updateIndicator();
    window.addEventListener('resize', updateIndicator);
    return () => window.removeEventListener('resize', updateIndicator);
  }, [pathname]);

  return (
    <header className="top-nav-shell">
      <div className="top-nav-inner">
        <div className="top-nav-brand-wrap">
          <Link href="/dashboard" className="top-nav-brand">
            Informed Curator
          </Link>
          <nav className="top-nav-links" aria-label="주요 메뉴" ref={navRef}>
            <span
              className="top-nav-indicator"
              style={{
                width: indicator.width,
                transform: `translateX(${indicator.left}px)`,
                opacity: indicator.visible ? 1 : 0,
              }}
            />
            {links.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link key={item.href} href={item.href} className={`top-nav-link ${active ? 'is-active' : ''}`.trim()}>
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
