import './globals.css';
import Nav from '../components/Nav';

export const metadata = {
  title: 'KOSPI Swing Scanner MVP',
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <Nav />
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
