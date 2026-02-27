'use client';

import React, { createContext, useReducer, useEffect } from 'react';
import { mockUser } from '@/lib/mockData';

export const UserContext = createContext();

const initialState = mockUser;

const userReducer = (state, action) => {
  switch (action.type) {
    case 'UPDATE_BALANCE':
      return { ...state, virtualBalance: state.virtualBalance + action.payload };
    case 'UPDATE_XP':
      return { ...state, xp: state.xp + action.payload };
    case 'UPDATE_LEVEL':
      return { ...state, level: action.payload };
    case 'SET_USER':
      return action.payload;
    default:
      return state;
  }
};

export const UserProvider = ({ children }) => {
  const [state, dispatch] = useReducer(userReducer, initialState);

  // Load from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('finnexus_user');
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        dispatch({ type: 'SET_USER', payload: parsedUser });
      } catch (error) {
        console.error('Failed to parse saved user:', error);
      }
    }
  }, []);

  // Save to localStorage on every state change
  useEffect(() => {
    localStorage.setItem('finnexus_user', JSON.stringify(state));
  }, [state]);

  const updateBalance = (amount) => {
    dispatch({ type: 'UPDATE_BALANCE', payload: amount });
  };

  const updateXP = (amount) => {
    dispatch({ type: 'UPDATE_XP', payload: amount });
  };

  const updateLevel = (level) => {
    dispatch({ type: 'UPDATE_LEVEL', payload: level });
  };

  const value = {
    ...state,
    updateBalance,
    updateXP,
    updateLevel,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export const useUser = () => {
  const context = React.useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
};
