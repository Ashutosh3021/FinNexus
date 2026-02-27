'use client';

import React, { useState } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
} from 'recharts';

export function CandlestickChart({ data = [], symbol = 'ASSET' }) {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-96 bg-slate-700/30 rounded-lg border border-slate-600 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400 mb-2">No candlestick data available</p>
          <p className="text-sm text-slate-500">Historical price data will appear here</p>
        </div>
      </div>
    );
  }

  // Format data for chart display
  const chartData = data.map((candle, idx) => ({
    date: candle.date,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    volume: candle.volume,
    candleColor: candle.close >= candle.open ? '#10b981' : '#ef4444',
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length > 0) {
      const candleData = payload[0].payload;
      const originalCandle = data.find(d => d.date === candleData.date);

      return (
        <div className="bg-slate-800 border border-slate-600 rounded p-3 shadow-lg">
          <p className="text-white font-semibold text-sm mb-2">{candleData.date}</p>
          <div className="text-xs space-y-1">
            <p className="text-green-400">
              Open: ${originalCandle?.open.toLocaleString() || '-'}
            </p>
            <p className="text-blue-400">
              High: ${originalCandle?.high.toLocaleString() || '-'}
            </p>
            <p className="text-orange-400">
              Low: ${originalCandle?.low.toLocaleString() || '-'}
            </p>
            <p className={originalCandle?.close >= originalCandle?.open ? 'text-green-400' : 'text-red-400'}>
              Close: ${originalCandle?.close.toLocaleString() || '-'}
            </p>
            <p className="text-slate-400 mt-2 pt-1 border-t border-slate-600">
              Vol: {((originalCandle?.volume || 0) / 1000000).toFixed(1)}M
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
        >
          <defs>
            <linearGradient id="bullishGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="bearishGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            stroke="#94a3b8"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#94a3b8"
            tick={{ fontSize: 12 }}
            label={{ value: `${symbol} Price ($)`, angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* High-Low Range - subtle background */}
          <Area
            type="monotone"
            dataKey="high"
            fill="#8b5cf6"
            stroke="none"
            fillOpacity={0.1}
            name="Daily Range"
          />

          {/* High line - subtle reference */}
          <Line
            type="monotone"
            dataKey="high"
            stroke="#8b5cf6"
            dot={false}
            strokeWidth={0.5}
            opacity={0.4}
            name="High"
            isAnimationActive={false}
          />

          {/* Close line - main price action */}
          <Line
            type="monotone"
            dataKey="close"
            stroke="#3b82f6"
            dot={false}
            strokeWidth={2}
            opacity={0.8}
            name="Close Price"
            isAnimationActive={false}
          />

          {/* Open line for context */}
          <Line
            type="monotone"
            dataKey="open"
            stroke="#10b981"
            dot={false}
            strokeWidth={1}
            opacity={0.5}
            strokeDasharray="5 5"
            name="Open Price"
            isAnimationActive={false}
          />

          {/* Low line - support level */}
          <Line
            type="monotone"
            dataKey="low"
            stroke="#ef4444"
            dot={false}
            strokeWidth={0.5}
            opacity={0.4}
            name="Low"
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend and Info */}
      <div className="mt-4 p-4 bg-slate-700/30 rounded border border-slate-700">
        <p className="text-xs text-slate-400 mb-2">
          Chart shows 30-day price action with Open (green dashed), Close (blue), High-Low range (purple).
        </p>
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-slate-300">Opening Price</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-slate-300">Closing Price</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-slate-300">High-Low Range</span>
          </div>
        </div>
      </div>
    </div>
  );
}
