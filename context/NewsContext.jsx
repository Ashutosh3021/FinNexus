'use client';

import React, { createContext, useReducer, useEffect, useState } from 'react';
import { mockNews } from '@/lib/mockData';

export const NewsContext = createContext();

const initialState = {
  newsFeed: mockNews,
  selectedNews: null,
  selectedCategory: 'all',
};

const newsReducer = (state, action) => {
  switch (action.type) {
    case 'SET_SELECTED_NEWS':
      return { ...state, selectedNews: action.payload };
    case 'SET_CATEGORY':
      return { ...state, selectedCategory: action.payload };
    case 'SET_NEWS':
      return { ...state, newsFeed: action.payload };
    default:
      return state;
  }
};

export const NewsProvider = ({ children }) => {
  const [state, dispatch] = useReducer(newsReducer, initialState);

  // Load from localStorage on mount
  useEffect(() => {
    const savedNews = localStorage.getItem('finnexus_news');
    if (savedNews) {
      try {
        const parsedNews = JSON.parse(savedNews);
        dispatch({ type: 'SET_NEWS', payload: parsedNews.newsFeed });
      } catch (error) {
        console.error('Failed to parse saved news:', error);
      }
    }
  }, []);

  // Save to localStorage on every state change
  useEffect(() => {
    localStorage.setItem('finnexus_news', JSON.stringify(state));
  }, [state]);

  const setSelectedNews = (news) => {
    dispatch({ type: 'SET_SELECTED_NEWS', payload: news });
  };

  const setSelectedCategory = (category) => {
    dispatch({ type: 'SET_CATEGORY', payload: category });
  };

  const getFilteredNews = () => {
    if (state.selectedCategory === 'all') {
      return state.newsFeed;
    }
    return state.newsFeed.filter((news) => news.category === state.selectedCategory);
  };

  const getNewsByCategory = (category) => {
    return state.newsFeed.filter((news) => news.category === category);
  };

  const value = {
    newsFeed: state.newsFeed,
    selectedNews: state.selectedNews,
    selectedCategory: state.selectedCategory,
    filteredNews: getFilteredNews(),
    setSelectedNews,
    setSelectedCategory,
    getNewsByCategory,
  };

  return (
    <NewsContext.Provider value={value}>{children}</NewsContext.Provider>
  );
};

export const useNews = () => {
  const context = React.useContext(NewsContext);
  if (!context) {
    throw new Error('useNews must be used within NewsProvider');
  }
  return context;
};
