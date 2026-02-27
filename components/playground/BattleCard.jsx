'use client';

import React from 'react';
import { Loader2, Trophy, Frown, Bot, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function BattleCard({
  userPrediction = null,
  botPrediction = null,
  userResult = null,
  botResult = null,
  isRevealed = false,
  actualDirection = null,
  pnl = null,
  stake = 0,
}) {
  const win = userResult === 'win';
  const lose = userResult === 'loss';

  const UserSide = () => (
    <motion.div
      animate={isRevealed ? (win ? { scale: 1.03 } : { scale: 0.98 }) : { scale: 1 }}
      className={`flex-1 rounded-xl border p-5 bg-slate-800/70 ${win ? 'border-green-500/60' : lose ? 'border-red-500/60' : 'border-slate-700'}`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <User className="text-slate-300" size={18} />
          <span className="font-bold text-white">YOU</span>
        </div>
        {isRevealed && win && <Trophy className="text-yellow-400" size={18} />}
      </div>
      {!userPrediction && (
        <div className="h-24 flex items-center justify-center rounded-lg border border-slate-700 text-slate-400">
          Make your prediction
        </div>
      )}
      {userPrediction && !isRevealed && (
        <div className="h-24 flex flex-col items-center justify-center gap-2">
          <div className={`px-3 py-1 rounded-full text-sm ${userPrediction==='buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
            {userPrediction === 'buy' ? 'BUY 📈' : 'SELL 📉'}
          </div>
          <Loader2 className="animate-spin text-slate-400" size={18} />
        </div>
      )}
      {isRevealed && (
        <div className="h-24 flex flex-col items-center justify-center gap-1">
          <AnimatePresence>
            {win ? (
              <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="text-green-400 font-bold">
                +₹{Math.max(0, pnl || 0).toLocaleString()}
              </motion.div>
            ) : (
              <motion.div initial={{ y: -4, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="text-red-400 font-bold">
                -₹{Math.abs(pnl || 0).toLocaleString()}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );

  const BotSide = () => (
    <motion.div
      animate={isRevealed ? (botResult === 'win' ? { scale: 1.03 } : { scale: 0.98 }) : { scale: 1 }}
      className={`flex-1 rounded-xl border p-5 bg-slate-800/70 ${botResult==='win' ? 'border-green-500/60' : botResult==='loss' ? 'border-red-500/60' : 'border-slate-700'}`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bot className="text-slate-300" size={18} />
          <span className="font-bold text-white">BOT</span>
        </div>
      </div>
      {!userPrediction && (
        <div className="h-24 flex items-center justify-center text-slate-400">
          Waiting<span className="animate-pulse">...</span>
        </div>
      )}
      {userPrediction && !isRevealed && (
        <div className="h-24 flex flex-col items-center justify-center gap-2">
          <div className="text-slate-200">I disagree! 😤</div>
          <div className={`px-3 py-1 rounded-full text-sm ${botPrediction==='buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
            {botPrediction === 'buy' ? 'BUY 📈' : 'SELL 📉'}
          </div>
        </div>
      )}
      {isRevealed && (
        <div className="h-24 flex items-center justify-center">
          {botResult === 'win' ? (
            <div className="text-green-400">I told you so! 🤖</div>
          ) : (
            <div className="text-slate-300">We both got this wrong</div>
          )}
        </div>
      )}
    </motion.div>
  );

  return (
    <div className="relative flex items-stretch gap-6">
      <UserSide />
      <div className="flex items-center">
        <div className="text-slate-300 font-black tracking-widest text-2xl">VS</div>
      </div>
      <BotSide />
    </div>
  );
}

