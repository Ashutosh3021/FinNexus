'use client';

import React from 'react';
import { TrendingUp, TrendingDown, AlertCircle, Info } from 'lucide-react';

export function AssetAnalysisPanel({ asset, insights = null }) {
  if (!asset) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <p className="text-slate-400 text-center py-8">Select an asset to view detailed analysis</p>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <p className="text-slate-400 text-center py-8">Analysis data unavailable for {asset.symbol}</p>
      </div>
    );
  }

  const getTrendIcon = (trend) => {
    if (trend === 'uptrend') {
      return <TrendingUp className="text-green-400" size={20} />;
    }
    return <TrendingDown className="text-red-400" size={20} />;
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'very strong':
        return 'text-green-400 bg-green-400/10';
      case 'strong':
        return 'text-green-400 bg-green-400/10';
      case 'moderate':
        return 'text-blue-400 bg-blue-400/10';
      case 'weak':
        return 'text-orange-400 bg-orange-400/10';
      default:
        return 'text-slate-400 bg-slate-400/10';
    }
  };

  return (
    <div className="space-y-4">
      {/* Key Metrics */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          {getTrendIcon(insights.trend)}
          Technical Analysis
        </h3>

        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Support/Resistance */}
          <div className="bg-slate-700/50 rounded p-4">
            <p className="text-slate-400 text-sm mb-2">Resistance Level</p>
            <p className="text-white font-bold text-lg">${insights.resistance.toLocaleString()}</p>
          </div>
          <div className="bg-slate-700/50 rounded p-4">
            <p className="text-slate-400 text-sm mb-2">Support Level</p>
            <p className="text-white font-bold text-lg">${insights.support.toLocaleString()}</p>
          </div>

          {/* Moving Averages */}
          <div className="bg-slate-700/50 rounded p-4">
            <p className="text-slate-400 text-sm mb-2">50-Day MA</p>
            <p className="text-white font-bold text-lg">${insights.movingAverage50.toLocaleString()}</p>
          </div>
          <div className="bg-slate-700/50 rounded p-4">
            <p className="text-slate-400 text-sm mb-2">200-Day MA</p>
            <p className="text-white font-bold text-lg">${insights.movingAverage200.toLocaleString()}</p>
          </div>

          {/* RSI and MACD */}
          <div className="bg-slate-700/50 rounded p-4">
            <p className="text-slate-400 text-sm mb-2">RSI (14)</p>
            <p className={`font-bold text-lg ${insights.rsi > 70 ? 'text-red-400' : insights.rsi < 30 ? 'text-green-400' : 'text-blue-400'}`}>
              {insights.rsi}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {insights.rsi > 70 ? 'Overbought' : insights.rsi < 30 ? 'Oversold' : 'Neutral'}
            </p>
          </div>
          <div className="bg-slate-700/50 rounded p-4">
            <p className="text-slate-400 text-sm mb-2">MACD Signal</p>
            <p className={`font-bold text-lg ${insights.macd === 'bullish' ? 'text-green-400' : 'text-red-400'}`}>
              {insights.macd?.toUpperCase()}
            </p>
          </div>
        </div>

        {/* Trend and Strength */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-700/50 rounded p-3 text-center">
            <p className="text-slate-400 text-xs mb-1">Trend</p>
            <p className="text-white font-semibold capitalize text-sm">{insights.trend}</p>
          </div>
          <div className="bg-slate-700/50 rounded p-3 text-center">
            <p className="text-slate-400 text-xs mb-1">Strength</p>
            <p className={`font-semibold text-sm capitalize ${getStrengthColor(insights.strength)}`}>
              {insights.strength}
            </p>
          </div>
          <div className="bg-slate-700/50 rounded p-3 text-center">
            <p className="text-slate-400 text-xs mb-1">Volatility</p>
            <p className="text-white font-semibold text-sm capitalize">{insights.volatility}</p>
          </div>
        </div>
      </div>

      {/* Recommendation */}
      <div className="bg-blue-500/10 border border-blue-500/50 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="text-blue-400 mt-1 flex-shrink-0" size={20} />
          <div>
            <p className="text-blue-300 font-semibold text-sm mb-2">Recommendation</p>
            <p className="text-blue-200 text-sm">{insights.recommendation}</p>
          </div>
        </div>
      </div>

      {/* Detailed Analysis */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <p className="text-slate-300 text-sm leading-relaxed">{insights.analysis}</p>
      </div>
    </div>
  );
}
