'use client';

import React from 'react';
import { Menu, Bell, User } from 'lucide-react';
import { useUser } from '@/context/UserContext';
import BackendStatus from '@/components/ui/BackendStatus';

export default function Navbar({ onMenuClick }) {
  const user = useUser();

  return (
    <nav className="bg-slate-800 border-b border-slate-700 h-16 flex items-center justify-between px-6">
      {/* Left: Menu Button & Logo */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu size={24} className="text-slate-300" />
        </button>
        <div className="text-xl font-bold text-blue-500">FinNexus</div>
      </div>

      {/* Right: Backend status, Balance, Notifications, Avatar */}
      <div className="flex items-center gap-6">
        <div className="hidden md:block">
          <BackendStatus />
        </div>
        {/* Virtual Balance Display */}
        <div className="text-sm hidden md:block">
          <div className="text-slate-400">Virtual Balance</div>
          <div className="text-lg font-semibold text-green-400">
            ${user?.virtualBalance?.toLocaleString('en-US', { maximumFractionDigits: 2 }) || '0.00'}
          </div>
        </div>

        {/* Notification Bell */}
        <button
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors relative"
          aria-label="Notifications"
        >
          <Bell size={20} className="text-slate-300" />
          <div className="absolute top-1 right-1 w-3 h-3 bg-red-500 rounded-full"></div>
        </button>

        {/* User Avatar */}
        <button className="flex items-center gap-2 hover:bg-slate-700 px-3 py-2 rounded-lg transition-colors">
          <img
            src={user?.avatar || '/placeholder-user.jpg'}
            alt={user?.name || 'User'}
            className="w-8 h-8 rounded-full"
          />
          <div className="hidden lg:block text-left">
            <div className="text-sm font-medium">{user?.name || 'User'}</div>
            <div className="text-xs text-slate-400">{user?.level || 'BEGINNER'}</div>
          </div>
        </button>
      </div>
    </nav>
  );
}
