'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Activity, TrendingUp, BookOpen, Zap, Brain } from 'lucide-react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, RadialBarChart, RadialBar } from 'recharts';

const TypingIndicator = () => (
  <div className="flex justify-start">
    <div className="bg-slate-700 p-3 rounded-tr-lg rounded-bl-lg flex gap-2">
      <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  </div>
);

export default function AdvisorPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        '👋 Hey! I\'m FinAdvisor. I have complete context about your portfolio, predictions, and learning progress. What would you like to discuss today?',
      actions: null
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [context, setContext] = useState(null);
  const [showProactiveInsight, setShowProactiveInsight] = useState(false);
  const chatEndRef = useRef(null);

  // Load context on mount
  useEffect(() => {
    fetchContextSummary();
  }, []);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchContextSummary = async () => {
    try {
      const res = await fetch('/api/advisor/context-summary');
      const data = await res.json();
      if (data.success) {
        setContext(data.data);
      }
    } catch (error) {
      console.error('Failed to load context:', error);
    }
  };

  const handleSendMessage = async (msg = input) => {
    if (!msg.trim() || isLoading) return;

    const userMessage = msg;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await fetch('/api/advisor/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: messages.map(m => ({
            role: m.role,
            content: typeof m.content === 'string' ? m.content : m.content.reply || ''
          })),
          user_context: {
            level: 'intermediate',
            virtual_balance: 100000,
            portfolio: context?.portfolio_summary || [],
            prediction_history: context?.prediction_stats?.recent_results || [],
            learning_progress: context?.learning_progress || {}
          }
        })
      });

      const data = await res.json();
      if (data.success) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.data, actions: data.data.suggested_actions }]);
        setShowProactiveInsight(!!data.data.proactive_insight);
      }
    } catch (error) {
      console.error('Chat failed:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: { reply: '❌ Sorry, I had trouble processing that.' } }]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickQuestions = [
    "Should I buy more crypto given today's news?",
    "Why do I keep losing crypto predictions?",
    "Is my portfolio too risky right now?",
    "What should I focus on learning next?"
  ];

  if (!context) {
    return (
      <div className="h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="flex gap-2 justify-center mb-4">
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce" />
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <p className="text-slate-400">Loading FinAdvisor context...</p>
        </div>
      </div>
    );
  }

  const { portfolio_summary, prediction_stats, news_headlines, learning_progress } = context;

  return (
    <div className="h-screen bg-slate-900 text-white flex gap-6 p-6">
      {/* LEFT SIDEBAR */}
      <div className="w-80 space-y-4 overflow-y-auto">
        {/* Portfolio Snapshot */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-slate-800 border border-slate-700 rounded-lg p-4"
        >
          <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
            <TrendingUp size={16} className="text-blue-400" />
            Portfolio Snapshot
          </h3>
          <div className="space-y-3">
            {/* Mini Pie Chart */}
            {portfolio_summary && portfolio_summary.holdings_count > 0 && (
              <div className="h-32 flex items-center justify-center">
                <ResponsiveContainer width="100%" height={120}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Stocks', value: 60 },
                        { name: 'Crypto', value: 30 },
                        { name: 'Bonds', value: 10 }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={35}
                      outerRadius={50}
                      dataKey="value"
                    >
                      <Cell fill="#3b82f6" />
                      <Cell fill="#f59e0b" />
                      <Cell fill="#10b981" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="text-xs text-slate-400">
              <p>Total Value</p>
              <p className="text-lg font-bold text-white">₹{portfolio_summary?.total_value?.toLocaleString() || '100,000'}</p>
            </div>
            <div className="text-xs">
              <span className="inline-block bg-green-500/20 text-green-400 px-2 py-1 rounded">+5.2% Today</span>
            </div>
          </div>
        </motion.div>

        {/* Prediction Performance */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-slate-800 border border-slate-700 rounded-lg p-4"
        >
          <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
            <Zap size={16} className="text-yellow-400" />
            Prediction Stats
          </h3>
          <div className="space-y-2">
            <div className="text-center py-2">
              <div className="text-4xl font-bold text-blue-400">{prediction_stats?.win_rate || 50}%</div>
              <p className="text-xs text-slate-400 mt-1">Win Rate</p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-700/50 p-2 rounded text-center">
                <p className="font-bold">{prediction_stats?.current_streak || 0}</p>
                <p className="text-slate-400">🔥 Streak</p>
              </div>
              <div className="bg-slate-700/50 p-2 rounded text-center">
                <p className="font-bold">{prediction_stats?.total_rounds || 0}</p>
                <p className="text-slate-400">Rounds</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Learning Progress */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-800 border border-slate-700 rounded-lg p-4"
        >
          <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
            <BookOpen size={16} className="text-purple-400" />
            Learning Progress
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span>Topics Completed</span>
                <span className="font-bold">{learning_progress?.completed_topics || 5}/{learning_progress?.total_topics || 20}</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${((learning_progress?.completed_topics || 5) / (learning_progress?.total_topics || 20)) * 100}%` }}
                  transition={{ duration: 1 }}
                  className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                />
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Weak Areas</p>
              <div className="flex flex-wrap gap-1">
                {(learning_progress?.weak_areas || ['Derivatives']).map((area, i) => (
                  <span key={i} className="text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded">
                    {area}
                  </span>
                ))}
              </div>
            </div>
            <div className="text-xs">
              <p className="text-slate-400">Currently studying</p>
              <p className="font-bold text-blue-300">{learning_progress?.current_topic || 'Market Analysis'}</p>
            </div>
          </div>
        </motion.div>

        {/* Market Pulse */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-800 border border-slate-700 rounded-lg p-4"
        >
          <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
            <Activity size={16} className="text-green-400" />
            Today's Market Pulse
          </h3>
          <div className="space-y-2">
            {(news_headlines || []).map((news, i) => {
              const sentimentColor = {
                positive: 'text-green-400 bg-green-500/10',
                negative: 'text-red-400 bg-red-500/10',
                neutral: 'text-slate-400 bg-slate-600/10'
              }[news.sentiment || 'neutral'] || 'text-slate-400';

              const sentimentDot = {
                positive: '🟢',
                negative: '🔴',
                neutral: '⚪'
              }[news.sentiment || 'neutral'] || '⚪';

              return (
                <button
                  key={i}
                  onClick={() => handleSendMessage(`Tell me about: ${news.headline}`)}
                  className="w-full text-left text-xs p-2 bg-slate-700/30 hover:bg-slate-700 rounded transition-colors"
                >
                  <p className="text-slate-300 line-clamp-2 mb-1">{sentimentDot} {news.headline}</p>
                  <p className={`text-xs font-semibold ${sentimentColor}`}>{news.sentiment?.toUpperCase() || 'NEUTRAL'}</p>
                </button>
              );
            })}
          </div>
        </motion.div>
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-4 mb-4"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
                <Brain size={20} />
              </div>
              <div>
                <h2 className="font-bold text-lg">FinAdvisor</h2>
                <div className="flex items-center gap-1 text-xs text-blue-100">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  Online
                </div>
              </div>
            </div>
            <div className="text-xs bg-purple-500/30 px-2 py-1 rounded">⚡ Powered by Gemini 2.5 Flash</div>
          </div>
          <div className="flex gap-4 text-xs text-blue-100">
            <span>✅ Context: Portfolio</span>
            <span>✅ News</span>
            <span>✅ Predictions</span>
          </div>
        </motion.div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 px-2">
          {messages.length === 1 && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center py-8">
              <div className="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center mx-auto mb-4">
                <Brain size={32} />
              </div>
              <p className="text-lg font-bold mb-2">Hello! I'm FinAdvisor</p>
              <p className="text-slate-300 text-sm mb-6 max-w-md mx-auto">
                I know your portfolio, predictions, and learning progress. Here's what I'm watching for you today...
              </p>
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6 text-left"
              >
                <p className="text-xs text-amber-300 font-semibold mb-1">💡 Proactive Insight</p>
                <p className="text-sm text-amber-100">Your win rate is solid at {prediction_stats?.win_rate || 50}%, but your weak areas in Derivatives could be causing losses. I recommend focusing on options strategies next.</p>
              </motion.div>
            </motion.div>
          )}

          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mr-3 text-sm">🤖</div>}
              <div className={`max-w-xl ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-l-lg rounded-tr-lg' : 'bg-slate-700 text-white rounded-r-lg rounded-tl-lg'} p-4`}>
                {typeof msg.content === 'string' ? (
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                ) : (
                  <div className="space-y-3">
                    <p className="text-sm leading-relaxed">{msg.content.reply}</p>

                    {/* Action chips */}
                    {msg.actions && msg.actions.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="flex flex-wrap gap-2 pt-2"
                      >
                        {msg.actions.map((action, i) => (
                          <a
                            key={i}
                            href={action.route}
                            className="text-xs bg-blue-500 hover:bg-blue-600 px-3 py-1 rounded transition-colors whitespace-nowrap"
                          >
                            {action.icon} {action.label}
                          </a>
                        ))}
                      </motion.div>
                    )}

                    {/* Proactive insight */}
                    {msg.content.proactive_insight && (
                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.6 }}
                        className="bg-amber-500/10 border-l-2 border-amber-500 p-2 mt-3"
                      >
                        <p className="text-xs text-amber-300 font-semibold mb-1">💡 Insight</p>
                        <p className="text-xs text-amber-100">{msg.content.proactive_insight}</p>
                      </motion.div>
                    )}
                  </div>
                )}
              </div>
              {msg.role === 'user' && <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0 ml-3 text-sm">👤</div>}
            </motion.div>
          ))}

          {isLoading && <TypingIndicator />}
          <div ref={chatEndRef} />
        </div>

        {/* Suggested questions (show only on first visit with >1 message) */}
        {messages.length <= 5 && !isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-2 gap-2 mb-4"
          >
            {quickQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(q)}
                className="text-xs bg-slate-700 hover:bg-slate-600 p-3 rounded transition-colors text-left text-slate-300 hover:text-white"
              >
                "{q}"
              </button>
            ))}
          </motion.div>
        )}

        {/* Input Area */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={isLoading}
              placeholder="Ask me anything... (Shift+Enter for new line)"
              className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 resize-none max-h-24"
              rows={2}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 px-4 py-3 rounded-lg transition-colors flex items-center gap-2 flex-shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2">{input.length} characters</p>
        </div>
      </div>
    </div>
  );
}
