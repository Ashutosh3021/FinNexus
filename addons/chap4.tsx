import { useState } from "react";

const questions = [
  {
    id: 1,
    question: "What is the 4% rule used for?",
    answer: "Safe withdrawal rate",
    altAnswers: ["withdrawal rate", "safe withdrawal", "sustainable withdrawal rate", "portfolio withdrawal rate"],
    placeholder: "Your answer...",
  },
  {
    id: 2,
    question: "Gold in a portfolio protects against?",
    answer: "Inflation, uncertainty",
    altAnswers: [
      "inflation and uncertainty",
      "uncertainty and inflation",
      "inflation uncertainty",
      "uncertainty inflation",
      "inflation",
      "economic uncertainty",
      "inflation and economic uncertainty",
    ],
    placeholder: "Your answer...",
  },
  {
    id: 3,
    question: "What is the maximum 80C deduction allowed per year?",
    answer: "₹1.5 lakh",
    altAnswers: ["1.5 lakh", "rs 1.5 lakh", "rupees 1.5 lakh", "1.5lakh", "15 lakh", "150000", "1,50,000"],
    placeholder: "Your answer...",
  },
  {
    id: 4,
    question: "ELSS has a lock-in period of how many years?",
    answer: "3 years",
    altAnswers: ["3", "three years", "three"],
    placeholder: "Your answer...",
  },
  {
    id: 5,
    question: "PPF has triple tax exemption — on what three things exactly?",
    answer: "Contribution, interest, maturity",
    altAnswers: [
      "contribution interest maturity",
      "interest contribution maturity",
      "maturity interest contribution",
      "maturity contribution interest",
      "interest maturity contribution",
      "contributions interest maturity",
      "contribution interest and maturity",
    ],
    placeholder: "Your answer...",
  },
];

function normalizeAnswer(str) {
  return str.trim().toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, " ");
}

function checkAnswer(input, q) {
  const norm = normalizeAnswer(input);
  const allAccepted = [q.answer, ...(q.altAnswers || [])].map(normalizeAnswer);
  return allAccepted.includes(norm);
}

function QuestionCard({ q, index }) {
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const isCorrect = submitted && checkAnswer(input, q);
  const isWrong = submitted && !isCorrect;

  const handleCheck = () => {
    if (input.trim()) setSubmitted(true);
  };

  const handleReset = () => {
    setInput("");
    setSubmitted(false);
  };

  return (
    <div
      className={`rounded-xl border p-6 transition-all duration-300 ${
        isCorrect
          ? "border-emerald-500/50 bg-emerald-500/5"
          : isWrong
          ? "border-red-500/50 bg-red-500/5"
          : "border-slate-700 bg-slate-800/60"
      }`}
    >
      <div className="flex items-start gap-4">
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
            isCorrect
              ? "bg-emerald-500/20 text-emerald-400"
              : isWrong
              ? "bg-red-500/20 text-red-400"
              : "bg-blue-500/20 text-blue-400"
          }`}
        >
          {isCorrect ? (
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : isWrong ? (
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          ) : (
            `Q${index + 1}`
          )}
        </div>

        <div className="flex-1">
          <p className="text-white font-medium mb-4">{q.question}</p>

          <div className="flex gap-3 items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                if (submitted) setSubmitted(false);
              }}
              onKeyDown={(e) => e.key === "Enter" && handleCheck()}
              placeholder={q.placeholder}
              disabled={isCorrect}
              className={`flex-1 bg-slate-700/60 border rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-1 ${
                isCorrect
                  ? "border-emerald-500/40 cursor-not-allowed opacity-70"
                  : isWrong
                  ? "border-red-500/40 focus:border-red-400 focus:ring-red-500/30"
                  : "border-slate-600 focus:border-blue-500 focus:ring-blue-500/20"
              }`}
            />

            {!isCorrect ? (
              <button
                onClick={handleCheck}
                disabled={!input.trim()}
                className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                Check
              </button>
            ) : (
              <button
                onClick={handleReset}
                className="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm font-semibold rounded-lg transition-colors"
              >
                Redo
              </button>
            )}
          </div>

          {isWrong && (
            <p className="text-red-400 text-sm mt-2 flex items-center gap-1.5">
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 flex-shrink-0">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Not quite — try again!
            </p>
          )}

          {isCorrect && (
            <p className="text-emerald-400 text-sm mt-2 flex items-center gap-1.5">
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 flex-shrink-0">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Correct!
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function FinancialIndependencePage() {
  return (
    <div style={{ fontFamily: "'Georgia', 'Times New Roman', serif" }} className="min-h-screen bg-slate-900 text-slate-100">

      {/* Top Nav */}
      <div className="sticky top-0 z-10 bg-slate-900/90 backdrop-blur-sm border-b border-slate-800 px-6 py-3 flex items-center gap-3">
        <button className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors text-sm">
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to Lessons
        </button>
        <span className="text-slate-600">|</span>
        <span className="text-slate-400 text-sm truncate">Personal Finance · Financial Independence</span>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12">

        {/* Chapter Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <span className="px-3 py-1 bg-blue-500/15 text-blue-400 rounded-full text-xs font-medium tracking-wide uppercase" style={{ fontFamily: "system-ui" }}>
              Chapter 4
            </span>
            <span className="flex items-center gap-1.5 text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              11 min read
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white leading-tight mb-4">
            Designing Financial Independence
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            The destination all the earlier stages are building toward — how to calculate your number, spread your portfolio intelligently across asset classes, and use the tax system to keep more of every rupee you earn.
          </p>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-10">
          <div className="flex-1 h-px bg-slate-800"></div>
          <div className="w-1.5 h-1.5 rounded-full bg-slate-600"></div>
          <div className="flex-1 h-px bg-slate-800"></div>
        </div>

        {/* Lesson Content */}
        <div className="space-y-10 mb-16">

          {/* Section 1: Financial Independence */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>1</span>
              Financial Independence
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              Financial independence is the state where your investments and assets generate enough passive income every month to cover all your living expenses — without you needing to work. You still can work if you choose to, but you no longer have to. Your money works for you instead of you working for money. This is the ultimate destination that all the earlier stages — savings rate, SIP, index funds, compounding — are building toward.
            </p>

            {/* 4% Rule Callout */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl px-6 py-5 mb-5">
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-3" style={{ fontFamily: "system-ui" }}>The 4% Rule — Your FI Number</p>
              <p className="text-blue-300 font-bold text-lg tracking-wide" style={{ fontFamily: "monospace" }}>
                FI Portfolio = Annual Expenses ÷ 0.04
              </p>
              <div className="mt-3 pt-3 border-t border-slate-700">
                <p className="text-slate-400 text-sm" style={{ fontFamily: "system-ui" }}>
                  If your monthly expenses are ₹50,000 — meaning ₹6 lakh per year — you need a portfolio of approximately <span className="text-white font-semibold">₹1.5 crore</span> to be financially independent.
                </p>
              </div>
            </div>

            {/* What FI gives you */}
            <p className="text-slate-300 leading-relaxed text-base mb-4">
              The reason financial independence is so powerful as a goal is not just about quitting your job. It is about having options:
            </p>
            <div className="grid grid-cols-2 gap-3 mb-5">
              {[
                "Take lower-paying work you love",
                "Start a business without needing a salary",
                "Take a year off",
                "Spend more time with your family",
              ].map((item) => (
                <div key={item} className="bg-slate-800/60 border border-slate-700/60 rounded-lg px-4 py-3 flex items-start gap-2.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 flex-shrink-0"></div>
                  <p className="text-slate-300 text-sm leading-snug" style={{ fontFamily: "system-ui" }}>{item}</p>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 px-6 py-5">
              <p className="text-slate-200 leading-relaxed text-base">
                Financial independence converts money from a source of anxiety into a source of freedom. Most people never reach it not because it's mathematically impossible on their income, but because they <span className="text-white font-semibold">never calculated the number, never built a plan, and never started early enough.</span>
              </p>
            </div>
          </section>

          {/* Section 2: Asset Allocation */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>2</span>
              Asset Allocation
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              Asset allocation is the strategy of dividing your total investment portfolio across different asset classes — stocks, bonds, gold, cash, real estate, and others — in deliberate proportions. It is arguably the single most important investment decision you will ever make, more important than which specific stocks or funds you pick.
            </p>

            {/* Classic allocation visual */}
            <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden mb-5">
              <div className="px-5 py-3 border-b border-slate-700 bg-slate-800">
                <p className="text-xs text-slate-500 uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>Classic Moderate Allocation — Age 30s/40s</p>
              </div>
              <div className="divide-y divide-slate-700/60">
                {[
                  { pct: "60%", label: "Stocks", desc: "Drives long-term portfolio growth", color: "text-blue-400", bar: "bg-blue-500" },
                  { pct: "20%", label: "Bonds", desc: "Cushions crashes — often hold value when stocks fall", color: "text-emerald-400", bar: "bg-emerald-500" },
                  { pct: "10%", label: "Gold", desc: "Protects against inflation and currency devaluation", color: "text-amber-400", bar: "bg-amber-500" },
                  { pct: "10%", label: "Cash", desc: "Liquidity for emergencies and opportunities", color: "text-slate-300", bar: "bg-slate-500" },
                ].map((row) => (
                  <div key={row.label} className="px-5 py-3 flex items-center gap-4">
                    <span className={`text-xl font-bold w-12 flex-shrink-0 ${row.color}`} style={{ fontFamily: "system-ui" }}>{row.pct}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-white text-sm font-semibold" style={{ fontFamily: "system-ui" }}>{row.label}</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-1.5 mb-1">
                        <div className={`${row.bar} h-1.5 rounded-full`} style={{ width: row.pct }}></div>
                      </div>
                      <p className="text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>{row.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <p className="text-slate-300 leading-relaxed text-base mb-5">
              Asset allocation changes with age. When you are young, time is your greatest asset and you can absorb volatility, so a higher stock allocation — even 80–90% — is appropriate. As you approach retirement, you gradually shift toward bonds and stable assets because you no longer have decades to recover from a market crash.
            </p>

            <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 px-5 py-4">
              <p className="text-amber-300 text-sm font-semibold mb-1" style={{ fontFamily: "system-ui" }}>The Glide Path</p>
              <p className="text-slate-300 text-sm leading-relaxed" style={{ fontFamily: "system-ui" }}>
                This gradual shift from stocks toward bonds and stable assets as you age is called a glide path and it is the foundation of every serious long-term financial plan. The biggest mistake investors make is either holding too much cash out of fear or holding too much stock without understanding their own emotional capacity to handle a 40% drawdown without panic-selling.
              </p>
            </div>
          </section>

          {/* Section 3: Tax Optimization */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>3</span>
              Tax Optimization
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              Tax optimization is the legal practice of structuring your investments and finances in a way that minimises the amount of tax you pay, thereby keeping more of your money compounding for you. It is not tax evasion — which is illegal — it is tax planning, which is not only legal but actively encouraged by the government through instruments designed to direct private money toward long-term savings.
            </p>

            <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden mb-5">
              <div className="px-5 py-3 border-b border-slate-700 bg-slate-800">
                <p className="text-xs text-slate-500 uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>Section 80C — Up to ₹1.5 Lakh Deduction Per Year</p>
              </div>
              <div className="px-5 py-4">
                <p className="text-slate-300 text-sm leading-relaxed" style={{ fontFamily: "system-ui" }}>
                  If you are in the 30% tax bracket, maximising your 80C deductions alone saves you{" "}
                  <span className="text-white font-semibold">₹45,000 in tax every single year</span> — money that stays invested and compounding rather than going to the government.
                </p>
              </div>
            </div>

            {/* Three instruments */}
            <div className="space-y-4">

              {/* ELSS */}
              <div className="rounded-xl border border-emerald-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-bold" style={{ fontFamily: "system-ui" }}>ELSS</h3>
                    <p className="text-slate-500 text-xs mt-0.5" style={{ fontFamily: "system-ui" }}>Equity Linked Savings Scheme</p>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" style={{ fontFamily: "system-ui" }}>
                    Best for Growth
                  </span>
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    A type of mutual fund that qualifies for 80C deductions. It invests primarily in equities, giving you stock market returns, while simultaneously reducing your tax liability.
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-700/40 rounded-lg px-3 py-2.5 text-center">
                      <p className="text-white font-bold text-sm" style={{ fontFamily: "system-ui" }}>3 Years</p>
                      <p className="text-slate-500 text-xs mt-0.5" style={{ fontFamily: "system-ui" }}>Lock-in (shortest of any 80C)</p>
                    </div>
                    <div className="bg-slate-700/40 rounded-lg px-3 py-2.5 text-center">
                      <p className="text-white font-bold text-sm" style={{ fontFamily: "system-ui" }}>10% LTCG</p>
                      <p className="text-slate-500 text-xs mt-0.5" style={{ fontFamily: "system-ui" }}>On gains above ₹1 lakh</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* PPF */}
              <div className="rounded-xl border border-blue-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-bold" style={{ fontFamily: "system-ui" }}>PPF</h3>
                    <p className="text-slate-500 text-xs mt-0.5" style={{ fontFamily: "system-ui" }}>Public Provident Fund</p>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/30" style={{ fontFamily: "system-ui" }}>
                    Triple Tax-Free
                  </span>
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    A government-backed savings scheme with a 15-year lock-in offering around 7.1% annual interest, completely tax-free. Its EEE status — Exempt-Exempt-Exempt — makes it one of the most tax-efficient instruments in India.
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {["Contribution", "Interest", "Maturity"].map((item) => (
                      <div key={item} className="bg-blue-500/10 border border-blue-500/20 rounded-lg px-2 py-2.5 text-center">
                        <p className="text-blue-300 text-xs font-semibold" style={{ fontFamily: "system-ui" }}>Exempt</p>
                        <p className="text-slate-400 text-xs mt-0.5" style={{ fontFamily: "system-ui" }}>{item}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* NPS */}
              <div className="rounded-xl border border-amber-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-bold" style={{ fontFamily: "system-ui" }}>NPS</h3>
                    <p className="text-slate-500 text-xs mt-0.5" style={{ fontFamily: "system-ui" }}>National Pension System</p>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30" style={{ fontFamily: "system-ui" }}>
                    Retirement Only
                  </span>
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    A government-run retirement scheme with an additional deduction of up to ₹50,000 under Section 80CCD(1B) — over and above the ₹1.5 lakh 80C limit. One of the few instruments that gives you tax deductions beyond the standard ceiling.
                  </p>
                  <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 px-4 py-3">
                    <p className="text-amber-300 text-sm" style={{ fontFamily: "system-ui" }}>
                      ⚠️ Locked until age 60, and 40% of the corpus at maturity must be used to purchase an annuity. Best treated as a pure retirement vehicle, not a flexible investment.
                    </p>
                  </div>
                </div>
              </div>

            </div>
          </section>

          {/* Section 4: Why It Matters */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>4</span>
              Why Tax Optimization Matters More Than Most People Realize
            </h2>

            {/* Compounding tax savings */}
            <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden mb-5">
              <div className="px-5 py-3 border-b border-slate-700 bg-slate-800">
                <p className="text-xs text-slate-500 uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>₹45,000 saved in tax this year @ 12% over 20 years</p>
              </div>
              <div className="grid grid-cols-2 divide-x divide-slate-700">
                <div className="px-5 py-5 text-center">
                  <p className="text-3xl font-bold text-slate-400 mb-1">₹45,000</p>
                  <p className="text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>Tax saved today</p>
                </div>
                <div className="px-5 py-5 text-center">
                  <p className="text-3xl font-bold text-emerald-400 mb-1">₹4.8L</p>
                  <p className="text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>After 20 years compounding</p>
                </div>
              </div>
              <div className="px-5 py-3 border-t border-slate-700 bg-emerald-500/5">
                <p className="text-emerald-400 text-sm text-center" style={{ fontFamily: "system-ui" }}>Multiply this across every year of your working life — tax optimization can add tens of lakhs to your final wealth.</p>
              </div>
            </div>

            <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 px-6 py-5">
              <p className="text-slate-200 leading-relaxed text-base">
                The wealthiest individuals and families in India spend significant time and money on tax planning not because they are greedy but because they understand that <span className="text-white font-semibold">the return on smart tax planning is often higher than the return on picking a better stock.</span>
              </p>
            </div>
          </section>

        </div>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-10">
          <div className="flex-1 h-px bg-slate-800"></div>
          <div className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
            Knowledge Check
          </div>
          <div className="flex-1 h-px bg-slate-800"></div>
        </div>

        {/* Q&A Section */}
        <div className="mb-16">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white mb-1">Test Your Understanding</h2>
            <p className="text-slate-400 text-sm" style={{ fontFamily: "system-ui" }}>
              Type your answers below. Press Enter or click Check to verify.
            </p>
          </div>

          <div className="space-y-4" style={{ fontFamily: "system-ui" }}>
            {questions.map((q, index) => (
              <QuestionCard key={q.id} q={q} index={index} />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-8 flex items-center justify-between" style={{ fontFamily: "system-ui" }}>
          <span className="text-slate-500 text-sm">Chapter 4 of 8</span>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors">
            Next Chapter
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

      </div>
    </div>
  );
}