'use client';

import React, { useState } from 'react';
import { CandlestickChart } from '@/components/charts/CandlestickChart';
import { mockCandleData } from '@/lib/mockData';

export function MarketTrendChart({ holdings = [] }) {
  const [selectedSymbol, setSelectedSymbol] = useState(holdings?.[0]?.symbol || 'AAPL');

  const chartData = mockCandleData[selectedSymbol];
  const availableSymbols = Object.keys(mockCandleData);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-lg sm:text-xl font-bold text-white mb-4">Market Trends (Candlestick)</h2>
        
        {/* Symbol Selector */}
        <div className="flex flex-wrap gap-2">
          {availableSymbols.map((symbol) => (
            <button
              key={symbol}
              onClick={() => setSelectedSymbol(symbol)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
                selectedSymbol === symbol
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <CandlestickChart 
        data={chartData || []} 
        symbol={selectedSymbol}
      />
    </div>
  );
}
