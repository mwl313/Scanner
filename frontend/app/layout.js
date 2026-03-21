import './globals.css';
import AppShell from '../components/layout/AppShell';

export const metadata = {
  title: 'KOSPI Swing Scanner MVP',
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
