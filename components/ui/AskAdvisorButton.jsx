'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePathname } from 'next/navigation';

export default function AskAdvisorButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [contextPreFill, setContextPreFill] = useState('');
  const pathname = usePathname();
  const messagesEndRef = useRef(null);

  // Set pre-fill based on current page
  useEffect(() => {
    const prefills = {
      '/news': "I want to ask about the latest news",
      '/portfolio': "I want to discuss my portfolio",
      '/playground': "I want to understand my last prediction",
      '/learn': "I need help with {current_topic}"
    };

    const currentPrefill = Object.entries(prefills).find(([path]) => pathname.startsWith(path));
    if (currentPrefill) {
      setContextPreFill(currentPrefill[1]);
    }
  }, [pathname]);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input;
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
            portfolio: [],
            prediction_history: [],
            learning_progress: {}
          }
        })
      });

      const data = await res.json();
      if (data.success) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.data }]);
      }
    } catch (error) {
      console.error('Chat failed:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: { reply: '❌ Sorry, I had trouble processing that.' } }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5 }}
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-8 right-8 z-90 w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all flex items-center justify-center"
        title="Ask FinAdvisor"
      >
        <AnimatePresence>
          {isOpen ? (
            <motion.div key="close" initial={{ rotate: -90 }} animate={{ rotate: 0 }} exit={{ rotate: 90 }}>
              <X size={24} />
            </motion.div>
          ) : (
            <motion.div key="open" initial={{ rotate: 90 }} animate={{ rotate: 0 }} exit={{ rotate: -90 }}>
              <MessageCircle size={24} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Mini Drawer */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed bottom-0 right-0 z-99 w-96 h-[600px] bg-slate-800 border-l border-slate-700 shadow-2xl rounded-tl-lg flex flex-col"
          >
            {/* Mini Drawer Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-4 rounded-tl-lg">
              <h3 className="font-bold text-white flex items-center gap-2">
                <MessageCircle size={18} />
                FinAdvisor
              </h3>
              <p className="text-xs text-blue-100 mt-1">Quick question mode</p>
            </div>

            {/* Context Pre-fill (show on open if empty) */}
            {messages.length === 0 && contextPreFill && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="px-4 pt-3 pb-2"
              >
                <p className="text-xs text-slate-400 mb-2">Suggested context:</p>
                <button
                  onClick={() => handleSendMessage()}
                  className="w-full text-left text-xs bg-slate-700/50 hover:bg-slate-700 p-2 rounded text-blue-300 hover:text-blue-200 transition-colors"
                >
                  {contextPreFill}
                </button>
              </motion.div>
            )}

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 && (
                <div className="text-center py-6">
                  <div className="text-4xl mb-2">🤖</div>
                  <p className="text-sm text-slate-400">Ask me anything about your finances</p>
                </div>
              )}

              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs text-xs p-2 rounded ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white rounded-bl-lg'
                        : 'bg-slate-700 text-slate-100 rounded-br-lg'
                    }`}
                  >
                    {typeof msg.content === 'string' ? msg.content : msg.content.reply}
                  </div>
                </motion.div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-700 p-2 rounded-br-lg flex gap-1">
                    <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '100ms' }} />
                    <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="bg-slate-700 border-t border-slate-600 p-3 space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !isLoading) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  disabled={isLoading}
                  placeholder="Type your question..."
                  className="flex-1 bg-slate-600 border border-slate-500 rounded px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading || !input.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white p-2 rounded transition-colors"
                >
                  <Send size={16} />
                </button>
              </div>

              {/* Full Advisor Button */}
              <a
                href="/advisor"
                className="block w-full text-center text-xs bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white py-2 rounded transition-all"
              >
                Open Full Advisor
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
