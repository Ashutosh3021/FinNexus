'use client';

import React, { useEffect, useRef, useState } from 'react';
import { TrendingUp, TrendingDown, Bot } from 'lucide-react';

export default function PredictionBar({
  onPredict,
  virtualBalance = 0,
  isDisabled = false,
  hasChosen = false,
}) {
  const [stake, setStake] = useState(0);
  const [choice, setChoice] = useState(null);
  const revealRef = useRef(null);

  useEffect(() => {
    setStake(Math.min(1000, Math.max(0, virtualBalance)));
  }, [virtualBalance]);

  const handleChoose = (dir) => {
    if (isDisabled) return;
    setChoice(dir);
  };

  const handleReveal = () => {
    if (!choice) return;
    onPredict(choice, stake);
  };

  return (
    <div className="fixed bottom-0 inset-x-0 z-[90]">
      <div className="mx-auto max-w-6xl">
        <div className="m-3 rounded-2xl border border-slate-700 bg-slate-900/80 backdrop-blur px-4 py-3">
          <div className="flex items-center gap-4">
            <div className="text-slate-300 whitespace-nowrap">💰 ₹{Math.floor(virtualBalance).toLocaleString()}</div>
            <div className="flex items-center gap-3 flex-1 justify-center">
              <button
                onClick={() => handleChoose('buy')}
                disabled={isDisabled}
                className={`px-4 py-2 rounded-lg border text-sm flex items-center gap-2 ${choice==='buy' ? 'bg-green-600 text-white border-green-500' : 'bg-green-600/20 text-green-300 border-green-600/60'} disabled:opacity-50`}
              >
                <TrendingUp size={16} />
                BUY
              </button>
              <div className="flex items-center gap-2">
                <span className="text-slate-400 text-sm whitespace-nowrap">Stake: ₹</span>
                <input
                  type="number"
                  value={stake}
                  onChange={(e) => setStake(Math.min(virtualBalance, Math.max(0, Number(e.target.value) || 0)))}
                  className="w-28 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white text-sm"
                />
              </div>
              <button
                onClick={() => handleChoose('sell')}
                disabled={isDisabled}
                className={`px-4 py-2 rounded-lg border text-sm flex items-center gap-2 ${choice==='sell' ? 'bg-red-600 text-white border-red-500' : 'bg-red-600/20 text-red-300 border-red-600/60'} disabled:opacity-50`}
              >
                <TrendingDown size={16} />
                SELL
              </button>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-slate-300 whitespace-nowrap">
              <Bot size={16} className="text-purple-400" />
              <span>Bot picks OPPOSITE</span>
            </div>
            {choice && (
              <button
                ref={revealRef}
                onClick={handleReveal}
                className="ml-auto px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold animate-pulse"
              >
                REVEAL
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

