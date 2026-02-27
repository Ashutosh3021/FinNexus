'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function PredictionStatsChart({ predictionHistory = [] }) {
  if (!predictionHistory || predictionHistory.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle>Prediction Stats</CardTitle>
          <CardDescription>Your prediction accuracy by asset</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="text-slate-400 mb-2">No predictions yet</div>
              <p className="text-sm text-slate-500">
                Start making predictions to track your accuracy
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate stats by asset
  const assetStats = {};

  predictionHistory.forEach((pred) => {
    if (!assetStats[pred.asset]) {
      assetStats[pred.asset] = { total: 0, wins: 0 };
    }
    assetStats[pred.asset].total += 1;
    if (pred.type === 'win') {
      assetStats[pred.asset].wins += 1;
    }
  });

  const chartData = Object.entries(assetStats)
    .slice(0, 6)
    .map(([asset, stats]) => ({
      asset,
      wins: stats.wins,
      losses: stats.total - stats.wins,
      winRate: Math.round((stats.wins / stats.total) * 100),
    }));

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <CardTitle>Prediction Stats</CardTitle>
        <CardDescription>Your accuracy by asset (recent predictions)</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis dataKey="asset" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Bar dataKey="wins" fill="#10b981" name="Wins" />
            <Bar dataKey="losses" fill="#ef4444" name="Losses" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
