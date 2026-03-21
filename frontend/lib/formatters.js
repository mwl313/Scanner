export function formatNumber(value, options = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
  return Number(value).toLocaleString('ko-KR', options);
}

export function formatDateTime(value) {
  if (!value) return '-';
  return new Date(value).toLocaleString('ko-KR');
}

export function formatDateTimeCompact(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}

export function formatScanRunLabel(run) {
  if (!run) return '#-';
  return `#${run.id} · ${formatDateTimeCompact(run.started_at)}`;
}

export function formatPercent(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
  return `${Number(value).toFixed(digits)}%`;
}

export function formatForeignValue(value) {
  if (value === null || value === undefined) return '-';
  return formatNumber(value);
}

export function buildTossInvestUrl(stockCode) {
  if (stockCode === null || stockCode === undefined) return null;
  const code = String(stockCode).trim();
  if (!/^\d{6}$/.test(code)) return null;
  return `https://www.tossinvest.com/stocks/A${code}/order`;
}

export function reasonToPlainKorean(reason) {
  if (!reason) return '';
  if (reason.includes('RSI 상향 돌파 + 목표구간')) return 'RSI가 최근 조건에서 상향 돌파했고 목표 구간을 유지합니다.';
  if (reason.includes('볼린저 하단 근접')) return '볼린저 하단 부근으로 눌림 이후 반등 구간에 가깝습니다.';
  if (reason.includes('가격 vs MA20 충족')) return '현재가가 20일선 위이거나 근처에서 지지되고 있습니다.';
  if (reason.includes('MA5 vs MA20 충족')) return '단기 흐름(MA5)이 20일선 대비 회복 상태입니다.';
  if (reason.includes('MA20 vs MA60 충족')) return '중기 흐름(MA20)이 장기 흐름(MA60)보다 우세합니다.';
  if (reason.includes('외국인 최근')) {
    const match = reason.match(/외국인 최근\s+(\d+)일/);
    const days = match ? match[1] : 'N';
    return `최근 ${days}일 외국인 확정 순매수 합계가 양수입니다.`;
  }
  if (reason.includes('외인 확정 데이터 없음(중립 처리)')) return '외국인 확정 데이터가 없어 중립 처리되었습니다.';
  if (reason.includes('외인 데이터 미확보지만 정책상 통과')) return '외국인 데이터가 없지만 현재 정책상 통과입니다.';
  if (reason.includes('시가총액 기준 통과')) return '시가총액 기준을 충족합니다.';
  if (reason.includes('거래대금 기준 통과')) return '거래대금 기준을 충족합니다.';
  return reason;
}

export function failReasonToPlainKorean(reason) {
  if (!reason) return '';
  if (reason.includes('RSI 조건 미충족')) return 'RSI 상향 돌파 또는 목표 구간 조건을 만족하지 못했습니다.';
  if (reason.includes('볼린저 하단 근접 미충족')) return '볼린저 하단 근접 조건을 만족하지 못했습니다.';
  if (reason.includes('가격 vs MA20 미충족')) return '가격 vs MA20 조건을 만족하지 못했습니다.';
  if (reason.includes('MA5 vs MA20 미충족')) return 'MA5 vs MA20 조건을 만족하지 못했습니다.';
  if (reason.includes('MA20 vs MA60 미충족')) return 'MA20 vs MA60 조건을 만족하지 못했습니다.';
  if (reason.includes('외국인 확정 순매수 조건 미충족')) return '외국인 확정 순매수 조건이 충족되지 않았습니다.';
  if (reason.includes('외인 데이터 미확보(실패 정책)')) return '외국인 데이터 미확보로 실패 처리되었습니다.';
  if (reason.includes('시가총액 조건 미충족')) return '시가총액 최소 기준보다 낮습니다.';
  if (reason.includes('거래대금 기준 미달')) return '거래대금 최소 기준보다 낮습니다.';
  if (reason.includes('시장 필터 미충족')) return '시장 필터 조건과 맞지 않습니다.';
  return reason;
}

export function buildPositivePoints(item) {
  const plainReasons = (item.matched_reasons_json || []).map(reasonToPlainKorean).filter(Boolean);
  if (plainReasons.length === 0) return ['긍정 포인트 정보가 없습니다.'];
  return plainReasons;
}

export function maStatus(item) {
  const price = Number(item.price);
  const ma20 = Number(item.ma20);
  const ma5 = Number(item.ma5);
  const aboveMa20 = price >= ma20;
  const ma5Above20 = ma5 >= ma20;
  if (aboveMa20 && ma5Above20) return '상승 유지';
  if (aboveMa20) return 'MA20 위';
  if (ma20 > 0 && (ma20 - price) / ma20 <= 0.02) return 'MA20 근처';
  return '약세';
}

export function foreignStatusLabel(item) {
  if (item.foreign_data_status === 'confirmed') {
    return (item.foreign_data_source || '').includes('krx_confirmed_daily') ? '확정(KRX)' : '확정';
  }
  if (item.foreign_net_buy_snapshot_value !== null && item.foreign_net_buy_snapshot_value !== undefined) {
    return '미확정(스냅샷)';
  }
  return '없음';
}
