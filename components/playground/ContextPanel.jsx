'use client';

import React, { useState, useEffect } from 'react';
import { Lightbulb, X, ExternalLink } from 'lucide-react';

export default function ContextPanel({ asset, timeframe, isVisible, onClose }) {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [roundEnded, setRoundEnded] = useState(false);

  useEffect(() => {
    if (!isVisible || !asset) return;
    fetchEducationalContent();
  }, [isVisible, asset, timeframe]);

  const fetchEducationalContent = async () => {
    setLoading(true);
    try {
      const query = `${asset} ${timeframe} trading strategy`;
      const res = await fetch(
        `/api/education/search?q=${encodeURIComponent(query)}&level=INTERMEDIATE`
      );
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      if (data.success) {
        // Show top 3 lessons with preview
        const preview = (data.data || []).slice(0, 3).map(lesson => ({
          ...lesson,
          preview: lesson.content?.substring(0, 150) + '...' || ''
        }));
        setLessons(preview);
      }
    } catch (error) {
      console.error('Failed to fetch educational content:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden flex flex-col max-h-96">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lightbulb size={18} className="text-yellow-300" />
          <h3 className="font-semibold text-sm">💡 Learn</h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-300 hover:text-white transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-4">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        ) : lessons.length > 0 ? (
          <>
            <p className="text-xs text-slate-400 font-semibold uppercase">
              Relevant to {asset}
            </p>
            {lessons.map((lesson, idx) => (
              <div key={idx} className="bg-slate-700/50 rounded p-2 hover:bg-slate-700 transition-colors">
                <p className="text-xs font-semibold text-blue-300 mb-1">
                  {lesson.title || lesson.topic}
                </p>
                <p className="text-xs text-slate-400 line-clamp-2 mb-2">
                  {lesson.preview}
                </p>
                <a
                  href="/learn"
                  className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Learn More <ExternalLink size={12} />
                </a>
              </div>
            ))}

            {/* Round End Suggestions */}
            {roundEnded && (
              <div className="mt-3 pt-3 border-t border-slate-600 text-xs text-slate-300">
                <p className="font-semibold mb-2">Based on this result, you should learn:</p>
                <div className="space-y-1">
                  {lessons.map((lesson, idx) => (
                    <a
                      key={idx}
                      href="/learn"
                      className="block text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      → {lesson.title || lesson.topic}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-xs text-slate-400 text-center py-4">
            No relevant lessons found for {asset}
          </p>
        )}
      </div>

      {/* Footer CTA */}
      <div className="bg-slate-700/50 border-t border-slate-600 p-3">
        <a
          href="/learn"
          className="block text-center text-xs bg-blue-600 hover:bg-blue-700 text-white py-2 rounded transition-colors font-semibold"
        >
          Explore All Lessons
        </a>
      </div>
    </div>
  );
}
