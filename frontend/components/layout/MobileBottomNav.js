"use client";

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

export default function MobileBottomNav({ links, pathname }) {
  const navRef = useRef(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0, visible: false });

  useEffect(() => {
    const updateIndicator = () => {
      const root = navRef.current;
      if (!root) return;
      const active = root.querySelector('.mobile-nav-link.is-active');
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
    <nav className="mobile-bottom-nav" aria-label="모바일 하단 메뉴" ref={navRef}>
      <span
        className="mobile-nav-indicator"
        style={{
          width: indicator.width,
          transform: `translateX(${indicator.left}px)`,
          opacity: indicator.visible ? 1 : 0,
        }}
      />
      {links.map((item) => {
        const active = pathname.startsWith(item.href);
        return (
          <Link key={item.href} href={item.href} className={`mobile-nav-link ${active ? 'is-active' : ''}`.trim()}>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
