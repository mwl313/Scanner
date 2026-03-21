function pad(value) {
  return String(value).padStart(2, '0');
}

export function escapeCsvValue(value) {
  if (value === null || value === undefined) return '';
  const text = String(value);
  const escaped = text.replace(/"/g, '""');
  if (/[",\n\r]/.test(text)) {
    return `"${escaped}"`;
  }
  return escaped;
}

export function convertRowsToCsv(headers, rows) {
  const headerLine = headers.map(escapeCsvValue).join(',');
  const bodyLines = rows.map((row) => row.map(escapeCsvValue).join(','));
  return [headerLine, ...bodyLines].join('\r\n');
}

export function convertScanResultsToCsv(results) {
  const headers = [
    '종목명',
    '종목코드',
    '등급',
    '상태',
    '점수',
    '현재가',
    '거래대금',
    'RSI',
    'RSI Signal',
    '외인 확정합',
    '장중 스냅샷',
    '긍정 포인트',
  ];
  const rows = results.map((item) => [
    item.stock_name ?? '',
    item.stock_code ?? '',
    item.grade ?? '',
    item.status ?? '',
    item.score ?? '',
    item.price ?? '',
    item.trading_value ?? '',
    item.rsi ?? '',
    item.rsi_signal ?? '',
    item.foreign_net_buy_confirmed_value ?? '',
    item.foreign_net_buy_snapshot_value ?? '',
    item.positive_points ?? '',
  ]);
  return convertRowsToCsv(headers, rows);
}

export function buildCsvFilename(prefix = 'scan-results') {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = pad(now.getMonth() + 1);
  const dd = pad(now.getDate());
  const hh = pad(now.getHours());
  const min = pad(now.getMinutes());
  return `${prefix}-${yyyy}-${mm}-${dd}-${hh}-${min}.csv`;
}

export function downloadCsv(csvText, filename) {
  const blob = new Blob(['\uFEFF', csvText], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
