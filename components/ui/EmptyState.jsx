'use client';

import React from 'react';
import { AlertCircle, TrendingUp, Zap } from 'lucide-react';

export function EmptyState({ 
  icon: Icon = AlertCircle, 
  title = 'No data available',
  description = 'Data will appear here once you start using the platform',
  action = null,
  variant = 'default'
}) {
  const getIconColor = () => {
    switch (variant) {
      case 'success':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-blue-400';
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-64 py-12 px-4">
      <div className={`${getIconColor()} mb-4`}>
        <Icon size={48} />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2 text-center">
        {title}
      </h3>
      <p className="text-sm text-slate-400 text-center mb-6 max-w-sm">
        {description}
      </p>
      {action && (
        <div className="mt-4">
          {action}
        </div>
      )}
    </div>
  );
}

export function DataLoadingState() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-64 py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
      <p className="text-slate-400">Loading your data...</p>
    </div>
  );
}
