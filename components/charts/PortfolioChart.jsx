'use client';

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function PortfolioChart({ holdings = [] }) {
  if (!holdings || holdings.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle>Asset Allocation</CardTitle>
          <CardDescription>Your portfolio distribution</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="text-slate-400 mb-2">No holdings yet</div>
              <p className="text-sm text-slate-500">
                Add investments to see your asset allocation
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate distribution by type
  const typeDistribution = {};
  let totalValue = 0;

  holdings.forEach((holding) => {
    const value = holding.qty * holding.currentPrice;
    totalValue += value;
    typeDistribution[holding.type] = (typeDistribution[holding.type] || 0) + value;
  });

  const chartData = Object.entries(typeDistribution).map(([type, value]) => ({
    name: type.charAt(0).toUpperCase() + type.slice(1),
    value: Math.round((value / totalValue) * 100),
    actualValue: value,
  }));

  const COLORS = {
    stock: '#3b82f6',
    crypto: '#fbbf24',
    commodity: '#f97316',
    etf: '#a78bfa',
  };

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <CardTitle>Asset Allocation</CardTitle>
        <CardDescription>Your portfolio distribution by asset type</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name} ${value}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[entry.name.toLowerCase()] || '#6b7280'}
                />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name, props) =>
                `${value}% ($${Math.round(props.payload.actualValue).toLocaleString()})`
              }
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
