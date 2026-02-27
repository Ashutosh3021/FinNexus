'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function PerformanceChart({ holdings = [] }) {
  if (!holdings || holdings.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle>Portfolio Performance</CardTitle>
          <CardDescription>Your P&L over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="text-slate-400 mb-2">No data available</div>
              <p className="text-sm text-slate-500">
                Performance data will appear once you add holdings
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Simulate performance data for the past 30 days
  const generatePerformanceData = () => {
    const data = [];
    const today = new Date();

    for (let i = 29; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      let totalValue = 0;
      let totalCost = 0;

      holdings.forEach((holding) => {
        const value = holding.qty * holding.currentPrice;
        const cost = holding.qty * holding.buyPrice;
        totalValue += value;
        totalCost += cost;
      });

      const variance = (Math.random() - 0.5) * 2000 * (i / 30);
      const pnl = totalValue - totalCost + variance;

      data.push({
        date: `${date.getMonth() + 1}/${date.getDate()}`,
        pnl: Math.round(pnl),
        value: Math.round(totalValue + variance),
      });
    }

    return data;
  };

  const data = generatePerformanceData();

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <CardTitle>Portfolio Performance</CardTitle>
        <CardDescription>Your P&L over the last 30 days</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis dataKey="date" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              formatter={(value) => `$${value.toLocaleString()}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="pnl"
              stroke="#10b981"
              dot={false}
              strokeWidth={2}
              name="Profit/Loss"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
