'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';

const SYMBOLS = ['BTC-USD','ETH-USD','AAPL','GOOGL','TSLA','GC=F','^NSEI','^GSPC','USDINR=X','CL=F'];

const getApiBase = () => process.env.NEXT_PUBLIC_API_URL || '';

export default function LiveTickerBar() {
  const [prices, setPrices] = useState({});
  const [prevPrices, setPrevPrices] = useState({});
  const [flashes, setFlashes] = useState({});
  const timerRef = useRef(null);

  const items = useMemo(() => SYMBOLS.map(sym => {
    const p = prices[sym];
    return {
      symbol: sym,
      price: p?.price ?? '-',
      change: p?.change ?? 0,
    };
  }), [prices]);

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const url = `${getApiBase()}/market/live-prices?symbols=${encodeURIComponent(SYMBOLS.join(','))}`;
        const res = await fetch(url, { cache: 'no-store' });
        if (!res.ok) throw new Error('bad status');
        const data = await res.json();
        const map = {};
        for (const sym of SYMBOLS) {
          map[sym] = data[sym] ?? null;
        }
        setPrevPrices(prices);
        setPrices(map);
        const nextFlashes = {};
        for (const sym of SYMBOLS) {
          const oldP = prevPrices[sym]?.price;
          const newP = map[sym]?.price;
          if (typeof oldP === 'number' && typeof newP === 'number' && oldP !== newP) {
            nextFlashes[sym] = newP > oldP ? 'up' : 'down';
          }
        }
        setFlashes(nextFlashes);
        setTimeout(() => setFlashes({}), 700);
      } catch {
        const mock = {};
        SYMBOLS.forEach(s => {
          const base = Math.random()*100 + 100;
          mock[s] = { price: parseFloat(base.toFixed(2)), change: parseFloat(((Math.random()-0.5)*2).toFixed(2)) };
        });
        setPrevPrices(prices);
        setPrices(mock);
      }
    };
    fetchPrices();
    timerRef.current = setInterval(fetchPrices, 30000);
    return () => timerRef.current && clearInterval(timerRef.current);
  }, []);

  const doubled = [...items, ...items];

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-slate-900/95 border-b border-slate-800">
      <div className="overflow-hidden">
        <div className="ticker-track">
          {doubled.map((it, idx) => (
            <div
              key={`${it.symbol}-${idx}`}
              className={`px-4 py-2 flex items-center gap-3 text-sm border-r border-slate-800 ${flashes[it.symbol]==='up' ? 'price-flash-up' : flashes[it.symbol]==='down' ? 'price-flash-down' : ''}`}
            >
              <span className="font-semibold text-slate-200">{it.symbol}</span>
              <span className="text-white">{typeof it.price === 'number' ? it.price.toLocaleString() : '-'}</span>
              <span className={`${(it.change ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(it.change ?? 0) >= 0 ? '+' : ''}{it.change}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

