'use client';

import React from 'react';
import { UserProvider } from '@/context/UserContext';
import { PortfolioProvider } from '@/context/PortfolioContext';
import { PlaygroundProvider } from '@/context/PlaygroundContext';
import { NewsProvider } from '@/context/NewsContext';

export function Providers({ children }) {
  return (
    <UserProvider>
      <PortfolioProvider>
        <PlaygroundProvider>
          <NewsProvider>
            {children}
          </NewsProvider>
        </PlaygroundProvider>
      </PortfolioProvider>
    </UserProvider>
  );
}
