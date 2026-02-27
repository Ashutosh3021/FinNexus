'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@/context/UserContext';
import { Check } from 'lucide-react';

export default function OnboardingPage() {
  const router = useRouter();
  const { updateLevel } = useUser();
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const levels = [
    {
      id: 'BEGINNER',
      name: 'Beginner',
      description: 'New to investing and trading concepts',
      features: ['Fundamentals', 'Basic terminology', 'Getting started guides'],
    },
    {
      id: 'INTERMEDIATE',
      name: 'Intermediate',
      description: 'Some experience with trading and markets',
      features: ['Technical analysis', 'Risk management', 'Portfolio building'],
    },
    {
      id: 'ADVANCED',
      name: 'Advanced',
      description: 'Experienced trader looking to deepen knowledge',
      features: ['Options trading', 'Advanced strategies', 'Market analysis'],
    },
  ];

  const handleContinue = async () => {
    if (!selectedLevel) return;

    setIsLoading(true);
    updateLevel(selectedLevel);

    // Simulate processing
    await new Promise((resolve) => setTimeout(resolve, 1000));

    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 p-4">
      <div className="max-w-4xl mx-auto py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="text-4xl font-bold text-blue-500 mb-2">FinNexus</div>
          <h1 className="text-3xl font-bold text-white mb-4">
            Choose Your Learning Level
          </h1>
          <p className="text-slate-300 text-lg">
            Select the experience level that best matches your knowledge
          </p>
        </div>

        {/* Level Selection Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {levels.map((level) => (
            <button
              key={level.id}
              onClick={() => setSelectedLevel(level.id)}
              className={`p-6 rounded-xl border-2 transition-all ${
                selectedLevel === level.id
                  ? 'bg-blue-600 border-blue-400 shadow-lg shadow-blue-500/50'
                  : 'bg-slate-800 border-slate-700 hover:border-slate-600'
              }`}
            >
              {/* Selected Badge */}
              {selectedLevel === level.id && (
                <div className="flex justify-end mb-4">
                  <div className="bg-green-500 rounded-full p-1">
                    <Check size={20} className="text-white" />
                  </div>
                </div>
              )}

              <h3 className={`text-xl font-bold mb-2 ${
                selectedLevel === level.id ? 'text-white' : 'text-slate-100'
              }`}>
                {level.name}
              </h3>

              <p className={`text-sm mb-4 ${
                selectedLevel === level.id ? 'text-blue-100' : 'text-slate-400'
              }`}>
                {level.description}
              </p>

              <div className="space-y-2">
                {level.features.map((feature, i) => (
                  <div
                    key={i}
                    className={`text-sm flex items-center gap-2 ${
                      selectedLevel === level.id ? 'text-blue-100' : 'text-slate-300'
                    }`}
                  >
                    <div className={`w-1.5 h-1.5 rounded-full ${
                      selectedLevel === level.id ? 'bg-blue-100' : 'bg-slate-500'
                    }`}></div>
                    {feature}
                  </div>
                ))}
              </div>
            </button>
          ))}
        </div>

        {/* Continue Button */}
        <div className="flex justify-center">
          <button
            onClick={handleContinue}
            disabled={!selectedLevel || isLoading}
            className="px-12 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-semibold rounded-lg transition-colors"
          >
            {isLoading ? 'Setting up...' : 'Continue to Dashboard'}
          </button>
        </div>

        {/* Info Footer */}
        <p className="text-center text-slate-400 text-sm mt-8">
          You can change your level anytime from your profile settings
        </p>
      </div>
    </div>
  );
}
