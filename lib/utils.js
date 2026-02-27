// Utility functions for FinNexus

export const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const formatPercent = (value, decimals = 2) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

export const calculatePnL = (currentPrice, buyPrice, quantity) => {
  const currentValue = currentPrice * quantity;
  const costValue = buyPrice * quantity;
  const pnl = currentValue - costValue;
  const pnlPercent = (pnl / costValue) * 100;

  return { pnl, pnlPercent };
};

export const calculatePortfolioMetrics = (holdings) => {
  const totalCost = holdings.reduce((sum, h) => sum + h.qty * h.buyPrice, 0);
  const totalValue = holdings.reduce((sum, h) => sum + h.qty * h.currentPrice, 0);
  const totalPnL = totalValue - totalCost;
  const totalPnLPercent = (totalPnL / totalCost) * 100;

  return {
    totalCost,
    totalValue,
    totalPnL,
    totalPnLPercent,
  };
};

export const getAssetTypeColor = (type) => {
  const colors = {
    stock: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
    crypto: { bg: 'bg-yellow-500/10', text: 'text-yellow-400' },
    commodity: { bg: 'bg-orange-500/10', text: 'text-orange-400' },
    etf: { bg: 'bg-purple-500/10', text: 'text-purple-400' },
  };
  return colors[type] || { bg: 'bg-slate-500/10', text: 'text-slate-400' };
};

export const getLevelColor = (level) => {
  const colors = {
    BEGINNER: { bg: 'bg-green-500/10', text: 'text-green-400' },
    INTERMEDIATE: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
    ADVANCED: { bg: 'bg-purple-500/10', text: 'text-purple-400' },
  };
  return colors[level] || { bg: 'bg-slate-500/10', text: 'text-slate-400' };
};

export const calculateWinRate = (wins, total) => {
  if (total === 0) return 0;
  return ((wins / total) * 100).toFixed(2);
};

export const formatDate = (date) => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatTime = (date) => {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const truncateText = (text, length) => {
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
};

export const generateId = () => {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};
