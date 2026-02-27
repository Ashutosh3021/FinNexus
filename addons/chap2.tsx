import { useState } from "react";

const questions = [
  {
    id: 1,
    question: "What is India's approximate annual inflation rate?",
    answer: "6-7%",
    altAnswers: ["6–7%", "6-7", "6–7", "6 to 7%", "6 to 7"],
    placeholder: "Your answer...",
  },
  {
    id: 2,
    question: "Savings account interest in India is typically?",
    answer: "3-4%",
    altAnswers: ["3–4%", "3-4", "3–4", "3 to 4%", "3 to 4"],
    placeholder: "Your answer...",
  },
  {
    id: 3,
    question: "Index funds mirror what instead of having a manager?",
    answer: "Market index",
    altAnswers: ["a market index", "the market index", "index"],
    placeholder: "Your answer...",
  },
  {
    id: 4,
    question: "Crypto is backed by?",
    answer: "Nothing",
    altAnswers: ["nothing at all", "no one", "none"],
    placeholder: "Your answer...",
  },
  {
    id: 5,
    question: "What reduces risk more than anything else in investing?",
    answer: "Time",
    altAnswers: ["time in market", "time horizon"],
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

const RiskBadge = ({ level }) => {
  const styles = {
    Low: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
    Medium: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
    High: "bg-red-500/15 text-red-400 border border-red-500/30",
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${styles[level]}`} style={{ fontFamily: "system-ui" }}>
      {level} Risk
    </span>
  );
};

export default function InflationRiskPage() {
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
        <span className="text-slate-400 text-sm truncate">Personal Finance · Inflation & Risk</span>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12">

        {/* Chapter Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <span className="px-3 py-1 bg-blue-500/15 text-blue-400 rounded-full text-xs font-medium tracking-wide uppercase" style={{ fontFamily: "system-ui" }}>
              Chapter 2
            </span>
            <span className="flex items-center gap-1.5 text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              12 min read
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white leading-tight mb-4">
            Understanding Inflation and the Risk–Return Spectrum
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            Money left idle doesn't stay still — it quietly shrinks. This chapter explains why investing isn't optional, and maps out every major instrument across the risk spectrum so you can make informed choices.
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

          {/* Section 1: Inflation */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>1</span>
              Inflation — The Silent Money Killer
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              Inflation is the gradual rise in the price of goods and services over time. When prices go up, the purchasing power of your money goes down. The same ₹100 that buys you a full meal today might only buy you a cup of chai five years from now.
            </p>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              In India, inflation runs at roughly 6–7% per year. That means every year, your money silently loses about 6–7% of its real value — even if the number in your bank account stays exactly the same. It's not a dramatic crash. It's a slow, invisible leak.
            </p>

            {/* Inflation vs Savings visual callout */}
            <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden mb-5">
              <div className="px-5 py-3 border-b border-slate-700 bg-slate-800">
                <p className="text-xs text-slate-500 uppercase tracking-widest" style={{ fontFamily: "system-ui" }}>The Savings Account Trap</p>
              </div>
              <div className="grid grid-cols-2 divide-x divide-slate-700">
                <div className="px-5 py-4 text-center">
                  <p className="text-3xl font-bold text-red-400 mb-1">6–7%</p>
                  <p className="text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>Annual inflation rate</p>
                </div>
                <div className="px-5 py-4 text-center">
                  <p className="text-3xl font-bold text-slate-400 mb-1">3–4%</p>
                  <p className="text-slate-400 text-xs" style={{ fontFamily: "system-ui" }}>Savings account interest</p>
                </div>
              </div>
              <div className="px-5 py-3 border-t border-slate-700 bg-red-500/5">
                <p className="text-red-400 text-sm text-center" style={{ fontFamily: "system-ui" }}>You're losing 2–3% of real value every year, even while "earning" interest.</p>
              </div>
            </div>

            {/* Rule of 72 */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl px-6 py-5 mb-5">
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-3" style={{ fontFamily: "system-ui" }}>The Rule of 72</p>
              <p className="text-blue-300 font-bold text-lg tracking-wide" style={{ fontFamily: "monospace" }}>72 ÷ 7% ≈ 10 years to double prices</p>
              <div className="mt-3 pt-3 border-t border-slate-700">
                <p className="text-slate-400 text-sm" style={{ fontFamily: "system-ui" }}>₹100 today has the same buying power as ₹50 will have in about a decade. Your money didn't disappear — inflation just cut it in half silently.</p>
              </div>
            </div>

            <p className="text-slate-300 leading-relaxed text-base">
              This is why investing isn't optional. It is the only way to stay ahead of inflation and preserve the real value of your money over time.
            </p>
          </section>

          {/* Section 2: Risk vs Return */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>2</span>
              Risk vs Return — The Fundamental Trade-off
            </h2>
            <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 px-6 py-5 mb-5">
              <p className="text-slate-200 leading-relaxed text-base">
                This is the single most important concept in all of investing. Risk and return are almost always directly linked — the more return you want, the more risk you have to accept. <span className="text-white font-semibold">There is no free lunch.</span> Anyone promising high returns with zero risk is either misinformed or selling something dangerous.
              </p>
            </div>
            <p className="text-slate-300 leading-relaxed text-base">
              The reason this relationship exists is logical: if something were guaranteed to give high returns with no risk, every investor in the world would pile into it immediately, driving up the price until the returns dropped back to normal. Markets constantly price in risk. Higher risk means higher uncertainty — you might win big, or you might lose significantly. That uncertainty is precisely what gets rewarded with higher potential returns. You are being compensated for tolerating the possibility of loss.
            </p>
          </section>

          {/* Section 3: The Spectrum */}
          <section>
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>3</span>
              The Risk–Return Spectrum
            </h2>

            <div className="space-y-4">

              {/* Savings Account */}
              <div className="rounded-xl border border-emerald-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <h3 className="text-white font-bold">Savings Account</h3>
                  <RiskBadge level="Low" />
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    You deposit money in a bank, they pay you interest — typically 3–4% in India — and your principal is completely protected. The government insures deposits up to ₹5 lakh per bank through DICGC.
                  </p>
                  <p className="text-slate-300 leading-relaxed text-base">
                    The problem: the return is almost always below inflation. A savings account is the right place for your emergency fund (3–6 months of expenses) and for money you need in the next 1–3 months. It is the wrong place for money you won't need for years.
                  </p>
                </div>
              </div>

              {/* Fixed Deposit */}
              <div className="rounded-xl border border-emerald-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <h3 className="text-white font-bold">Fixed Deposit (FD)</h3>
                  <RiskBadge level="Low" />
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    You lock your money with a bank for a set period — 7 days to 10 years — and receive a fixed, guaranteed interest rate. Currently most Indian banks offer 6.5–7.5%, meaningfully better than a savings account.
                  </p>
                  <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 px-4 py-3">
                    <p className="text-amber-300 text-sm" style={{ fontFamily: "system-ui" }}>
                      ⚠️ FD interest is fully taxable. In the 30% bracket, a 7% FD returns only ~4.9% after tax — barely beating inflation. Good for short-term goals and capital protection, poor for long-term wealth building.
                    </p>
                  </div>
                </div>
              </div>

              {/* Mutual Funds */}
              <div className="rounded-xl border border-amber-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <h3 className="text-white font-bold">Mutual Funds</h3>
                  <RiskBadge level="Medium" />
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    A mutual fund pools money from thousands of investors, and a professional fund manager invests that collective pool into stocks, bonds, or a combination. You own units of the fund, and the value of those units rises or falls with the underlying assets.
                  </p>
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    Diversified equity mutual funds in India have historically delivered 10–14% annually over long periods of 7–10 years or more. The risk is medium because diversification cushions the blow — when a fund holds 50–100 different companies, one failing barely dents the overall portfolio.
                  </p>
                  <p className="text-slate-400 text-sm italic border-l-2 border-slate-700 pl-4" style={{ fontFamily: "system-ui" }}>
                    Watch the expense ratio — active funds charge 1–2% annually, which compounds into a significant drag over decades.
                  </p>
                </div>
              </div>

              {/* Index Funds */}
              <div className="rounded-xl border border-amber-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <h3 className="text-white font-bold">Index Funds</h3>
                  <RiskBadge level="Medium" />
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    An index fund simply mirrors a market index with no active manager. The Nifty 50 index tracks India's 50 largest publicly listed companies — an index fund buys all 50 in the same proportion. If the Nifty 50 rises 12%, your fund rises approximately 12%.
                  </p>
                  <div className="rounded-lg border border-blue-500/25 bg-blue-500/5 px-4 py-3 mb-3">
                    <p className="text-blue-300 text-sm font-semibold mb-1" style={{ fontFamily: "system-ui" }}>Why index funds win long-term:</p>
                    <p className="text-slate-300 text-sm" style={{ fontFamily: "system-ui" }}>Expense ratio of just 0.1–0.2% vs 1–2% for active funds. Decades of data show the majority of professional active managers fail to consistently beat their benchmark index. The index wins by being cheap, consistent, and emotionally disciplined.</p>
                  </div>
                  <p className="text-slate-400 text-sm italic border-l-2 border-slate-700 pl-4" style={{ fontFamily: "system-ui" }}>
                    Index funds are widely considered the best starting point for any new investor.
                  </p>
                </div>
              </div>

              {/* Individual Stocks */}
              <div className="rounded-xl border border-red-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <h3 className="text-white font-bold">Individual Stocks</h3>
                  <RiskBadge level="High" />
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    When you buy a stock, you're purchasing a small ownership stake in a real company. Some stocks have returned 20x, 50x, even 100x over a decade — wealth-building that no FD or savings account can match.
                  </p>
                  <p className="text-slate-300 leading-relaxed text-base">
                    The downside is equally real. A single company can face bad management, regulatory trouble, industry disruption, or fraud — and the stock can fall 50%, 80%, even 100%. Successful stock picking requires deep research, financial analysis, and the emotional discipline to hold through volatile periods. Most retail investors who try to beat the market end up underperforming a simple index fund.
                  </p>
                </div>
              </div>

              {/* Crypto */}
              <div className="rounded-xl border border-red-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <h3 className="text-white font-bold">Crypto</h3>
                  <RiskBadge level="High" />
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    Cryptocurrencies like Bitcoin and Ethereum are digital assets with no physical backing, no government guarantee, no earnings, and no intrinsic yield. Their value is driven entirely by supply, demand, speculation, and narrative. Bitcoin has gone from ₹10 lakh to ₹60 lakh and crashed back to ₹20 lakh within a single year — these aren't unusual swings; they're normal for crypto.
                  </p>
                  <div className="rounded-lg border border-red-500/25 bg-red-500/5 px-4 py-3">
                    <p className="text-red-300 text-sm" style={{ fontFamily: "system-ui" }}>
                      India's 30% flat tax on gains with no loss offset against other income makes crypto especially punishing. Treat it as a small speculative position at most — never a core wealth-building strategy.
                    </p>
                  </div>
                </div>
              </div>

              {/* Business */}
              <div className="rounded-xl border border-red-500/25 bg-slate-800/60 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/60 flex items-center justify-between">
                  <h3 className="text-white font-bold">Business</h3>
                  <RiskBadge level="High" />
                </div>
                <div className="px-6 py-4">
                  <p className="text-slate-300 leading-relaxed text-base mb-3">
                    Starting or directly investing in a private business carries the highest risk — a large majority of new businesses fail within their first five years. You're not just risking money; you're risking time, energy, relationships, and often personal savings.
                  </p>
                  <p className="text-slate-300 leading-relaxed text-base">
                    But the return ceiling is also the highest of any asset class. Every major fortune in history was built through business ownership. You're not just earning a return on capital — you're building an asset whose value multiplies as the business scales. For those with the right skills, temperament, and domain expertise, business is the most powerful wealth-creation vehicle that exists.
                  </p>
                </div>
              </div>

            </div>
          </section>

          {/* Section 4: Balancing Risk */}
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>4</span>
              Balancing Risk Wisely
            </h2>
            <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 px-6 py-5">
              <p className="text-slate-200 leading-relaxed text-base">
                The goal is never to eliminate risk — that guarantees you lose to inflation. The goal is to take the right amount of risk for your specific situation. A 22-year-old with stable income and a 30-year horizon can afford to be heavily in equities. A 58-year-old near retirement needs capital protection. <span className="text-white font-semibold">Time is the greatest risk-reducer</span> — the longer you stay invested, the more short-term volatility you can absorb, and the more likely your portfolio is to recover from any downturn.
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
          <span className="text-slate-500 text-sm">Chapter 2 of 8</span>
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