'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { usePortfolio } from '@/context/PortfolioContext';
import { Plus, Trash2, TrendingUp, TrendingDown } from 'lucide-react';

function PortfolioContent() {
  const portfolio = usePortfolio();
  const [isLoading, setIsLoading] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const getAssetTypeColor = (type) => {
    const colors = {
      stock: 'text-blue-400 bg-blue-500/10',
      crypto: 'text-yellow-400 bg-yellow-500/10',
      commodity: 'text-orange-400 bg-orange-500/10',
      etf: 'text-purple-400 bg-purple-500/10',
    };
    return colors[type] || 'text-slate-400 bg-slate-500/10';
  };

  if (!isHydrated || !portfolio) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-10 bg-slate-700 rounded w-1/4 mb-2"></div>
          <div className="h-4 bg-slate-700 rounded w-1/3"></div>
        </div>
        <div className="grid md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="h-4 bg-slate-700 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-slate-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Portfolio</h1>
          <p className="text-slate-400 mt-1">Manage your virtual investments</p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap">
          <Plus size={20} />
          Add Holding
        </button>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm mb-1">Total Value</p>
          <p className="text-2xl font-bold text-white">
            ${portfolio.totalValue?.toLocaleString('en-US', { maximumFractionDigits: 2 }) || '0.00'}
          </p>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm mb-1">Total Cost</p>
          <p className="text-2xl font-bold text-white">
            ${portfolio.totalCost?.toLocaleString('en-US', { maximumFractionDigits: 2 }) || '0.00'}
          </p>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm mb-1">Total P&L</p>
          <p
            className={`text-2xl font-bold ${
              (portfolio.totalPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {(portfolio.totalPnL || 0) >= 0 ? '+' : ''}
            ${(portfolio.totalPnL || 0)?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm mb-1">Holdings Count</p>
          <p className="text-2xl font-bold text-white">{portfolio.holdings?.length || 0}</p>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white">Your Holdings</h2>
        </div>

        {portfolio.holdings && portfolio.holdings.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-700/50">
                  <th className="px-3 sm:px-6 py-3 text-left text-xs sm:text-sm font-semibold text-slate-400">
                    Asset
                  </th>
                  <th className="hidden sm:table-cell px-6 py-3 text-left text-sm font-semibold text-slate-400">
                    Type
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-right text-xs sm:text-sm font-semibold text-slate-400">
                    Qty
                  </th>
                  <th className="hidden md:table-cell px-6 py-3 text-right text-sm font-semibold text-slate-400">
                    Buy Price
                  </th>
                  <th className="hidden lg:table-cell px-6 py-3 text-right text-sm font-semibold text-slate-400">
                    Current Price
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-right text-xs sm:text-sm font-semibold text-slate-400">
                    Value
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-right text-xs sm:text-sm font-semibold text-slate-400">
                    Return
                  </th>
                </tr>
              </thead>
              <tbody>
                {portfolio.holdings.map((holding) => {
                  const value = holding.qty * holding.currentPrice;
                  const cost = holding.qty * holding.buyPrice;
                  const pnl = value - cost;
                  const pnlPercent = (pnl / cost) * 100;

                  return (
                    <tr
                      key={holding.id}
                      className="border-b border-slate-700 hover:bg-slate-700/50 transition-colors"
                    >
                      <td className="px-3 sm:px-6 py-4">
                        <div>
                          <p className="font-semibold text-white text-sm sm:text-base">
                            {holding.asset}
                          </p>
                          <p className="text-xs sm:text-sm text-slate-400">
                            {holding.symbol}
                          </p>
                        </div>
                      </td>
                      <td className="hidden sm:table-cell px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${getAssetTypeColor(
                            holding.type
                          )}`}
                        >
                          {holding.type}
                        </span>
                      </td>
                      <td className="px-3 sm:px-6 py-4 text-right text-white font-medium text-sm sm:text-base">
                        {holding.qty}
                      </td>
                      <td className="hidden md:table-cell px-6 py-4 text-right text-white">
                        ${holding.buyPrice.toLocaleString()}
                      </td>
                      <td className="hidden lg:table-cell px-6 py-4 text-right text-white">
                        ${holding.currentPrice.toLocaleString()}
                      </td>
                      <td className="px-3 sm:px-6 py-4 text-right text-white font-semibold text-sm sm:text-base">
                        ${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-3 sm:px-6 py-4 text-right">
                        <div
                          className={`font-semibold flex items-center justify-end gap-1 text-xs sm:text-base ${
                            pnl >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {pnl >= 0 ? (
                            <TrendingUp size={14} className="hidden sm:block" />
                          ) : (
                            <TrendingDown size={14} className="hidden sm:block" />
                          )}
                          {pnlPercent.toFixed(1)}%
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center">
            <p className="text-slate-400">No holdings yet. Add your first investment!</p>
          </div>
        )}
      </div>

      {/* Asset Allocation */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <h2 className="text-xl font-bold text-white mb-4">Asset Type Distribution</h2>
        {portfolio.totalValue > 0 ? (
          <div className="space-y-3">
            {['stock', 'crypto', 'commodity', 'etf'].map((type) => {
              const typeHoldings = portfolio.holdings?.filter(
                (h) => h.type === type
              ) || [];
              const typeValue = typeHoldings.reduce(
                (sum, h) => sum + h.qty * h.currentPrice,
                0
              );
              const percent =
                (typeValue / portfolio.totalValue) * 100;

              return (
                <div key={type}>
                  <div className="flex justify-between mb-1">
                    <span className="text-white capitalize text-sm sm:text-base">{type}</span>
                    <span className="text-slate-400 text-sm sm:text-base">
                      {percent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        type === 'stock'
                          ? 'bg-blue-500'
                          : type === 'crypto'
                          ? 'bg-yellow-500'
                          : type === 'commodity'
                          ? 'bg-orange-500'
                          : 'bg-purple-500'
                      }`}
                      style={{ width: `${Math.max(percent, 0.5)}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-400 text-center py-4">Add holdings to see distribution</p>
        )}
      </div>
    </div>
  );
}

export default function PortfolioPage() {
  return (
    <Suspense fallback={
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-10 bg-slate-700 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="h-4 bg-slate-700 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-slate-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    }>
      <PortfolioContent />
    </Suspense>
  );
}
