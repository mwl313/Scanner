export const NAV_LINKS = [
  { href: '/dashboard', label: '대시보드' },
  { href: '/strategies', label: '전략' },
  { href: '/scans', label: '스캔 콘솔' },
];

const ROUTE_TRANSITION_ORDER = [
  '/dashboard',
  '/strategies',
  '/scans',
  '/watchlist',
  '/journals',
];

export function resolveRouteTransitionIndex(pathname = '') {
  if (!pathname || pathname === '/') return 0;
  const normalized = String(pathname).toLowerCase();

  if (normalized.startsWith('/stocks')) {
    return ROUTE_TRANSITION_ORDER.indexOf('/scans');
  }

  const matchedIndex = ROUTE_TRANSITION_ORDER.findIndex((base) => normalized.startsWith(base));
  return matchedIndex >= 0 ? matchedIndex : 0;
}

export const GRADE_META = {
  A: { label: 'A', tone: 'a' },
  B: { label: 'B', tone: 'b' },
  C: { label: 'C', tone: 'c' },
  EXCLUDED: { label: '제외', tone: 'excluded' },
};
