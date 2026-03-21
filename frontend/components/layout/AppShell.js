"use client";

import { useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import Drawer from '../ui/Drawer';
import SurfaceCard from '../ui/SurfaceCard';
import TopNav from './TopNav';
import MobileBottomNav from './MobileBottomNav';
import { apiRequest } from '../../lib/api';
import { NAV_LINKS } from '../../lib/theme';

const AUTH_FREE_ROUTES = new Set(['/login', '/signup']);

export default function AppShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const hideChrome = AUTH_FREE_ROUTES.has(pathname || '');

  useEffect(() => {
    if (hideChrome) return;
    apiRequest('/api/auth/me')
      .then(setUser)
      .catch(() => setUser(null));
  }, [pathname, hideChrome]);

  const onLogout = async () => {
    await apiRequest('/api/auth/logout', { method: 'POST' });
    setUser(null);
    router.push('/login');
  };

  const navLinks = useMemo(() => NAV_LINKS, []);

  return (
    <div className="app-shell">
      <div className="app-tone-layer" />
      {!hideChrome && (
        <>
          <TopNav
            links={navLinks}
            pathname={pathname || ''}
            userEmail={user?.email}
            onLogout={onLogout}
            onOpenSettings={() => setSettingsOpen(true)}
          />
          <MobileBottomNav links={navLinks} pathname={pathname || ''} />
        </>
      )}

      <main className={`app-main ${hideChrome ? 'auth-main' : ''}`}>
        <div className="app-container">{children}</div>
      </main>

      <Drawer open={settingsOpen} onClose={() => setSettingsOpen(false)} title="설정" side="right" width="420px">
        <div className="settings-stack">
          <SurfaceCard tone="soft">
            <h4>데이터 소스</h4>
            <p className="helper">현재 연결된 Provider 상태를 보여주는 영역입니다.</p>
            <p className="settings-static">현재 앱 설정은 서버 환경변수에서 관리됩니다.</p>
          </SurfaceCard>
          <SurfaceCard tone="soft">
            <h4>신호 정책</h4>
            <p className="helper">향후 규칙 템플릿/알림 정책 설정이 추가될 예정입니다.</p>
            <p className="settings-static">이번 버전에서는 읽기 전용 안내만 제공합니다.</p>
          </SurfaceCard>
          <SurfaceCard tone="soft">
            <h4>보안</h4>
            <p className="helper">세션 기반 인증이 활성화되어 있으며 쿠키는 서버에서 관리됩니다.</p>
            <p className="settings-static">실제 변경은 배포 환경의 `.env`에서 수행하세요.</p>
          </SurfaceCard>
        </div>
      </Drawer>
    </div>
  );
}
