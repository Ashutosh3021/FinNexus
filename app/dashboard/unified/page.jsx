'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { usePortfolio } from '@/context/PortfolioContext';
import { usePlayground } from '@/context/PlaygroundContext';
import { useNews } from '@/context/NewsContext';
import { useUser } from '@/context/UserContext';
import { PortfolioChart } from '@/components/charts/PortfolioChart';
import { PerformanceChart } from '@/components/charts/PerformanceChart';
import { PredictionStatsChart } from '@/components/charts/PredictionStatsChart';
import { EmptyState, DataLoadingState } from '@/components/ui/EmptyState';
import { TrendingUp, TrendingDown, Zap, BarChart3, AlertCircle } from 'lucide-react';

function UnifiedDashboardContent() {
  const portfolio = usePortfolio();
  const playground = usePlayground();
  const news = useNews();
  const user = useUser();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) {
    return <DataLoadingState />;
  }

  // Calculate portfolio metrics
  const totalValue = portfolio?.totalValue || 0;
  const totalPnL = portfolio?.totalPnL || 0;
  const holdingsCount = portfolio?.holdings?.length || 0;

  // Calculate playground metrics
  const totalPredictions = playground?.predictionHistory?.length || 0;
  const winCount = playground?.predictionHistory?.filter((p) => p.type === 'win').length || 0;
  const winRate = totalPredictions > 0 ? Math.round((winCount / totalPredictions) * 100) : 0;

  // Get recent news
  const recentNews = news?.filteredNews?.slice(0, 3) || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-2">
            Welcome back, {user?.name || 'Trader'}! Here's your complete financial overview.
          </p>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Portfolio Value */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Portfolio Value</p>
            <BarChart3 size={18} className="text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">
            ${totalValue.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-slate-500 mt-1">{holdingsCount} holdings</p>
        </div>

        {/* Total P&L */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Total P&L</p>
            {totalPnL >= 0 ? (
              <TrendingUp size={18} className="text-green-400" />
            ) : (
              <TrendingDown size={18} className="text-red-400" />
            )}
          </div>
          <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalPnL >= 0 ? '+' : ''} ${totalPnL.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-slate-500 mt-1">Profit and Loss</p>
        </div>

        {/* Prediction Win Rate */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Win Rate</p>
            <Zap size={18} className="text-yellow-400" />
          </div>
          <p className="text-2xl font-bold text-white">{winRate}%</p>
          <p className="text-xs text-slate-500 mt-1">
            {winCount} of {totalPredictions} predictions
          </p>
        </div>

        {/* Virtual Balance */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm">Virtual Balance</p>
            <AlertCircle size={18} className="text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-white">
            ${user?.virtualBalance?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'}
          </p>
          <p className="text-xs text-slate-500 mt-1">Available to trade</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PortfolioChart holdings={portfolio?.holdings} />
        <PerformanceChart holdings={portfolio?.holdings} />
      </div>

      {/* Prediction Stats */}
      <div className="grid grid-cols-1 gap-6">
        <PredictionStatsChart predictionHistory={playground?.predictionHistory} />
      </div>

      {/* News Section */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white">Latest Financial News</h2>
          <p className="text-slate-400 mt-1">Stay informed with recent market updates</p>
        </div>

        {recentNews.length > 0 ? (
          <div className="space-y-4">
            {recentNews.map((newsItem) => (
              <div
                key={newsItem.id}
                className="bg-slate-700/50 rounded-lg border border-slate-600 p-4 hover:border-slate-500 transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-2">
                  <h3 className="text-base font-semibold text-white line-clamp-2">
                    {newsItem.headline}
                  </h3>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
                      newsItem.sentiment === 'positive'
                        ? 'bg-green-500/20 text-green-400'
                        : newsItem.sentiment === 'negative'
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-slate-600 text-slate-300'
                    }`}
                  >
                    {newsItem.sentiment}
                  </span>
                </div>
                <p className="text-sm text-slate-300 mb-3">{newsItem.summary}</p>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="text-slate-500">{newsItem.date}</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-500">{newsItem.source}</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-400">Impact: {newsItem.impactScore}/10</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={AlertCircle}
            title="No news available"
            description="Financial news will appear here as it becomes available"
            variant="default"
          />
        )}
      </div>

      {/* Data Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <p className="text-blue-400 font-medium">Portfolio Status</p>
          <p className="text-slate-300 text-xs mt-1">
            {holdingsCount > 0 ? `Actively managing ${holdingsCount} assets` : 'Start by adding your first holding'}
          </p>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
          <p className="text-yellow-400 font-medium">Prediction Activity</p>
          <p className="text-slate-300 text-xs mt-1">
            {totalPredictions > 0 ? `${totalPredictions} predictions tracked` : 'No predictions yet'}
          </p>
        </div>
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
          <p className="text-purple-400 font-medium">Learning Progress</p>
          <p className="text-slate-300 text-xs mt-1">
            Level {user?.level || 'BEGINNER'} • {user?.xp || 0} XP
          </p>
        </div>
      </div>
    </div>
  );
}

export default function UnifiedDashboardPage() {
  return (
    <Suspense fallback={<DataLoadingState />}>
      <UnifiedDashboardContent />
    </Suspense>
  );
}
