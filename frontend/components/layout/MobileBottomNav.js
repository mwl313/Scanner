"use client";

import Link from 'next/link';

export default function MobileBottomNav({ links, pathname }) {
  return (
    <nav className="mobile-bottom-nav" aria-label="모바일 하단 메뉴">
      {links.map((item) => {
        const active = pathname.startsWith(item.href);
        return (
          <Link key={item.href} href={item.href} className={active ? 'is-active' : ''}>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
