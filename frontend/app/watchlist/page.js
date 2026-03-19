"use client";

import { useEffect, useState } from 'react';
import { useRequireAuth } from '../../lib/auth';
import { apiRequest } from '../../lib/api';

export default function WatchlistPage() {
  const { loading } = useRequireAuth();
  const [items, setItems] = useState([]);
  const [stockCode, setStockCode] = useState('');
  const [stockName, setStockName] = useState('');
  const [error, setError] = useState('');

  const load = () => apiRequest('/api/watchlist').then(setItems);

  useEffect(() => {
    if (!loading) {
      load();
    }
  }, [loading]);

  const add = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await apiRequest('/api/watchlist', {
        method: 'POST',
        body: JSON.stringify({ stock_code: stockCode, stock_name: stockName }),
      });
      setStockCode('');
      setStockName('');
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const remove = async (id) => {
    await apiRequest(`/api/watchlist/${id}`, { method: 'DELETE' });
    load();
  };

  if (loading) return <p>로딩중...</p>;

  return (
    <div>
      <h2>관심종목</h2>
      <form className="card" onSubmit={add}>
        <div className="grid-2">
          <div>
            <label>종목코드</label>
            <input value={stockCode} onChange={(e) => setStockCode(e.target.value)} required />
          </div>
          <div>
            <label>종목명</label>
            <input value={stockName} onChange={(e) => setStockName(e.target.value)} required />
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" style={{ marginTop: 10 }}>추가</button>
      </form>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>종목코드</th>
                <th>종목명</th>
                <th>전략ID</th>
                <th>추가시각</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.stock_code}</td>
                  <td>{item.stock_name}</td>
                  <td>{item.strategy_id || '-'}</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
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
