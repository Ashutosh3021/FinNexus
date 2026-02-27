import { useState } from "react";

const lessonSections = [
  {
    id: "active-income",
    title: "Active Income",
    content: `This is money you earn by directly exchanging your time and effort for payment. If you stop working, the money stops too. A salaried job is the most common example — you show up, you get paid. Freelancing works the same way: you complete a project, you get paid for that project. Other examples include hourly wages, commissions, and tips. The key limitation of active income is that it's capped by the number of hours you can work.`,
  },
  {
    id: "expenses",
    title: "Expenses: Needs vs Wants",
    content: null,
    structured: {
      intro: "Expenses are everything you spend money on, and the most important skill here is learning to tell the difference between the two categories.",
      blocks: [
        {
          label: "Needs",
          labelColor: "text-emerald-400",
          borderColor: "border-emerald-500/40",
          bg: "bg-emerald-500/5",
          text: "are non-negotiable — things you genuinely require to live and function. Rent, food, electricity, transportation to work, and basic healthcare fall here. You can't reasonably cut these out.",
        },
        {
          label: "Wants",
          labelColor: "text-amber-400",
          borderColor: "border-amber-500/40",
          bg: "bg-amber-500/5",
          text: "are things that improve your life but aren't essential for survival. Streaming subscriptions, eating out, new clothes beyond what you need, vacations, and the latest phone are all wants. This doesn't mean you can never spend on wants — it means you should spend on them consciously and deliberately, after your needs and savings are covered.",
        },
      ],
      footnote: "The trap most people fall into is treating wants as needs over time. A basic phone is a need; the newest flagship model is a want.",
    },
  },
  {
    id: "savings-rate",
    title: "Savings Rate",
    content: null,
    structured: {
      intro: "This is the percentage of your income that you keep rather than spend. It's arguably the single most powerful number in personal finance, because it determines two things simultaneously — how fast you accumulate money, and how cheaply you can live.",
      formula: "Savings Rate = (Income − Expenses) ÷ Income × 100",
      example: "So if you earn ₹50,000/month and spend ₹35,000, you save ₹15,000 — a 30% savings rate.",
      footnote: "A person saving 40% of their income will reach financial independence dramatically faster than someone saving 10%, even if they earn the same salary. The 20–40% target is a strong benchmark. Most people save less than 10%, which is why most people feel financially stuck regardless of how much their salary grows.",
    },
  },
  {
    id: "wealth-mindset",
    title: `Why "Wealth = What You Keep, Not What You Earn"`,
    content: `This is the core mindset shift. A person earning ₹2,00,000/month but spending ₹1,95,000 is financially weaker than someone earning ₹60,000 and saving ₹20,000. High income with low savings rate builds lifestyle, not wealth. The goal is to widen the gap between what comes in and what goes out — and then put that gap to work.`,
    highlight: true,
  },
];

const questions = [
  {
    id: 1,
    question: "What stops active income from growing infinitely?",
    answer: "Time limit",
    placeholder: "Your answer...",
  },
  {
    id: 2,
    question: "Rent and food are examples of?",
    answer: "Needs",
    placeholder: "Your answer...",
  },
  {
    id: 3,
    question: "Netflix and eating out are examples of?",
    answer: "Wants",
    placeholder: "Your answer...",
  },
  {
    id: 4,
    question: "What is the formula output called when you divide saved money by income?",
    answer: "Savings rate",
    placeholder: "Your answer...",
  },
  {
    id: 5,
    question: "Wealth equals what you _____, not what you earn?",
    answer: "Keep",
    placeholder: "Your answer...",
  },
];

function normalizeAnswer(str) {
  return str.trim().toLowerCase().replace(/[^a-z0-9\s]/g, "");
}

function QuestionCard({ q, index }) {
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const isCorrect =
    submitted && normalizeAnswer(input) === normalizeAnswer(q.answer);
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
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          ) : isWrong ? (
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
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
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              Not quite — try again!
            </p>
          )}

          {isCorrect && (
            <p className="text-emerald-400 text-sm mt-2 flex items-center gap-1.5">
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 flex-shrink-0">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              Correct!
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PersonalFinancePage() {
  const [activeSection, setActiveSection] = useState(null);
  const allQuestionIds = questions.map((q) => q.id);

  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div
      style={{ fontFamily: "'Georgia', 'Times New Roman', serif" }}
      className="min-h-screen bg-slate-900 text-slate-100"
    >
      {/* Top Nav Bar */}
      <div className="sticky top-0 z-10 bg-slate-900/90 backdrop-blur-sm border-b border-slate-800 px-6 py-3 flex items-center gap-3">
        <button className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors text-sm">
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path
              fillRule="evenodd"
              d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
              clipRule="evenodd"
            />
          </svg>
          Back to Lessons
        </button>
        <span className="text-slate-600">|</span>
        <span className="text-slate-400 text-sm truncate">Personal Finance · Fundamentals</span>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12">
        {/* Chapter Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <span className="px-3 py-1 bg-blue-500/15 text-blue-400 rounded-full text-xs font-medium tracking-wide uppercase" style={{ fontFamily: "system-ui, sans-serif" }}>
              Chapter 1
            </span>
            <span className="flex items-center gap-1.5 text-slate-400 text-xs" style={{ fontFamily: "system-ui, sans-serif" }}>
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                  clipRule="evenodd"
                />
              </svg>
              8 min read
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white leading-tight mb-4">
            Understanding the Fundamentals of Personal Finance
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            Before building wealth, you need to understand the language of money — how income works, where expenses go, and what the most powerful lever in your financial life actually is.
          </p>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-10">
          <div className="flex-1 h-px bg-slate-800"></div>
          <div className="w-1.5 h-1.5 rounded-full bg-slate-600"></div>
          <div className="flex-1 h-px bg-slate-800"></div>
        </div>

        {/* Lesson Sections */}
        <div className="space-y-10 mb-16">
          {/* Section 1: Active Income */}
          <section id="active-income">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>1</span>
              Active Income
            </h2>
            <p className="text-slate-300 leading-relaxed text-base">
              {lessonSections[0].content}
            </p>
          </section>

          {/* Section 2: Expenses */}
          <section id="expenses">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>2</span>
              Expenses: Needs vs Wants
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              {lessonSections[1].structured.intro}
            </p>
            <div className="space-y-3 mb-5">
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-5 py-4">
                <p className="text-slate-300 leading-relaxed text-base">
                  <span className="font-bold text-emerald-400">Needs</span>{" "}
                  {lessonSections[1].structured.blocks[0].text}
                </p>
              </div>
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-5 py-4">
                <p className="text-slate-300 leading-relaxed text-base">
                  <span className="font-bold text-amber-400">Wants</span>{" "}
                  {lessonSections[1].structured.blocks[1].text}
                </p>
              </div>
            </div>
            <p className="text-slate-400 text-sm italic leading-relaxed border-l-2 border-slate-700 pl-4">
              {lessonSections[1].structured.footnote}
            </p>
          </section>

          {/* Section 3: Savings Rate */}
          <section id="savings-rate">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>3</span>
              Savings Rate
            </h2>
            <p className="text-slate-300 leading-relaxed text-base mb-5">
              {lessonSections[2].structured.intro}
            </p>
            <div className="bg-slate-800 border border-slate-700 rounded-xl px-6 py-5 mb-5">
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-3" style={{ fontFamily: "system-ui" }}>Formula</p>
              <p className="text-blue-300 font-bold text-lg tracking-wide" style={{ fontFamily: "monospace" }}>
                {lessonSections[2].structured.formula}
              </p>
              <div className="mt-3 pt-3 border-t border-slate-700">
                <p className="text-slate-400 text-sm">{lessonSections[2].structured.example}</p>
              </div>
            </div>
            <p className="text-slate-300 leading-relaxed text-base">
              {lessonSections[2].structured.footnote}
            </p>
          </section>

          {/* Section 4: Wealth Mindset */}
          <section id="wealth-mindset">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold" style={{ fontFamily: "system-ui" }}>4</span>
              Wealth = What You Keep
            </h2>
            <div className="rounded-xl border border-blue-500/25 bg-blue-500/5 px-6 py-5">
              <p className="text-slate-200 leading-relaxed text-base">
                {lessonSections[3].content}
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
          <span className="text-slate-500 text-sm">Chapter 1 of 8</span>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors">
            Next Chapter
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}