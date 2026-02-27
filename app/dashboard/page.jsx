'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useUser } from '@/context/UserContext';
import { usePortfolio } from '@/context/PortfolioContext';
import { usePlayground } from '@/context/PlaygroundContext';
import { useNews } from '@/context/NewsContext';
import { PortfolioChart } from '@/components/charts/PortfolioChart';
import { PerformanceChart } from '@/components/charts/PerformanceChart';
import { PredictionStatsChart } from '@/components/charts/PredictionStatsChart';
import { MarketTrendChart } from '@/components/dashboard/MarketTrendChart';
import { TrendingUp, Target, Trophy, Activity, AlertCircle } from 'lucide-react';

function DashboardContent() {
  const user = useUser();
  const portfolio = usePortfolio();
  const playground = usePlayground();
  const news = useNews();
  const [isLoading, setIsLoading] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-10 bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  const portfolioChange = portfolio.totalPnL;
  const portfolioChangePercent =
    (portfolio.totalPnL / portfolio.totalCost) * 100;

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          Welcome back, {user?.name?.split(' ')[0]}!
        </h1>
        <p className="text-slate-400 mt-1">
          Here's your financial overview for today
        </p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid md:grid-cols-4 gap-4">
        {/* Total Portfolio Value */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Total Portfolio Value</p>
            <TrendingUp className="text-blue-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-white">
            ${portfolio.totalValue?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </p>
          <p
            className={`text-sm mt-2 ${
              portfolioChange >= 0 ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {portfolioChange >= 0 ? '+' : ''}
            {portfolioChange.toFixed(2)} ({portfolioChangePercent.toFixed(2)}%)
          </p>
        </div>

        {/* Win Rate */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Win Rate</p>
            <Trophy className="text-yellow-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-white">{playground.winRate}%</p>
          <p className="text-sm text-slate-400 mt-2">
            {playground.wins} / {playground.totalRounds} predictions
          </p>
        </div>

        {/* Current Streak */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Current Streak</p>
            <Target className="text-orange-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-white">{playground.streak}</p>
          <p className="text-sm text-slate-400 mt-2">Consecutive wins</p>
        </div>

        {/* Virtual Balance */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Virtual Balance</p>
            <Activity className="text-green-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-white">
            ${user?.virtualBalance?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </p>
          <p className="text-sm text-slate-400 mt-2">Available to trade</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PortfolioChart holdings={portfolio?.holdings} />
        <PerformanceChart holdings={portfolio?.holdings} />
      </div>

      {/* Market Trends Candlestick Chart */}
      <div>
        <MarketTrendChart holdings={portfolio?.holdings} />
      </div>

      {/* Prediction Stats */}
      <div>
        <PredictionStatsChart predictionHistory={playground?.predictionHistory} />
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Top Holdings */}
        <div className="lg:col-span-2 bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
          <div className="p-6 border-b border-slate-700">
            <h2 className="text-xl font-bold text-white">Top Holdings</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-400">
                    Asset
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-400">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-400">
                    Qty
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-400">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-400">
                    Return
                  </th>
                </tr>
              </thead>
              <tbody>
                {portfolio.holdings?.slice(0, 5).map((holding) => {
                  const holdingValue = holding.qty * holding.currentPrice;
                  const holdingCost = holding.qty * holding.buyPrice;
                  const holdingReturn = holdingValue - holdingCost;
                  const holdingReturnPercent =
                    (holdingReturn / holdingCost) * 100;

                  return (
                    <tr
                      key={holding.id}
                      className="border-b border-slate-700 hover:bg-slate-700/50"
                    >
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-white">
                            {holding.asset}
                          </p>
                          <p className="text-sm text-slate-400">
                            {holding.symbol}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-3 py-1 bg-slate-700 text-slate-300 text-sm rounded-full capitalize">
                          {holding.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-white">{holding.qty}</td>
                      <td className="px-6 py-4 text-white">
                        ${holding.currentPrice.toLocaleString()}
                      </td>
                      <td
                        className={`px-6 py-4 font-medium ${
                          holdingReturn >= 0
                            ? 'text-green-400'
                            : 'text-red-400'
                        }`}
                      >
                        {holdingReturn >= 0 ? '+' : ''}
                        {holdingReturnPercent.toFixed(2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h2 className="text-xl font-bold text-white mb-4">Recent Predictions</h2>
          <div className="space-y-3">
            {playground.predictionHistory?.slice(0, 5).map((pred) => (
              <div
                key={pred.id}
                className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
              >
                <div>
                  <p className="text-white font-medium">{pred.asset}</p>
                  <p className="text-xs text-slate-400">{pred.date}</p>
                </div>
                <div className="text-right">
                  <div
                    className={`text-sm font-semibold ${
                      pred.type === 'win'
                        ? 'text-green-400'
                        : 'text-red-400'
                    }`}
                  >
                    {pred.type === 'win' ? '+' : ''}
                    {pred.pnl}
                  </div>
                  <div className="text-xs text-slate-400">
                    {pred.pnlPercent}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-4">
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors">
          Start New Prediction
        </button>
        <button className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 rounded-lg transition-colors">
          View Full Portfolio
        </button>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-10 bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
