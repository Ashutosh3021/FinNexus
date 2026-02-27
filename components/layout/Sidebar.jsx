'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  BookOpen,
  Gamepad2,
  Newspaper,
  Briefcase,
  Bot,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { useUser } from '@/context/UserContext';

export default function Sidebar({ isOpen, setIsOpen }) {
  const pathname = usePathname();
  const user = useUser();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/learn', label: 'Learn', icon: BookOpen },
    { href: '/playground', label: 'Playground', icon: Gamepad2 },
    { href: '/news', label: 'News', icon: Newspaper },
    { href: '/portfolio', label: 'Portfolio', icon: Briefcase },
    { href: '/advisor', label: 'AI Advisor', icon: Bot },
  ];

  const isActive = (href) => pathname === href || pathname.startsWith(href + '/');

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`${
          isOpen ? 'w-60' : 'w-0'
        } bg-slate-800 border-r border-slate-700 overflow-y-auto transition-all duration-300 fixed md:relative h-full z-50 md:z-auto flex flex-col`}
      >
        {/* Sidebar Content */}
        <div className="p-6 flex-1">
          {/* User Level Badge */}
          <div className="mb-8">
            <div className="bg-slate-700 rounded-lg p-4">
              <div className="text-xs text-slate-400 mb-2">Current Level</div>
              <div className="text-lg font-bold text-blue-400 mb-3">{user?.level || 'BEGINNER'}</div>

              {/* XP Progress Bar */}
              <div className="mb-2">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">XP Progress</span>
                  <span className="text-blue-400">{user?.xp || 0} / 10000</span>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(((user?.xp || 0) / 10000) * 100, 100)}%`,
                    }}
                  ></div>
                </div>
              </div>

              {/* XP Gain Button */}
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2 mt-3">
                <Zap size={16} />
                Earn XP
              </button>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
                    active
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  <span className="flex items-center gap-3">
                    <Icon size={20} />
                    <span className="font-medium">{item.label}</span>
                  </span>
                  {active && <ChevronRight size={16} />}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer Info */}
        <div className="p-6 border-t border-slate-700">
          <p className="text-xs text-slate-400 text-center">
            FinNexus v1.0 • Learn & Trade
          </p>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 md:hidden z-40"
          onClick={() => setIsOpen(false)}
        ></div>
      )}
    </>
  );
}
