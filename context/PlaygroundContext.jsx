'use client';

import React, { createContext, useReducer, useEffect } from 'react';
import { mockPredictionHistory } from '@/lib/mockData';

export const PlaygroundContext = createContext();

const initialState = {
  currentRound: null,
  predictionHistory: mockPredictionHistory,
  streak: 3,
  totalRounds: mockPredictionHistory.length,
  wins: mockPredictionHistory.filter((p) => p.type === 'win').length,
};

const playgroundReducer = (state, action) => {
  switch (action.type) {
    case 'START_ROUND':
      return {
        ...state,
        currentRound: action.payload,
      };
    case 'SUBMIT_PREDICTION':
      const newPrediction = action.payload;
      const newStreak =
        newPrediction.type === 'win'
          ? state.streak + 1
          : 0;
      return {
        ...state,
        predictionHistory: [newPrediction, ...state.predictionHistory],
        streak: newStreak,
        totalRounds: state.totalRounds + 1,
        wins: newPrediction.type === 'win' ? state.wins + 1 : state.wins,
        currentRound: null,
      };
    case 'SET_HISTORY':
      return { ...state, predictionHistory: action.payload };
    default:
      return state;
  }
};

export const PlaygroundProvider = ({ children }) => {
  const [state, dispatch] = useReducer(playgroundReducer, initialState);

  // Load from localStorage on mount
  useEffect(() => {
    const savedPlayground = localStorage.getItem('finnexus_playground');
    if (savedPlayground) {
      try {
        const parsedData = JSON.parse(savedPlayground);
        dispatch({ type: 'SET_HISTORY', payload: parsedData.predictionHistory });
      } catch (error) {
        console.error('Failed to parse saved playground:', error);
      }
    }
  }, []);

  // Save to localStorage on every state change
  useEffect(() => {
    localStorage.setItem('finnexus_playground', JSON.stringify(state));
  }, [state]);

  const startRound = (round) => {
    dispatch({ type: 'START_ROUND', payload: round });
  };

  const submitPrediction = (prediction) => {
    dispatch({ type: 'SUBMIT_PREDICTION', payload: prediction });
  };

  const calculateWinRate = () => {
    if (state.totalRounds === 0) return 0;
    return ((state.wins / state.totalRounds) * 100).toFixed(2);
  };

  const value = {
    currentRound: state.currentRound,
    predictionHistory: state.predictionHistory,
    streak: state.streak,
    totalRounds: state.totalRounds,
    wins: state.wins,
    winRate: calculateWinRate(),
    startRound,
    submitPrediction,
  };

  return (
    <PlaygroundContext.Provider value={value}>{children}</PlaygroundContext.Provider>
  );
};

export const usePlayground = () => {
  const context = React.useContext(PlaygroundContext);
  if (!context) {
    throw new Error('usePlayground must be used within PlaygroundProvider');
  }
  return context;
};
