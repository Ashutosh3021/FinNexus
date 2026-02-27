'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Lightbulb, BookOpen, TrendingUp, Brain, Zap, CircleHelp } from 'lucide-react';
import { useUser } from '@/context/UserContext';

export default function ExplanationModal({
  isOpen,
  onClose,
  explanation,
  userResult,
  pnl,
  asset,
}) {
  const user = useUser();
  const [countPnl, setCountPnl] = useState(0);
  const oldBalance = useMemo(() => user?.virtualBalance || 0, [user?.virtualBalance]);
  const newBalance = oldBalance + pnl;

  useEffect(() => {
    if (!isOpen) return;
    let start = 0;
    const step = () => {
      start += Math.max(1, Math.floor(Math.abs(pnl) / 30));
      if (start >= Math.abs(pnl)) start = Math.abs(pnl);
      setCountPnl(start);
      if (start < Math.abs(pnl)) requestAnimationFrame(step);
    };
    setCountPnl(0);
    requestAnimationFrame(step);
  }, [isOpen, pnl]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[120] bg-slate-900/70 backdrop-blur"
        >
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ duration: 0.4 }}
            className="absolute inset-x-0 bottom-0 top-10 rounded-t-2xl bg-slate-900 border-t border-slate-700"
          >
            <div className="p-6 space-y-4 h-full overflow-y-auto">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {userResult === 'win' ? (
                    <Trophy className="text-yellow-400" />
                  ) : (
                    <CircleHelp className="text-amber-400" />
                  )}
                  <div className={`text-2xl font-bold ${userResult==='win' ? 'text-green-400' : 'text-amber-400'}`}>
                    {userResult === 'win' ? 'YOU WON!' : 'Tough Break'}
                  </div>
                </div>
                <button onClick={onClose} className="text-slate-300 hover:text-white">Close</button>
              </div>

              <div className="rounded-lg border border-slate-700 p-4 bg-slate-800/60">
                <div className="text-sm text-slate-300">P&L</div>
                <div className={`text-3xl font-bold ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {pnl >= 0 ? '+' : '-'}₹{countPnl.toLocaleString()}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { title: 'What Happened', icon: TrendingUp, color: 'border-blue-500' , key: 'what_happened'},
                  { title: 'Your Analysis', icon: Brain, color: userResult==='win' ? 'border-green-500' : 'border-red-500', key: 'why_user_was_right_or_wrong' },
                  { title: "Bot's Analysis", icon: Lightbulb, color: 'border-purple-500', key: 'why_bot_was_right_or_wrong' },
                  { title: 'Key Signal', icon: Zap, color: 'border-yellow-500', key: 'key_signal_that_decided_it' },
                  { title: 'Pro Trader View', icon: Trophy, color: 'border-slate-500', key: 'what_pro_would_do' },
                  { title: 'Learn More', icon: BookOpen, color: 'border-indigo-500', key: 'lesson_topic', link: 'lesson_link' },
                ].map((c, idx) => (
                  <motion.div
                    key={c.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 * idx }}
                    className={`rounded-lg border ${c.color} p-4 bg-slate-800/60`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <c.icon className="text-slate-300" size={18} />
                      <div className="font-semibold text-white">{c.title}</div>
                    </div>
                    <div className={`${c.title==='Key Signal' ? 'animate-pulse' : ''} text-slate-300 text-sm`}>
                      {explanation?.[c.key]}
                    </div>
                    {c.link && explanation?.[c.link] && (
                      <a href={explanation[c.link]} target="_blank" className="inline-block mt-3 text-indigo-300 hover:text-indigo-200 text-sm underline">
                        Learn this topic
                      </a>
                    )}
                  </motion.div>
                ))}
              </div>

              <div className="mt-2 rounded-lg border border-slate-700 p-4 bg-slate-800/60">
                <div className="text-xs text-slate-400 mb-2">Balance Update</div>
                <div className="flex items-center gap-3">
                  <div className="font-mono text-slate-300">₹{oldBalance.toLocaleString()}</div>
                  <div className="text-slate-400">→</div>
                  <div className="font-mono text-white">₹{newBalance.toLocaleString()}</div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button onClick={onClose} className="px-4 py-2 rounded bg-slate-700 text-slate-200">Play Again</button>
                {explanation?.lesson_link && (
                  <a href={explanation.lesson_link} target="_blank" className="px-4 py-2 rounded bg-indigo-600 text-white">
                    Learn This Topic
                  </a>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

