'use client';

import React from 'react';
import { Calendar, AlertCircle, TrendingUp, TrendingDown, Zap } from 'lucide-react';

export function HistoricalEventsTimeline({ events = [], symbol = 'ASSET' }) {
  if (!events || events.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="text-slate-400" size={20} />
          <h3 className="text-lg font-semibold text-white">Historical Events</h3>
        </div>
        <p className="text-slate-400 text-center py-8">No historical events found for {symbol}</p>
      </div>
    );
  }

  const getEventIcon = (category) => {
    switch (category) {
      case 'earnings':
        return <Zap className="text-yellow-400" size={18} />;
      case 'macro':
        return <AlertCircle className="text-blue-400" size={18} />;
      case 'regulatory':
        return <AlertCircle className="text-purple-400" size={18} />;
      case 'crypto':
        return <Zap className="text-orange-400" size={18} />;
      default:
        return <AlertCircle className="text-slate-400" size={18} />;
    }
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'positive':
        return 'bg-green-500/20 border-green-500/50 text-green-300';
      case 'negative':
        return 'bg-red-500/20 border-red-500/50 text-red-300';
      case 'neutral':
        return 'bg-slate-600/20 border-slate-500/50 text-slate-300';
      default:
        return 'bg-slate-600/20 border-slate-500/50 text-slate-300';
    }
  };

  const getCategoryBadge = (category) => {
    const categoryColor = {
      earnings: 'bg-yellow-500/20 text-yellow-300',
      macro: 'bg-blue-500/20 text-blue-300',
      regulatory: 'bg-purple-500/20 text-purple-300',
      crypto: 'bg-orange-500/20 text-orange-300',
    };
    return categoryColor[category] || 'bg-slate-600/20 text-slate-300';
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-6">
        <Calendar className="text-blue-400" size={20} />
        <h3 className="text-lg font-semibold text-white">Historical Events & News</h3>
      </div>

      <div className="space-y-4">
        {events.map((event, index) => (
          <div
            key={`${event.date}-${index}`}
            className={`border-l-4 pl-4 py-3 ${
              event.impact === 'positive'
                ? 'border-green-500 bg-green-500/5'
                : event.impact === 'negative'
                ? 'border-red-500 bg-red-500/5'
                : 'border-slate-500 bg-slate-500/5'
            }`}
          >
            {/* Event Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                {getEventIcon(event.category)}
                <div>
                  <p className="text-white font-semibold text-sm">{event.event}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Calendar size={12} />
                      {event.date}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded capitalize ${getCategoryBadge(event.category)}`}>
                      {event.category}
                    </span>
                  </div>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-xs font-semibold capitalize flex items-center gap-1 ${getImpactColor(event.impact)}`}>
                {event.impact === 'positive' ? (
                  <TrendingUp size={14} />
                ) : event.impact === 'negative' ? (
                  <TrendingDown size={14} />
                ) : null}
                {event.impact}
              </div>
            </div>

            {/* Event Description */}
            <p className="text-slate-300 text-sm leading-relaxed">{event.description}</p>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-slate-700">
        <p className="text-slate-400 text-xs font-semibold mb-3">Event Categories:</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-yellow-400" />
            <span className="text-slate-400">Earnings</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle size={14} className="text-blue-400" />
            <span className="text-slate-400">Macro</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle size={14} className="text-purple-400" />
            <span className="text-slate-400">Regulatory</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-orange-400" />
            <span className="text-slate-400">Crypto News</span>
          </div>
        </div>
      </div>
    </div>
  );
}
