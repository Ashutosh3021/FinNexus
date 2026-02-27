'use client';

import React, { createContext, useReducer, useEffect } from 'react';
import { mockPortfolio } from '@/lib/mockData';

export const PortfolioContext = createContext();

const initialState = {
  holdings: mockPortfolio,
};

const portfolioReducer = (state, action) => {
  switch (action.type) {
    case 'ADD_HOLDING':
      return {
        ...state,
        holdings: [...state.holdings, action.payload],
      };
    case 'REMOVE_HOLDING':
      return {
        ...state,
        holdings: state.holdings.filter((h) => h.id !== action.payload),
      };
    case 'UPDATE_HOLDING':
      return {
        ...state,
        holdings: state.holdings.map((h) =>
          h.id === action.payload.id ? action.payload : h
        ),
      };
    case 'SET_HOLDINGS':
      return { ...state, holdings: action.payload };
    default:
      return state;
  }
};

export const PortfolioProvider = ({ children }) => {
  const [state, dispatch] = useReducer(portfolioReducer, initialState);

  // Load from localStorage on mount
  useEffect(() => {
    const savedPortfolio = localStorage.getItem('finnexus_portfolio');
    if (savedPortfolio) {
      try {
        const parsedPortfolio = JSON.parse(savedPortfolio);
        dispatch({ type: 'SET_HOLDINGS', payload: parsedPortfolio.holdings });
      } catch (error) {
        console.error('Failed to parse saved portfolio:', error);
      }
    }
  }, []);

  // Save to localStorage on every state change
  useEffect(() => {
    localStorage.setItem('finnexus_portfolio', JSON.stringify(state));
  }, [state]);

  const addHolding = (holding) => {
    dispatch({ type: 'ADD_HOLDING', payload: holding });
  };

  const removeHolding = (id) => {
    dispatch({ type: 'REMOVE_HOLDING', payload: id });
  };

  const updateHolding = (holding) => {
    dispatch({ type: 'UPDATE_HOLDING', payload: holding });
  };

  const calculateTotalPnL = () => {
    return state.holdings.reduce((total, holding) => {
      const cost = holding.qty * holding.buyPrice;
      const current = holding.qty * holding.currentPrice;
      return total + (current - cost);
    }, 0);
  };

  const calculateTotalValue = () => {
    return state.holdings.reduce((total, holding) => {
      return total + holding.qty * holding.currentPrice;
    }, 0);
  };

  const calculateTotalCost = () => {
    return state.holdings.reduce((total, holding) => {
      return total + holding.qty * holding.buyPrice;
    }, 0);
  };

  const value = {
    holdings: state.holdings,
    addHolding,
    removeHolding,
    updateHolding,
    totalPnL: calculateTotalPnL(),
    totalValue: calculateTotalValue(),
    totalCost: calculateTotalCost(),
  };

  return (
    <PortfolioContext.Provider value={value}>{children}</PortfolioContext.Provider>
  );
};

export const usePortfolio = () => {
  const context = React.useContext(PortfolioContext);
  if (!context) {
    throw new Error('usePortfolio must be used within PortfolioProvider');
  }
  return context;
};
