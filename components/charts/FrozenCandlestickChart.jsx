'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

export default function FrozenCandlestickChart({
  chartData = [],
  predictionDate,
  revealData = null,
  isRevealed = false,
}) {
  const [drawnReveal, setDrawnReveal] = useState([]);
  const [phase, setPhase] = useState('idle');
  const lastCandle = drawnReveal[drawnReveal.length - 1] || null;
  const seqRef = useRef(null);

  const baseData = useMemo(() => {
    if (!predictionDate) return chartData;
    return chartData.filter(d => d.date <= predictionDate);
  }, [chartData, predictionDate]);

  const resultZone = useMemo(() => {
    if (!predictionDate || drawnReveal.length === 0) return null;
    return { start: predictionDate, end: drawnReveal[drawnReveal.length - 1].date };
  }, [predictionDate, drawnReveal]);

  useEffect(() => {
    if (!isRevealed || !revealData || revealData.length === 0) return;
    setPhase('pulse-line');
    const run = async () => {
      await new Promise(r => setTimeout(r, 750));
      setPhase('fade-overlay');
      await new Promise(r => setTimeout(r, 750));
      setPhase('draw-candles');
      for (let i = 0; i < revealData.length; i++) {
        setDrawnReveal(prev => [...prev, revealData[i]]);
        await new Promise(r => setTimeout(r, 50));
      }
      setPhase('finalize');
    };
    run();
    return () => seqRef.current && clearTimeout(seqRef.current);
  }, [isRevealed, JSON.stringify(revealData)]);

  const merged = useMemo(() => [...baseData, ...drawnReveal], [baseData, drawnReveal]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-600 rounded p-3 text-xs">
          <p className="text-white font-semibold mb-1">{d.date}</p>
          <p className="text-green-400">O: {d.open}</p>
          <p className="text-blue-400">H: {d.high}</p>
          <p className="text-orange-400">L: {d.low}</p>
          <p className={d.close >= d.open ? 'text-green-400' : 'text-red-400'}>C: {d.close}</p>
          <p className="text-slate-400 mt-1">Vol: {Math.round(d.volume/1e6)}M</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full relative">
      <div className="relative">
        <ResponsiveContainer width="100%" height={420}>
          <ComposedChart data={merged} margin={{ top: 20, right: 30, left: 0, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} angle={-30} textAnchor="end" height={60} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            {predictionDate && (
              <ReferenceLine
                x={predictionDate}
                stroke="#ef4444"
                strokeDasharray="6 6"
                label={{
                  value: 'PREDICT HERE',
                  position: 'top',
                  fill: '#ef4444',
                  fontWeight: 700,
                }}
                strokeWidth={phase === 'pulse-line' ? 3 : 2}
              />
            )}
            <Bar
              dataKey="close"
              name="Up Candles"
              data={merged}
              shape={(props) => {
                const { x, y, width, height, payload } = props;
                const up = payload.close >= payload.open;
                return (
                  <rect x={x} y={Math.min(y, y + height)} width={width} height={Math.abs(height)} fill={up ? '#10b981' : '#ef4444'} opacity={up ? 0.9 : 0.9} />
                );
              }}
              isAnimationActive={false}
            />
            {resultZone && (
              <ReferenceArea x1={resultZone.start} x2={resultZone.end} fill="#0ea5e9" fillOpacity={0.06} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
        {!isRevealed && (
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute inset-y-0 right-0 w-1/3 bg-gradient-to-l from-slate-900/70 to-transparent backdrop-blur-[1px]" />
          </div>
        )}
        {phase !== 'finalize' && isRevealed && (
          <AnimatePresence>
            {phase === 'fade-overlay' && (
              <motion.div
                initial={{ opacity: 0.6 }}
                animate={{ opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.75 }}
                className="pointer-events-none absolute inset-0 bg-slate-900/50"
              />
            )}
          </AnimatePresence>
        )}
      </div>
      <AnimatePresence>
        {lastCandle && phase === 'finalize' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`absolute -top-3 right-4 text-4xl ${lastCandle.close >= lastCandle.open ? 'text-green-400' : 'text-red-400'}`}
          >
            {lastCandle.close >= lastCandle.open ? '▲' : '▼'}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

