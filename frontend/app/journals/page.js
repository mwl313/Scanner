"use client";

import { useEffect, useMemo, useState } from 'react';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

export default function JournalsPage() {
  const { loading } = useRequireAuth();
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    strategy_id: '',
    stock_code: '',
    stock_name: '',
    trade_date: new Date().toISOString().slice(0, 10),
    buy_reason: '',
    quantity: 1,
    entry_price: 0,
    exit_price: '',
    memo: '',
  });

  const load = () => apiRequest('/api/journals').then(setItems);

  useEffect(() => {
    if (!loading) load();
  }, [loading]);

  const preview = useMemo(() => {
    const qty = Number(form.quantity || 0);
    const entry = Number(form.entry_price || 0);
    const exit = Number(form.exit_price || 0);
    if (!qty || !entry || !exit) return { profit: 0, rate: 0 };
    return {
      profit: (exit - entry) * qty,
      rate: (exit - entry) / entry,
    };
  }, [form]);

  const submit = async (e) => {
    e.preventDefault();
    await apiRequest('/api/journals', {
      method: 'POST',
      body: JSON.stringify({
        strategy_id: form.strategy_id ? Number(form.strategy_id) : null,
        stock_code: form.stock_code,
        stock_name: form.stock_name,
        trade_date: form.trade_date,
        buy_reason: form.buy_reason,
        quantity: Number(form.quantity),
        entry_price: Number(form.entry_price),
        exit_price: form.exit_price ? Number(form.exit_price) : null,
        memo: form.memo,
      }),
    });
    setForm((prev) => ({ ...prev, stock_code: '', stock_name: '', buy_reason: '', quantity: 1, entry_price: 0, exit_price: '', memo: '' }));
    load();
  };

  const remove = async (id) => {
    await apiRequest(`/api/journals/${id}`, { method: 'DELETE' });
    load();
  };

  if (loading) return <p>로딩중...</p>;

  return (
    <div>
      <h2>매매일지</h2>
      <form className="card" onSubmit={submit}>
        <div className="grid-3">
          <div>
            <label>날짜</label>
            <input type="date" value={form.trade_date} onChange={(e) => setForm((p) => ({ ...p, trade_date: e.target.value }))} required />
          </div>
          <div>
            <label>종목코드</label>
            <input value={form.stock_code} onChange={(e) => setForm((p) => ({ ...p, stock_code: e.target.value }))} required />
          </div>
          <div>
            <label>종목명</label>
            <input value={form.stock_name} onChange={(e) => setForm((p) => ({ ...p, stock_name: e.target.value }))} required />
          </div>
        </div>

        <div style={{ marginTop: 10 }}>
          <label>매수 이유</label>
          <textarea value={form.buy_reason} onChange={(e) => setForm((p) => ({ ...p, buy_reason: e.target.value }))} required />
        </div>

        <div className="grid-3" style={{ marginTop: 10 }}>
          <div>
            <label>수량</label>
            <input type="number" min={1} value={form.quantity} onChange={(e) => setForm((p) => ({ ...p, quantity: e.target.value }))} required />
          </div>
          <div>
            <label>진입가</label>
            <input type="number" min={0.01} step="0.01" value={form.entry_price} onChange={(e) => setForm((p) => ({ ...p, entry_price: e.target.value }))} required />
          </div>
          <div>
            <label>매도가</label>
            <input type="number" min={0.01} step="0.01" value={form.exit_price} onChange={(e) => setForm((p) => ({ ...p, exit_price: e.target.value }))} />
          </div>
        </div>

        <div style={{ marginTop: 10 }}>
          <label>비고</label>
          <textarea value={form.memo} onChange={(e) => setForm((p) => ({ ...p, memo: e.target.value }))} />
        </div>

        <p className="helper">
          예상 수익: {preview.profit.toFixed(2)} / 예상 수익률: {(preview.rate * 100).toFixed(2)}%
        </p>

        <button type="submit">기록 추가</button>
      </form>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>날짜</th>
                <th>종목</th>
                <th>수량</th>
                <th>진입가</th>
                <th>매도가</th>
                <th>수익</th>
                <th>수익률</th>
                <th>비고</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.trade_date}</td>
                  <td>{item.stock_name}({item.stock_code})</td>
                  <td>{item.quantity}</td>
                  <td>{Number(item.entry_price).toLocaleString()}</td>
                  <td>{item.exit_price ? Number(item.exit_price).toLocaleString() : '-'}</td>
                  <td>{Number(item.profit_value).toLocaleString()}</td>
                  <td>{(Number(item.profit_rate) * 100).toFixed(2)}%</td>
                  <td>{item.memo || '-'}</td>
                  <td><button className="danger" onClick={() => remove(item.id)}>삭제</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
