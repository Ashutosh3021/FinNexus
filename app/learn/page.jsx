'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, BookOpen, Lightbulb, ArrowRight, Send, Sparkles } from 'lucide-react';

const TypewriterText = ({ text, speed = 30 }) => {
  const [displayedText, setDisplayedText] = useState('');
  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.substring(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);
  return <div>{displayedText}</div>;
};

export default function LearnPage() {
  const [userLevel, setUserLevel] = useState('BEGINNER');
  const [topics, setTopics] = useState({});
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', content: '👋 Hey! I\'m FinMentor. What would you like to learn about today? Feel free to ask about any financial concept!' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Load topics on mount
  useEffect(() => {
    fetchTopics();
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const fetchTopics = async () => {
    try {
      const res = await fetch('/api/education/topics');
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      if (data.success) {
        setTopics(data.data || {});
      }
    } catch (error) {
      console.error('Failed to load topics:', error);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`/api/education/search?q=${encodeURIComponent(searchQuery)}&level=${userLevel}`);
      const data = await res.json();
      setSearchResults(data.data || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (message = input) => {
    if (!message.trim() || loading) return;

    const newMessage = message;
    setInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: newMessage }]);
    setLoading(true);

    try {
      const res = await fetch('/api/education/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: newMessage,
          user_level: userLevel,
          include_market_data: true
        })
      });

      const data = await res.json();
      if (data.success) {
        const lesson = data.data;
        setChatHistory(prev => [...prev, {
          role: 'assistant',
          content: lesson
        }]);
      }
    } catch (error) {
      console.error('Query failed:', error);
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: { explanation: '❌ Sorry, I couldn\'t process that. Try again!' }
      }]);
    } finally {
      setLoading(false);
    }
  };

  const quickChips = ['RSI indicator', 'Portfolio diversification', 'Risk management', 'Bull markets'];
  const currentLevel = userLevel.toLowerCase();
  const levelTopics = topics[userLevel] || [];

  return (
    <div className="h-screen bg-slate-900 text-white flex">
      {/* Left Panel - Topics & Search */}
      <div className="w-80 bg-slate-800 border-r border-slate-700 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-700">
          <h1 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <BookOpen size={24} className="text-blue-400" />
            FinLearner
          </h1>
          <p className="text-xs text-slate-400">Master finance, one concept at a time</p>
        </div>

        {/* Search Bar */}
        <div className="p-4 border-b border-slate-700">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search lessons..."
              className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 p-2 rounded-lg transition-colors"
            >
              <Search size={18} />
            </button>
          </form>
        </div>

        {/* Level Tabs */}
        <div className="p-4 border-b border-slate-700 flex gap-2">
          {['BEGINNER', 'INTERMEDIATE', 'ADVANCED'].map(level => (
            <button
              key={level}
              onClick={() => {
                setUserLevel(level);
                setSearchResults([]);
              }}
              className={`flex-1 px-2 py-2 rounded-lg text-xs font-semibold transition-all ${
                userLevel === level
                  ? level === 'BEGINNER'
                    ? 'bg-green-500/30 text-green-400 border border-green-500'
                    : level === 'INTERMEDIATE'
                    ? 'bg-blue-500/30 text-blue-400 border border-blue-500'
                    : 'bg-purple-500/30 text-purple-400 border border-purple-500'
                  : 'bg-slate-700 text-slate-300 border border-slate-600 hover:border-slate-500'
              }`}
            >
              {level.slice(0, 3)}
            </button>
          ))}
        </div>

        {/* Search Results or Topics */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {searchResults.length > 0 ? (
            // Search Results View
            <div className="space-y-2">
              <p className="text-xs text-slate-400 font-semibold">SEARCH RESULTS</p>
              {searchResults.map((result, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    handleSendMessage(`Tell me more about ${result.topic || result.title}`);
                    setSearchResults([]);
                  }}
                  className="w-full text-left p-3 bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors group"
                >
                  <p className="text-sm font-medium text-blue-300 group-hover:text-blue-200">{result.title || result.topic}</p>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">{result.content?.substring(0, 60)}...</p>
                </button>
              ))}
            </div>
          ) : (
            // Topics View
            <div className="space-y-4">
              <p className="text-xs text-slate-400 font-semibold">{userLevel} TOPICS</p>
              {levelTopics.map((topic, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setSelectedTopic(topic);
                    handleSendMessage(`Explain ${topic}`);
                  }}
                  className="w-full text-left p-3 bg-slate-700/30 hover:bg-slate-700/60 rounded-lg transition-all border border-slate-600 hover:border-blue-500 group"
                >
                  <p className="font-medium text-white group-hover:text-blue-300 transition-colors flex items-center justify-between">
                    {topic}
                    <ArrowRight size={16} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Progress Card */}
        <div className="p-4 bg-slate-700/50 border-t border-slate-700">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-3">
            <p className="text-xs text-blue-100 mb-2">Learning Streak</p>
            <p className="text-2xl font-bold">5 days 🔥</p>
          </div>
        </div>
      </div>

      {/* Right Panel - Chat Interface */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-4 border-b border-blue-500/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="font-bold">FinMentor</h2>
              <p className="text-xs text-blue-100">Your AI Finance Tutor</p>
            </div>
          </div>
          <Lightbulb size={20} className="text-yellow-300" />
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {chatHistory.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-l-lg rounded-tr-lg' : 'bg-slate-800 text-white rounded-r-lg rounded-tl-lg'} p-4 space-y-3`}>
                {typeof msg.content === 'string' ? (
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                ) : (
                  <>
                    {/* Explanation */}
                    <div className="text-sm leading-relaxed">
                      <TypewriterText text={msg.content.explanation || ''} speed={20} />
                    </div>

                    {/* Analogy Box */}
                    {msg.content.analogy && (
                      <div className="bg-yellow-500/20 border-l-4 border-yellow-500 p-3 rounded">
                        <p className="text-xs font-semibold text-yellow-300 mb-1">💡 Analogy</p>
                        <p className="text-sm text-yellow-100">{msg.content.analogy}</p>
                      </div>
                    )}

                    {/* Market Example */}
                    {msg.content.market_example && (
                      <div className="bg-green-500/10 border border-green-500/30 p-3 rounded">
                        <p className="text-xs font-semibold text-green-400 mb-1">📈 Real Market Example</p>
                        <p className="text-sm text-green-100">{msg.content.market_example}</p>
                      </div>
                    )}

                    {/* Key Takeaway */}
                    {msg.content.key_takeaway && (
                      <div className="bg-blue-500/20 border border-blue-500/30 p-3 rounded">
                        <p className="text-xs font-semibold text-blue-300 mb-1">⭐ Key Takeaway</p>
                        <p className="text-sm font-semibold text-blue-100">{msg.content.key_takeaway}</p>
                      </div>
                    )}

                    {/* Follow-up Questions */}
                    {msg.content.follow_up_questions && msg.content.follow_up_questions.length > 0 && (
                      <div className="space-y-2 mt-3 pt-3 border-t border-slate-700">
                        <p className="text-xs text-slate-400">Next steps:</p>
                        <div className="space-y-2">
                          {msg.content.follow_up_questions.slice(0, 2).map((q, qidx) => (
                            <button
                              key={qidx}
                              onClick={() => handleSendMessage(q)}
                              className="w-full text-left text-xs bg-slate-700/50 hover:bg-slate-700 p-2 rounded transition-colors text-blue-300 hover:text-blue-200"
                            >
                              → {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Try in Playground Button */}
                    {msg.content.related_playground_scenario && (
                      <div className="mt-2">
                        <a
                          href="/playground"
                          className="inline-flex items-center gap-2 text-xs bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded transition-colors"
                        >
                          Try in Playground <ArrowRight size={14} />
                        </a>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-800 p-4 rounded-r-lg rounded-tl-lg">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-slate-800 border-t border-slate-700 p-4 space-y-3">
          {/* Quick Chips */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {quickChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(chip)}
                disabled={loading}
                className="whitespace-nowrap px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-700 text-xs font-medium rounded-full transition-colors text-blue-300"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Input Field */}
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && handleSendMessage()}
              disabled={loading}
              placeholder="Ask me anything about finance..."
              className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={loading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 px-4 py-3 rounded-lg transition-colors flex items-center gap-2"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
