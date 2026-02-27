'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { TrendingUp, Users, Award, Zap } from 'lucide-react';

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl font-bold text-blue-500 mb-4">FinNexus</div>
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
      {/* Navigation */}
      <nav className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="text-2xl font-bold text-blue-500">FinNexus</div>
          <Link
            href="/login"
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Sign In
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Learn & Trade Virtual Markets
          </h1>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Master financial concepts with FinNexus. Start with $124,500 in virtual funds and practice trading in a risk-free environment.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/login"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              Get Started
            </Link>
            <Link
              href="/#features"
              className="bg-slate-700 hover:bg-slate-600 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              Learn More
            </Link>
          </div>
        </div>

        {/* Demo Card */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 shadow-2xl">
          <p className="text-slate-400 text-center mb-4">Try the demo account</p>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400 mb-2">
                $124,500
              </div>
              <p className="text-slate-400">Virtual Starting Balance</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400 mb-2">
                6
              </div>
              <p className="text-slate-400">Different Asset Types</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400 mb-2">
                5
              </div>
              <p className="text-slate-400">Learning Modules</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-slate-800/50 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-white text-center mb-16">
            Everything You Need to Learn & Trade
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <div className="bg-blue-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="text-blue-500" size={24} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Portfolio Management</h3>
              <p className="text-slate-400">
                Track your virtual portfolio with real-time price updates and detailed P&L analytics.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <div className="bg-purple-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <Award className="text-purple-500" size={24} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Interactive Learning</h3>
              <p className="text-slate-400">
                Complete lessons on stocks, crypto, and market analysis at your own pace.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <div className="bg-yellow-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <Zap className="text-yellow-500" size={24} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Prediction Playground</h3>
              <p className="text-slate-400">
                Test your trading skills by predicting asset price movements risk-free.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <div className="bg-green-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <Users className="text-green-500" size={24} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">AI Advisor</h3>
              <p className="text-slate-400">
                Get personalized financial advice from our AI-powered advisor 24/7.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-12 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Start Your Financial Journey?
          </h2>
          <p className="text-blue-100 text-lg mb-8 max-w-2xl mx-auto">
            Join thousands of learners who are mastering the markets with FinNexus.
          </p>
          <Link
            href="/login"
            className="bg-white hover:bg-slate-100 text-blue-600 px-8 py-3 rounded-lg font-semibold transition-colors inline-block"
          >
            Sign In Now
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-800 border-t border-slate-700 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-slate-400">
          <p>
            FinNexus is an educational platform for learning financial concepts and trading skills.
          </p>
          <p className="text-sm mt-4">
            © 2024 FinNexus. All rights reserved. This is a demo platform.
          </p>
        </div>
      </footer>
    </div>
  );
}
