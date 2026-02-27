'use client';

import React, { useEffect, useMemo, useState, Suspense } from 'react';
import LiveTickerBar from '@/components/ui/LiveTickerBar';
import FrozenCandlestickChart from '@/components/charts/FrozenCandlestickChart';
import BattleCard from '@/components/playground/BattleCard';
import ExplanationModal from '@/components/playground/ExplanationModal';
import PredictionBar from '@/components/playground/PredictionBar';
import { useUser } from '@/context/UserContext';
import { mockCandleData } from '@/lib/mockData';

const API = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || '') : '';

function PlaygroundContent() {
  const user = useUser();
  const [state, setState] = useState('IDLE');
  const [category, setCategory] = useState('Stocks');
  const [timeframe, setTimeframe] = useState('1D');
  const [asset, setAsset] = useState('AAPL');
  const [frozenData, setFrozenData] = useState([]);
  const [predictionDate, setPredictionDate] = useState('');
  const [revealData, setRevealData] = useState(null);
  const [userPrediction, setUserPrediction] = useState(null);
  const [botPrediction, setBotPrediction] = useState(null);
  const [result, setResult] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  const assetsByCategory = useMemo(() => ({
    Stocks: ['AAPL','GOOGL','TSLA','MSFT'],
    Crypto: ['BTC','ETH'],
    Gold: ['GOLD'],
    Forex: ['USDINR'],
    Indices: ['SPY','^GSPC','^NSEI'],
  }), []);

  useEffect(() => {
    const startRound = async () => {
      setState('LOADING_ROUND');
      try {
        const res = await fetch(`${API}/playground/start`, { method: 'POST' });
        if (!res.ok) throw new Error('fail');
        const data = await res.json();
        setFrozenData(data.chartData || []);
        setPredictionDate(data.predictionDate);
        setState('READY_TO_PREDICT');
      } catch {
        const data = mockCandleData[asset] || [];
        setFrozenData(data);
        setPredictionDate(data[Math.floor(data.length/2)]?.date || '');
        setState('READY_TO_PREDICT');
      }
    };
    startRound();
  }, [asset, timeframe]);

  const handlePredict = async (pred, stake) => {
    if (state !== 'READY_TO_PREDICT') return;
    setState('PREDICTED');
    setUserPrediction(pred === 'buy' ? 'buy' : 'sell');
    setBotPrediction(pred === 'buy' ? 'sell' : 'buy');
    try {
      await fetch(`${API}/playground/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset, prediction: pred, stake }),
      });
    } catch {}
  };

  const handleReveal = async () => {
    if (state !== 'PREDICTED') return;
    setState('REVEALING');
    try {
      const res = await fetch(`${API}/playground/reveal`, { method: 'POST' });
      const data = res.ok ? await res.json() : null;
      const rev = data?.revealData || frozenData.slice(frozenData.findIndex(d => d.date === predictionDate)+1);
      setRevealData(rev);
      const dirUp = (rev[rev.length-1]?.close || 0) >= (rev[rev.length-1]?.open || 0);
      const actualDirection = dirUp ? 'up' : 'down';
      const win = (userPrediction === 'buy' && dirUp) || (userPrediction === 'sell' && !dirUp);
      const pnl = win ? Math.round((Math.random()*0.04+0.01)*1000) : -Math.round((Math.random()*0.03+0.01)*1000);
      setResult({ userResult: win ? 'win' : 'loss', botResult: win ? 'loss' : 'win', actualDirection, pnl });
      setExplanation(data?.explanation || {
        what_happened: 'Price reacted to recent catalysts and trend continuation.',
        why_user_was_right_or_wrong: win ? 'You aligned with the prevailing momentum.' : 'Momentum faded after resistance.',
        why_bot_was_right_or_wrong: win ? 'Bot misread the pullback.' : 'Bot followed overbought signals.',
        key_signal_that_decided_it: dirUp ? 'RSI breakout above 60' : 'MACD bearish cross',
        what_pro_would_do: 'Wait for confirmation near support and size accordingly.',
        lesson_topic: dirUp ? 'RSI Momentum' : 'MACD Divergences',
        lesson_link: 'https://www.investopedia.com/terms/r/rsi.asp',
      });
      setTimeout(() => setState('REVEALED'), 1800);
      setTimeout(() => setModalOpen(true), 2200);
    } catch {
      const rev = frozenData.slice(frozenData.findIndex(d => d.date === predictionDate)+1);
      setRevealData(rev);
      const dirUp = (rev[rev.length-1]?.close || 0) >= (rev[rev.length-1]?.open || 0);
      const win = (userPrediction === 'buy' && dirUp) || (userPrediction === 'sell' && !dirUp);
      const pnl = win ? 1200 : -800;
      setResult({ userResult: win ? 'win' : 'loss', botResult: win ? 'loss' : 'win', actualDirection: dirUp ? 'up' : 'down', pnl });
      setTimeout(() => setState('REVEALED'), 1800);
      setTimeout(() => setModalOpen(true), 2200);
    }
  };

  return (
    <div className="pt-10">
      <LiveTickerBar />
      <div className="p-4 space-y-4 max-w-6xl mx-auto">
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {['Stocks','Crypto','Gold','Forex','Indices'].map(cat => (
              <button key={cat} onClick={() => setCategory(cat)} className={`px-3 py-1.5 rounded border text-sm ${category===cat ? 'bg-slate-700 border-slate-500' : 'bg-slate-800 border-slate-700'}`}>
                {cat}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            {['1D','1W','1M'].map(tf => (
              <button key={tf} onClick={() => setTimeframe(tf)} className={`px-3 py-1.5 rounded border text-sm ${timeframe===tf ? 'bg-slate-700 border-slate-500' : 'bg-slate-800 border-slate-700'}`}>
                {tf}
              </button>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          {assetsByCategory[category].map(sym => (
            <button key={sym} onClick={() => setAsset(sym)} className={`px-2.5 py-1 rounded border text-xs ${asset===sym ? 'bg-blue-600 text-white border-blue-500' : 'bg-slate-800 border-slate-700 text-slate-200'}`}>
              {sym}
            </button>
          ))}
        </div>
        <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-4">
          <FrozenCandlestickChart
            chartData={frozenData}
            predictionDate={predictionDate}
            revealData={revealData}
            isRevealed={state==='REVEALED' || state==='REVEALING'}
          />
        </div>
        <BattleCard
          userPrediction={userPrediction}
          botPrediction={botPrediction}
          userResult={result?.userResult || null}
          botResult={result?.botResult || null}
          isRevealed={state==='REVEALED' || state==='REVEALING'}
          actualDirection={result?.actualDirection || null}
          pnl={result?.pnl || null}
          stake={0}
        />
      </div>
      <PredictionBar
        onPredict={(p, s) => { setTimeout(handleReveal, 300); handlePredict(p, s); }}
        virtualBalance={user?.virtualBalance || 0}
        isDisabled={state!=='READY_TO_PREDICT'}
        hasChosen={!!userPrediction}
      />
      <ExplanationModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setState('EXPLAINED'); }}
        explanation={explanation}
        userResult={result?.userResult === 'win' ? 'win' : 'loss'}
        pnl={result?.pnl || 0}
        asset={asset}
      />
    </div>
  );
}

export default function PlaygroundPage() {
  return (
    <Suspense fallback={<div className="p-6 text-slate-300">Loading...</div>}>
      <PlaygroundContent />
    </Suspense>
  );
}
