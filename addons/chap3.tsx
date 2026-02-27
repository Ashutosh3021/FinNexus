import { useState } from "react";

const questions = [
  {
    id: 1,
    question: "What happens to your money when a company's profits increase?",
    answer: "Share value rises",
    altAnswers: ["share value increases", "value rises", "it rises", "the share value rises", "share price rises", "stock value rises"],
    placeholder: "Your answer...",
  },
  {
    id: 2,
    question: "What does SIP stand for?",
    answer: "Systematic Investment Plan",
    altAnswers: ["systematic investment plan"],
    placeholder: "Your answer...",
  },
  {
    id: 3,
    question: "SIP reduces risk through what mechanism?",
    answer: "Rupee cost averaging",
    altAnswers: ["rupee cost averaging", "cost averaging", "dollar cost averaging"],
    placeholder: "Your answer...",
  },
  {
    id: 4,
    question: "In a SIP, what happens when market prices are low?",
    answer: "Buy more units",
    altAnswers: ["you buy more units", "more units are bought", "you get more units", "more units", "buy more"],
    placeholder: "Your answer...",
  },
  {
    id: 5,
    question: "What three things did Infosys early investors need?",
    answer: "Knowledge, conviction, patience",
    altAnswers: [
      "knowledge conviction patience",
      "conviction knowledge patience",
      "patience conviction knowledge",
      "patience knowledge conviction",
      "conviction patience knowledge",
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

const FundTypeBadge = ({ type }) => {
  const styles = {
    Passive: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
    "Low Volatility": "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
    "High Growth": "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${styles[type]}`} style={{ fontFamily: "system-ui" }}>
      {type}
    </span>
  );
};

export default function EquityInvestingPage() {
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
        <span className="text-slate-400 text-sm truncate">Personal Finance · Equity Investing</span>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12">

        {/* Chapter Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <span className="px-3 py-1 bg-blue-500/15 text-blue-400 rounded-full text-xs font-medium tracking-wide uppercase" style={{ fontFamily: "system-ui" }}>
              Chapter 3
            </span>
            <span className="flex items-center gap-1.5 text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              10 min read
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white leading-tight mb-4">
            The Foundations of Equity Investing
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            From mutual funds to individual stocks to the discipline of a monthly SIP — this chapter lays out exactly how ordinary people use equity markets to build extraordinary long-term wealth.
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

          {/* Section 1: Mutual Funds */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>1</span>
              Mutual Funds
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              A mutual fund is a professionally managed investment vehicle that pools money from thousands of individual investors and deploys that combined capital into a diversified portfolio of stocks, bonds, or both. Instead of you researching companies or tracking markets daily, a fund house does all of that on your behalf. You invest money, receive units in return, and your wealth grows or falls based on how the underlying assets perform. It is the most accessible entry point into investing for a complete beginner.
            </p>

            {/* Fund Types Table */}
            <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden mb-5">
              <div className="px-5 py-3 border-b border-slate-700 bg-slate-800">
                <p className="text-xs text-slate-500 uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>The Three Main Types in India</p>
              </div>
              <div className="divide-y divide-slate-700/60">
                <div className="px-5 py-4 flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-white font-semibold mb-1" style={{ fontFamily: "system-ui" }}>Index Funds</p>
                    <p className="text-slate-400 text-sm" style={{ fontFamily: "system-ui" }}>Passively mirror a market index like the Nifty 50. Cheapest and most consistent — expense ratios as low as 0.1–0.2%.</p>
                  </div>
                  <FundTypeBadge type="Passive" />
                </div>
                <div className="px-5 py-4 flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-white font-semibold mb-1" style={{ fontFamily: "system-ui" }}>Large Cap Funds</p>
                    <p className="text-slate-400 text-sm" style={{ fontFamily: "system-ui" }}>Invest in India's top 100 companies by size. Stable, established businesses — less volatile, moderate growth.</p>
                  </div>
                  <FundTypeBadge type="Low Volatility" />
                </div>
                <div className="px-5 py-4 flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-white font-semibold mb-1" style={{ fontFamily: "system-ui" }}>Mid Cap Funds</p>
                    <p className="text-slate-400 text-sm" style={{ fontFamily: "system-ui" }}>Companies ranked 101st to 250th. Higher growth potential but meaningfully more volatile and risky.</p>
                  </div>
                  <FundTypeBadge type="High Growth" />
                </div>
              </div>
            </div>

            <p className="text-slate-400 text-sm italic border-l-2 border-slate-700 pl-4" style={{ fontFamily: "system-ui" }}>
              For a beginner, a Nifty 50 index fund is the single best starting point.
            </p>
          </section>

          {/* Section 2: Stock Market */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>2</span>
              Stock Market Basics
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              The stock market is a marketplace where ownership stakes in publicly listed companies are bought and sold. When a company wants to raise money to grow its business, it lists itself on a stock exchange — like the NSE or BSE in India — and sells small pieces of itself to the public. Each of those pieces is called a stock or share.
            </p>

            <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 px-6 py-5 mb-5">
              <p className="text-slate-200 leading-relaxed text-base">
                When you buy a stock, you are buying a real ownership stake in that company. You are not lending money — you are becoming a part-owner. As a shareholder, you participate directly in the company's success. When the company grows its revenue, expands, or increases its profits, <span className="text-white font-semibold">the value of each share rises and your investment grows with it.</span> You can also receive dividends — a portion of profits distributed directly to shareholders.
              </p>
            </div>

            {/* Infosys callout */}
            <div className="rounded-xl border border-slate-700 bg-slate-800 overflow-hidden mb-5">
              <div className="px-5 py-3 border-b border-slate-700 bg-slate-800/80 flex items-center gap-2">
                <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 text-amber-400">
                  <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.996.168-1.985.465-2.95a4 4 0 10-4.93 0c.297.965.45 1.954.465 2.95h4z" />
                </svg>
                <p className="text-xs text-slate-500 uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>Case Study — Infosys (1993)</p>
              </div>
              <div className="px-5 py-4">
                <p className="text-slate-300 text-base leading-relaxed mb-4">
                  Infosys listed on Indian stock exchanges in 1993. Investors who recognised early that India's software export industry was about to explode, bought shares, and held through decades of volatility, turned relatively small investments into life-changing wealth — returns in the thousands of percent over the long run.
                </p>
                <div className="grid grid-cols-3 gap-3">
                  {["Knowledge", "Conviction", "Patience"].map((trait) => (
                    <div key={trait} className="bg-slate-700/50 rounded-lg px-3 py-3 text-center">
                      <p className="text-white text-sm font-semibold" style={{ fontFamily: "system-ui" }}>{trait}</p>
                    </div>
                  ))}
                </div>
                <p className="text-slate-500 text-xs mt-3 text-center" style={{ fontFamily: "system-ui" }}>The three things every long-term equity investor needs</p>
              </div>
            </div>

            <p className="text-slate-300 leading-relaxed text-base">
              This is why the stock market requires learning. Without understanding how businesses work, how to read financial statements, how to assess competitive advantages, and how to manage your emotions during downturns, individual stock picking is closer to gambling than investing. The stock market rewards informed, patient, long-term investors and punishes impatient, uninformed speculators.
            </p>
          </section>

          {/* Section 3: SIP */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>3</span>
              SIP — Systematic Investment Plan
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              A SIP is a method of investing a fixed amount of money into a mutual fund at regular intervals — typically monthly — automatically. You set it up once, link it to your bank account, and a predetermined amount is debited and invested on a fixed date every month without you needing to do anything. It is the most practical and powerful wealth-building tool available to ordinary people in India.
            </p>

            {/* SIP projection */}
            <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden mb-5">
              <div className="px-5 py-3 border-b border-slate-700 bg-slate-800">
                <p className="text-xs text-slate-500 uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>What ₹2,000/month looks like over 30 years @ 12% p.a.</p>
              </div>
              <div className="grid grid-cols-2 divide-x divide-slate-700">
                <div className="px-5 py-5 text-center">
                  <p className="text-3xl font-bold text-blue-400 mb-1">₹2,000</p>
                  <p className="text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>Monthly investment</p>
                </div>
                <div className="px-5 py-5 text-center">
                  <p className="text-3xl font-bold text-emerald-400 mb-1">₹60–70L</p>
                  <p className="text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>After 30 years</p>
                </div>
              </div>
              <div className="px-5 py-3 border-t border-slate-700 bg-emerald-500/5">
                <p className="text-emerald-400 text-sm text-center" style={{ fontFamily: "system-ui" }}>Increase to ₹5,000/month and the number crosses ₹1.5 crore.</p>
              </div>
            </div>

            <p className="text-slate-300 leading-relaxed text-base mb-5">
              SIP works through three mechanisms that compound on each other over time:
            </p>

            <div className="space-y-3 mb-5">
              <div className="rounded-lg border border-slate-700/60 bg-slate-800/40 px-5 py-4">
                <div className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5" style={{ fontFamily: "system-ui" }}>1</span>
                  <div>
                    <p className="text-white font-semibold mb-1" style={{ fontFamily: "system-ui" }}>Consistency</p>
                    <p className="text-slate-300 text-sm leading-relaxed" style={{ fontFamily: "system-ui" }}>Removes the decision of whether to invest this month, eliminating the excuses that derail most people.</p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-5 py-4">
                <div className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5" style={{ fontFamily: "system-ui" }}>2</span>
                  <div>
                    <p className="text-amber-300 font-semibold mb-1" style={{ fontFamily: "system-ui" }}>Rupee Cost Averaging</p>
                    <p className="text-slate-300 text-sm leading-relaxed" style={{ fontFamily: "system-ui" }}>Because you invest a fixed amount every month regardless of market direction, you automatically buy more units when prices are low and fewer units when prices are high. Over time this averages out your purchase cost and smooths market volatility. You stop worrying about timing the market because you are always in the market.</p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-5 py-4">
                <div className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5" style={{ fontFamily: "system-ui" }}>3</span>
                  <div>
                    <p className="text-emerald-300 font-semibold mb-1" style={{ fontFamily: "system-ui" }}>Compounding</p>
                    <p className="text-slate-300 text-sm leading-relaxed" style={{ fontFamily: "system-ui" }}>Your returns generate their own returns, and over decades this creates exponential rather than linear wealth growth. The longer you stay invested, the more dramatic the compounding effect becomes.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 px-6 py-5">
              <p className="text-slate-200 leading-relaxed text-base">
                SIP is called <span className="text-white font-semibold">how normal people become rich</span> because it requires no special knowledge, no market timing, no large lump sum, and no constant monitoring. It simply requires discipline — starting early, investing consistently, and not stopping during market downturns, which is precisely when most people panic and quit.
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
          <span className="text-slate-500 text-sm">Chapter 3 of 8</span>
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